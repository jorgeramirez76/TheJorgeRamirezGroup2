import { and, eq } from 'drizzle-orm';
import * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';

// 1x1 transparent GIF.
export const TRANSPARENT_GIF = Buffer.from('R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==', 'base64');

export type EmailOpenOutcome = { recorded: boolean; messageId?: number };

/** `email_open` is a soft signal only (§6.2) — an unknown/missing id is a silent no-op, not an error. */
export function recordEmailOpen(db: CrmDb, gmailMessageId: string | undefined | null): EmailOpenOutcome {
  if (!gmailMessageId) return { recorded: false };

  const message = db.select().from(schema.messages)
    .where(and(eq(schema.messages.channel, 'email'), eq(schema.messages.externalId, gmailMessageId))).get();
  if (!message) return { recorded: false };

  db.insert(schema.events).values({
    contactId: message.contactId, kind: 'email_open', payload: { messageId: message.id, externalId: gmailMessageId }
  }).run();

  return { recorded: true, messageId: message.id };
}
