import { and, eq } from 'drizzle-orm';
import * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';
import { getSettings, upsertSetting } from '../settings/store.js';
import { handleOptOut, matchesOptOut } from '../sendgate/optout.js';
import { extractPlainTextBody, getHeader, type GmailApiClient } from './gmail-client.js';

export type GmailPollResult = { processed: number; ignored: number; cursorBefore: string | null; cursorAfter: string };

function parseEmailAddress(fromHeader: string): string {
  const angle = /<([^>]+)>/.exec(fromHeader);
  return (angle ? angle[1] : fromHeader).trim().toLowerCase();
}

function findContactByEmail(db: CrmDb, address: string) {
  const contacts = db.select().from(schema.contacts).all();
  return contacts.find((contact) => contact.emails.some((email) => email.toLowerCase() === address));
}

/**
 * Only known contacts, or replies within a thread the CRM already started, are processed.
 * Everything else is Jorge's personal inbox and is left alone (§6.2).
 */
async function processInboundMessage(db: CrmDb, client: GmailApiClient, messageId: string): Promise<'processed' | 'ignored'> {
  const existing = db.select().from(schema.messages)
    .where(and(eq(schema.messages.channel, 'email'), eq(schema.messages.externalId, messageId))).get();
  if (existing) return 'ignored';

  const message = await client.getMessage(messageId);
  if (message.labelIds?.includes('SENT')) return 'ignored';

  const fromHeader = getHeader(message, 'From');
  if (!fromHeader) return 'ignored';
  const fromAddress = parseEmailAddress(fromHeader);

  let contact = findContactByEmail(db, fromAddress);
  if (!contact) {
    const threadMessage = db.select().from(schema.messages)
      .where(and(eq(schema.messages.channel, 'email'), eq(schema.messages.threadKey, message.threadId))).get();
    if (!threadMessage) return 'ignored';
    contact = db.select().from(schema.contacts).where(eq(schema.contacts.id, threadMessage.contactId)).get();
    if (!contact) return 'ignored';
  }

  const body = extractPlainTextBody(message);
  const row = db.insert(schema.messages).values({
    contactId: contact.id, channel: 'email', direction: 'in', body,
    subject: getHeader(message, 'Subject'), externalId: message.id, threadKey: message.threadId, status: 'received'
  }).returning().get();

  db.insert(schema.events).values({
    contactId: contact.id, kind: 'inbound_message', payload: { messageId: row.id, channel: 'email' }
  }).run();

  // Hard rule, before any AI/workflow processing (§7.1 / §12), same as the iMessage webhook.
  if (matchesOptOut(db, body)) {
    handleOptOut(db, { contactId: contact.id, channel: 'email' });
  }

  return 'processed';
}

/**
 * Polls `users.history.list` from the persisted cursor (`settings.gmail_history_id`).
 * First-ever run has no cursor: it seeds one from the current profile and processes nothing,
 * so a fresh install doesn't replay Jorge's entire mailbox history as "inbound" on day one.
 */
export async function pollGmailInbox(db: CrmDb, client: GmailApiClient): Promise<GmailPollResult> {
  const settings = getSettings(db);
  const cursor = settings.gmail_history_id as string | null;

  if (!cursor) {
    const profile = await client.getProfile();
    upsertSetting(db, 'gmail_history_id', profile.historyId);
    return { processed: 0, ignored: 0, cursorBefore: null, cursorAfter: profile.historyId };
  }

  let historyResult;
  try {
    historyResult = await client.listHistory({ startHistoryId: cursor });
  } catch {
    // startHistoryId too old for Gmail to diff (e.g. long downtime) — reset the baseline rather
    // than crash the poller forever. A handful of inbound messages in the gap may be missed;
    // same trade-off BlueBubbles' own cursor makes after a server restart (see DECISIONS.md).
    const profile = await client.getProfile();
    upsertSetting(db, 'gmail_history_id', profile.historyId);
    return { processed: 0, ignored: 0, cursorBefore: cursor, cursorAfter: profile.historyId };
  }

  const messageIds = new Set<string>();
  for (const record of historyResult.history) {
    for (const added of record.messagesAdded ?? []) messageIds.add(added.message.id);
  }

  let processed = 0;
  let ignored = 0;
  for (const messageId of messageIds) {
    const outcome = await processInboundMessage(db, client, messageId);
    if (outcome === 'processed') processed++;
    else ignored++;
  }

  upsertSetting(db, 'gmail_history_id', historyResult.historyId);
  return { processed, ignored, cursorBefore: cursor, cursorAfter: historyResult.historyId };
}

export function startGmailPolling(db: CrmDb, client: GmailApiClient, opts: { intervalMs?: number } = {}) {
  const intervalMs = opts.intervalMs ?? 30_000;
  const timer = setInterval(() => {
    pollGmailInbox(db, client).catch((err) => {
      db.insert(schema.events).values({
        kind: 'error', payload: { source: 'gmail_poller', message: err instanceof Error ? err.message : String(err) }
      }).run();
    });
  }, intervalMs);
  timer.unref?.();
  return () => clearInterval(timer);
}
