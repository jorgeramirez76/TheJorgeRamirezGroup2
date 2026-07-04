import { and, eq, inArray } from 'drizzle-orm';
import * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';
import { getSettings } from '../settings/store.js';

const OPT_OUT_CONFIRMATION = "You're unsubscribed and won't receive further texts from this number. Reply HELP for help.";

export function compileStopRegex(pattern: string): RegExp {
  const inlineFlags = /^\(\?([a-z]+)\)([\s\S]*)$/.exec(pattern);
  if (inlineFlags) {
    const flags = inlineFlags[1].includes('i') ? 'i' : '';
    return new RegExp(inlineFlags[2], flags);
  }
  return new RegExp(pattern, 'i');
}

export function matchesOptOut(db: CrmDb, body: string): boolean {
  const settings = getSettings(db);
  const regex = compileStopRegex(settings.stop_regex as string);
  return regex.test(body);
}

export type OptOutResult = {
  alreadySuppressed: boolean;
  confirmationQueued: boolean;
};

/**
 * Runs before any AI/workflow handling. Idempotent: repeated STOP messages from an
 * already-suppressed contact do not queue a second confirmation.
 */
export function handleOptOut(db: CrmDb, params: { contactId: number; channel: 'imessage' | 'email' }): OptOutResult {
  const contact = db.select().from(schema.contacts).where(eq(schema.contacts.id, params.contactId)).get();
  if (!contact) throw new Error(`Contact ${params.contactId} not found`);

  const alreadySuppressed = contact.doNotContact === true
    || Boolean(db.select().from(schema.suppressions).where(and(eq(schema.suppressions.kind, 'contact'), eq(schema.suppressions.value, String(contact.id)))).get());

  db.insert(schema.suppressions).values({ kind: 'contact', value: String(contact.id), reason: 'stop_keyword' }).onConflictDoNothing().run();
  for (const phone of contact.phones) {
    db.insert(schema.suppressions).values({ kind: 'phone', value: phone, reason: 'stop_keyword' }).onConflictDoNothing().run();
  }
  for (const email of contact.emails) {
    db.insert(schema.suppressions).values({ kind: 'email', value: email, reason: 'stop_keyword' }).onConflictDoNothing().run();
  }
  db.update(schema.contacts).set({ doNotContact: true, updatedAt: new Date().toISOString() }).where(eq(schema.contacts.id, contact.id)).run();

  const leadIds = db.select().from(schema.leads).where(eq(schema.leads.contactId, contact.id)).all().map((lead) => lead.id);
  if (leadIds.length > 0) {
    db.update(schema.enrollments).set({ state: 'exited' })
      .where(and(inArray(schema.enrollments.leadId, leadIds), inArray(schema.enrollments.state, ['active', 'paused']))).run();
    db.update(schema.scheduledActions).set({ status: 'cancelled' })
      .where(and(inArray(schema.scheduledActions.leadId, leadIds), eq(schema.scheduledActions.status, 'queued'))).run();
  }

  let confirmationQueued = false;
  if (!alreadySuppressed) {
    db.insert(schema.messages).values({
      contactId: contact.id, channel: params.channel, direction: 'out', body: OPT_OUT_CONFIRMATION,
      status: 'queued', generatedBy: 'workflow_template'
    }).run();
    confirmationQueued = true;
  }

  db.insert(schema.auditLog).values({
    actor: 'system', action: 'opt_out', entity: 'contact', entityId: String(contact.id),
    detail: { channel: params.channel, alreadySuppressed, confirmationQueued }
  }).run();

  return { alreadySuppressed, confirmationQueued };
}
