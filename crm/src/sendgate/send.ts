import { and, desc, eq } from 'drizzle-orm';
import * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';
import type { Channel, EmailChannel } from '../channels/types.js';
import type { GmailApiClient } from '../channels/gmail-client.js';
import { getHeader } from '../channels/gmail-client.js';
import { appendCanSpamFooter, buildListUnsubscribeHeader } from '../channels/can-spam.js';
import { getSettings, upsertSetting } from '../settings/store.js';
import { evaluateSendGate } from './index.js';

export type SendOutboundParams = {
  leadId: number;
  contactId: number;
  channel: 'imessage';
  body: string;
  chatGuid?: string | null;
  address?: string | null;
  isReply?: boolean;
  generatedBy?: 'ai' | 'human' | 'workflow_template';
  now?: Date;
};

export type SendOutboundResult =
  | { sent: true; messageId: number; externalId: string }
  | { sent: false; reason: string; retryAt: string; scheduledActionId: number };

/**
 * The single path outbound iMessage sends must go through. A blocked send is never dropped —
 * it lands in scheduled_actions (the queue) with the send gate's computed retryAt.
 */
export async function sendOutboundMessage(db: CrmDb, channel: Channel, params: SendOutboundParams): Promise<SendOutboundResult> {
  const now = params.now ?? new Date();
  const gate = evaluateSendGate(db, { contactId: params.contactId, channel: params.channel, isReply: params.isReply, now });

  if (!gate.allowed) {
    const retryAt = gate.retryAt ?? new Date(now.getTime() + 5 * 60_000).toISOString();
    const scheduled = db.insert(schema.scheduledActions).values({
      leadId: params.leadId,
      kind: 'send_message',
      payload: {
        contactId: params.contactId, channel: params.channel, body: params.body,
        chatGuid: params.chatGuid ?? null, address: params.address ?? null, reason: gate.reason
      },
      runAt: retryAt,
      status: 'queued'
    }).returning().get();
    return { sent: false, reason: gate.reason, retryAt, scheduledActionId: scheduled.id };
  }

  const result = await channel.send({
    contactId: params.contactId, channel: params.channel, body: params.body,
    chatGuid: params.chatGuid, address: params.address
  });

  const message = db.insert(schema.messages).values({
    contactId: params.contactId, channel: params.channel, direction: 'out', body: params.body,
    externalId: result.externalId, threadKey: result.chatGuid,
    status: 'sent', generatedBy: params.generatedBy ?? 'human', sentAt: now.toISOString()
  }).returning().get();

  return { sent: true, messageId: message.id, externalId: result.externalId };
}

export type SendOutboundEmailParams = {
  leadId: number;
  contactId: number;
  to: string;
  subject: string;
  body: string;
  isReply?: boolean;
  generatedBy?: 'ai' | 'human' | 'workflow_template';
  now?: Date;
};

export type SendOutboundEmailResult =
  | { sent: true; messageId: number; externalId: string; threadId: string }
  | { sent: false; reason: string; retryAt: string; scheduledActionId: number };

function queueBlockedEmail(db: CrmDb, params: { leadId: number; contactId: number; to: string; subject: string; body: string; reason: string; retryAt: string }) {
  const scheduled = db.insert(schema.scheduledActions).values({
    leadId: params.leadId,
    kind: 'send_message',
    payload: { contactId: params.contactId, channel: 'email', to: params.to, subject: params.subject, body: params.body, reason: params.reason },
    runAt: params.retryAt,
    status: 'queued'
  }).returning().get();
  return scheduled.id;
}

/** Fetches the RFC 2822 Message-ID header of the most recent inbound email for threading a reply. */
async function resolveReplyHeaders(db: CrmDb, client: GmailApiClient, contactId: number): Promise<{ threadId: string | null; inReplyTo: string | null; references: string[] | null }> {
  const lastInbound = db.select().from(schema.messages)
    .where(and(eq(schema.messages.contactId, contactId), eq(schema.messages.channel, 'email'), eq(schema.messages.direction, 'in')))
    .orderBy(desc(schema.messages.id)).get();
  if (!lastInbound || !lastInbound.externalId) return { threadId: lastInbound?.threadKey ?? null, inReplyTo: null, references: null };

  const message = await client.getMessage(lastInbound.externalId);
  const messageIdHeader = getHeader(message, 'Message-ID');
  return { threadId: lastInbound.threadKey, inReplyTo: messageIdHeader, references: messageIdHeader ? [messageIdHeader] : null };
}

/**
 * The single path outbound 1:1 email must go through. Always threads onto the contact's
 * existing Gmail thread when replying; blocked sends land in scheduled_actions like iMessage.
 */
export async function sendOutboundEmail(db: CrmDb, channel: EmailChannel, client: GmailApiClient | null, params: SendOutboundEmailParams): Promise<SendOutboundEmailResult> {
  const now = params.now ?? new Date();
  const gate = evaluateSendGate(db, { contactId: params.contactId, channel: 'email', isReply: params.isReply, now });

  if (!gate.allowed) {
    const retryAt = gate.retryAt ?? new Date(now.getTime() + 5 * 60_000).toISOString();
    const scheduledActionId = queueBlockedEmail(db, { leadId: params.leadId, contactId: params.contactId, to: params.to, subject: params.subject, body: params.body, reason: gate.reason, retryAt });
    return { sent: false, reason: gate.reason, retryAt, scheduledActionId };
  }

  if (params.isReply && !client) throw new Error('sendOutboundEmail: a GmailApiClient is required to thread a reply');
  const threading = params.isReply && client
    ? await resolveReplyHeaders(db, client, params.contactId)
    : { threadId: null, inReplyTo: null, references: null };

  const result = await channel.send({
    contactId: params.contactId, to: params.to, subject: params.subject, body: params.body,
    threadId: threading.threadId, inReplyTo: threading.inReplyTo, references: threading.references
  });

  const message = db.insert(schema.messages).values({
    contactId: params.contactId, channel: 'email', direction: 'out', body: params.body, subject: params.subject,
    externalId: result.externalId, threadKey: result.threadId,
    status: 'sent', generatedBy: params.generatedBy ?? 'human', sentAt: now.toISOString()
  }).returning().get();

  return { sent: true, messageId: message.id, externalId: result.externalId, threadId: result.threadId };
}

export type SendCampaignEmailParams = {
  leadId: number;
  contactId: number;
  to: string;
  subject: string;
  body: string;
  /** Jorge's sending address (GMAIL_FROM) — the unsubscribe mailto goes to *him*, not the recipient. */
  fromEmail: string;
  generatedBy?: 'ai' | 'human' | 'workflow_template';
  now?: Date;
};

function recordCampaignSend(db: CrmDb, now: Date) {
  const settings = getSettings(db);
  const state = settings.email_campaign_state as { lastSentAt: string | null; countByDate: Record<string, number> };
  const todayKey = now.toISOString().slice(0, 10);
  upsertSetting(db, 'email_campaign_state', {
    lastSentAt: now.toISOString(),
    countByDate: { ...state.countByDate, [todayKey]: (state.countByDate[todayKey] ?? 0) + 1 }
  });
}

/**
 * The single path bulk/nurture (non-1:1) email must go through (§6.2/§12): 20s+ spacing and a
 * daily cap on top of the normal send gate, plus a mandatory CAN-SPAM footer + List-Unsubscribe.
 */
export async function sendCampaignEmail(db: CrmDb, channel: EmailChannel, params: SendCampaignEmailParams): Promise<SendOutboundEmailResult> {
  const now = params.now ?? new Date();
  const gate = evaluateSendGate(db, { contactId: params.contactId, channel: 'email', isReply: false, isCampaign: true, now });

  if (!gate.allowed) {
    const retryAt = gate.retryAt ?? new Date(now.getTime() + 5 * 60_000).toISOString();
    const scheduledActionId = queueBlockedEmail(db, { leadId: params.leadId, contactId: params.contactId, to: params.to, subject: params.subject, body: params.body, reason: gate.reason, retryAt });
    return { sent: false, reason: gate.reason, retryAt, scheduledActionId };
  }

  const settings = getSettings(db);
  const identity = {
    businessName: settings.business_name as string,
    businessMailingAddress: settings.business_mailing_address as string,
    fromEmail: params.fromEmail
  };
  const bodyWithFooter = appendCanSpamFooter(params.body, identity);

  const result = await channel.send({
    contactId: params.contactId, to: params.to, subject: params.subject, body: bodyWithFooter,
    listUnsubscribe: buildListUnsubscribeHeader(identity.fromEmail)
  });

  const message = db.insert(schema.messages).values({
    contactId: params.contactId, channel: 'email', direction: 'out', body: bodyWithFooter, subject: params.subject,
    externalId: result.externalId, threadKey: result.threadId,
    status: 'sent', generatedBy: params.generatedBy ?? 'workflow_template', sentAt: now.toISOString()
  }).returning().get();

  recordCampaignSend(db, now);

  return { sent: true, messageId: message.id, externalId: result.externalId, threadId: result.threadId };
}
