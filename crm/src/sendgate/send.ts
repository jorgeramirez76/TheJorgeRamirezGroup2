import * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';
import type { Channel } from '../channels/types.js';
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
