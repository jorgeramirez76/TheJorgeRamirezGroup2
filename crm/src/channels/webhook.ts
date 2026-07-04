import { and, eq } from 'drizzle-orm';
import * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';
import { handleOptOut, matchesOptOut } from '../sendgate/optout.js';
import { normalizePhone } from './phone.js';

export type BlueBubblesWebhookPayload = {
  type: string;
  data: {
    guid: string;
    text?: string | null;
    isFromMe?: boolean;
    handle?: { address?: string | null } | null;
    chatGuid?: string;
    chats?: Array<{ guid: string }>;
    dateCreated?: number;
    dateDelivered?: number | null;
    dateRead?: number | null;
  };
};

export type WebhookOutcome =
  | { status: 'ignored_from_me' }
  | { status: 'ignored_duplicate' }
  | { status: 'ignored_unhandled_type' }
  | { status: 'status_updated'; messageId: number; newStatus: string }
  | { status: 'status_update_unknown_message' }
  | { status: 'received'; messageId: number; contactId: number; shellContactCreated: boolean; optOut: boolean };

function resolveChatGuid(data: BlueBubblesWebhookPayload['data']): string | undefined {
  return data.chatGuid ?? data.chats?.[0]?.guid;
}

function findContactByAddress(db: CrmDb, address: string) {
  const normalized = normalizePhone(address);
  const contacts = db.select().from(schema.contacts).all();
  return contacts.find((contact) => contact.imessageHandle === address || contact.phones.some((phone) => normalizePhone(phone) === normalized));
}

function ensureNeedsReviewTag(db: CrmDb) {
  db.insert(schema.tags).values({ name: 'needs-review' }).onConflictDoNothing().run();
  const tag = db.select().from(schema.tags).where(eq(schema.tags.name, 'needs-review')).get();
  if (!tag) throw new Error('Could not resolve needs-review tag');
  return tag;
}

// Unknown senders get a shell contact so the message has somewhere to live, but with
// consentSms=false — the send gate blocks all outbound until Jorge reviews and confirms it.
function createShellContact(db: CrmDb, address: string) {
  const contact = db.insert(schema.contacts).values({
    phones: [address], imessageHandle: address, source: 'imessage_inbound',
    consentSms: false, consentEmail: false
  }).returning().get();
  const tag = ensureNeedsReviewTag(db);
  db.insert(schema.contactTags).values({ contactId: contact.id, tagId: tag.id }).onConflictDoNothing().run();
  return contact;
}

function handleNewMessage(db: CrmDb, data: BlueBubblesWebhookPayload['data']): WebhookOutcome {
  if (data.isFromMe) return { status: 'ignored_from_me' };

  const existing = db.select().from(schema.messages)
    .where(and(eq(schema.messages.channel, 'imessage'), eq(schema.messages.externalId, data.guid))).get();
  if (existing) return { status: 'ignored_duplicate' };

  const address = data.handle?.address;
  if (!address) throw new Error('BlueBubbles new-message webhook missing handle.address');

  let contact = findContactByAddress(db, address);
  let shellContactCreated = false;
  if (!contact) {
    contact = createShellContact(db, address);
    shellContactCreated = true;
  }

  const chatGuid = resolveChatGuid(data);
  const body = data.text ?? '';
  const message = db.insert(schema.messages).values({
    contactId: contact.id, channel: 'imessage', direction: 'in', body,
    externalId: data.guid, threadKey: chatGuid ?? null, status: 'received'
  }).returning().get();

  db.insert(schema.events).values({
    contactId: contact.id, kind: 'inbound_message', payload: { messageId: message.id, channel: 'imessage' }
  }).run();

  // Hard rule, before any AI/workflow processing (§7.1 / §12): STOP-family regex short-circuits everything else.
  let optOut = false;
  if (matchesOptOut(db, body)) {
    handleOptOut(db, { contactId: contact.id, channel: 'imessage' });
    optOut = true;
  }

  return { status: 'received', messageId: message.id, contactId: contact.id, shellContactCreated, optOut };
}

function handleUpdatedMessage(db: CrmDb, data: BlueBubblesWebhookPayload['data']): WebhookOutcome {
  const message = db.select().from(schema.messages)
    .where(and(eq(schema.messages.channel, 'imessage'), eq(schema.messages.externalId, data.guid))).get();
  if (!message) return { status: 'status_update_unknown_message' };

  const newStatus = data.dateRead ? 'read' : data.dateDelivered ? 'delivered' : message.status;
  db.update(schema.messages).set({ status: newStatus }).where(eq(schema.messages.id, message.id)).run();
  return { status: 'status_updated', messageId: message.id, newStatus };
}

export function handleBlueBubblesWebhook(db: CrmDb, payload: BlueBubblesWebhookPayload): WebhookOutcome {
  if (payload.type === 'new-message') return handleNewMessage(db, payload.data);
  if (payload.type === 'updated-message') return handleUpdatedMessage(db, payload.data);
  return { status: 'ignored_unhandled_type' };
}
