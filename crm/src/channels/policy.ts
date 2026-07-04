import type * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';
import type { Channel, EmailChannel } from './types.js';
import { sendOutboundEmail, sendOutboundMessage } from '../sendgate/send.js';

export type ContactRow = typeof schema.contacts.$inferSelect;
export type ChannelChoice = 'imessage' | 'email';

/**
 * §6.3 (LOCKED): preferred_channel wins if set and usable; otherwise iMessage first when the
 * contact has a phone + SMS consent, else email as secondary/long-form. Null means no channel
 * this contact has consented to and given us contact info for is currently eligible.
 */
export function selectPrimaryChannel(contact: ContactRow): ChannelChoice | null {
  const canImessage = contact.consentSms && contact.phones.length > 0;
  const canEmail = contact.consentEmail && contact.emails.length > 0;

  if (contact.preferredChannel === 'imessage' && canImessage) return 'imessage';
  if (contact.preferredChannel === 'email' && canEmail) return 'email';
  if (canImessage) return 'imessage';
  if (canEmail) return 'email';
  return null;
}

export type ChannelFallbackParams = {
  leadId: number;
  contactId: number;
  body: string;
  subject: string;
  isReply?: boolean;
  generatedBy?: 'ai' | 'human' | 'workflow_template';
  now?: Date;
};

export type ChannelFallbackResult =
  | { sent: true; channel: ChannelChoice; messageId: number; externalId: string }
  | { sent: false; channel: ChannelChoice | null; reason: string; retryAt?: string; scheduledActionId?: number };

function canEmailFallback(contact: ContactRow): boolean {
  return contact.consentEmail && contact.emails.length > 0;
}

async function sendEmailFallback(db: CrmDb, email: EmailChannel, contact: ContactRow, params: ChannelFallbackParams): Promise<ChannelFallbackResult> {
  // A fallback email is never threaded onto a prior email conversation — there may not be one.
  const result = await sendOutboundEmail(db, email, null, {
    leadId: params.leadId, contactId: params.contactId, to: contact.emails[0], subject: params.subject, body: params.body,
    isReply: false, generatedBy: params.generatedBy, now: params.now
  });
  return result.sent
    ? { sent: true, channel: 'email', messageId: result.messageId, externalId: result.externalId }
    : { sent: false, channel: 'email', reason: result.reason, retryAt: result.retryAt, scheduledActionId: result.scheduledActionId };
}

/**
 * §6.3/§6.1 (LOCKED): send on the policy-selected primary channel; if iMessage is the primary
 * channel but is unhealthy or the send itself fails, fall back to email when the contact has
 * consented to it. Never falls back on gate denials that also govern email (suppression,
 * consent, quiet hours, caps) — those are real policy blocks, not channel outages.
 */
export async function sendWithChannelFallback(
  db: CrmDb,
  contact: ContactRow,
  channels: { imessage?: Channel; email?: EmailChannel },
  params: ChannelFallbackParams
): Promise<ChannelFallbackResult> {
  const primary = selectPrimaryChannel(contact);
  if (!primary) return { sent: false, channel: null, reason: 'no_eligible_channel' };

  if (primary === 'email') {
    if (!channels.email) return { sent: false, channel: 'email', reason: 'email_channel_unavailable' };
    return sendEmailFallback(db, channels.email, contact, params);
  }

  if (!channels.imessage) {
    return channels.email && canEmailFallback(contact)
      ? sendEmailFallback(db, channels.email, contact, params)
      : { sent: false, channel: 'imessage', reason: 'imessage_channel_unavailable' };
  }

  try {
    const result = await sendOutboundMessage(db, channels.imessage, {
      leadId: params.leadId, contactId: params.contactId, channel: 'imessage', body: params.body,
      address: contact.imessageHandle ?? contact.phones[0], isReply: params.isReply,
      generatedBy: params.generatedBy, now: params.now
    });

    if (result.sent) return { sent: true, channel: 'imessage', messageId: result.messageId, externalId: result.externalId };
    if (result.reason === 'channel_unhealthy' && channels.email && canEmailFallback(contact)) {
      return sendEmailFallback(db, channels.email, contact, params);
    }
    return { sent: false, channel: 'imessage', reason: result.reason, retryAt: result.retryAt, scheduledActionId: result.scheduledActionId };
  } catch (err) {
    if (channels.email && canEmailFallback(contact)) return sendEmailFallback(db, channels.email, contact, params);
    throw err;
  }
}
