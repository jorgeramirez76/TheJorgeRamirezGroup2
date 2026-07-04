import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq } from 'drizzle-orm';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import * as schema from '../src/db/schema.js';
import { applyMigrations } from '../src/db/migrate.js';
import { seedCoreData } from '../src/db/seed.js';
import { handleOptOut, matchesOptOut } from '../src/sendgate/optout.js';

let sqlite: Database.Database;
let db: ReturnType<typeof drizzle<typeof schema>>;

beforeEach(() => {
  sqlite = new Database(':memory:');
  applyMigrations(sqlite);
  db = drizzle(sqlite, { schema });
  seedCoreData(db);
});

afterEach(() => sqlite.close());

describe('matchesOptOut', () => {
  it('matches common opt-out phrasing case-insensitively', () => {
    expect(matchesOptOut(db, 'STOP')).toBe(true);
    expect(matchesOptOut(db, 'please Unsubscribe me')).toBe(true);
    expect(matchesOptOut(db, "don't text me anymore")).toBe(true);
    expect(matchesOptOut(db, 'sounds great, thanks!')).toBe(false);
  });
});

describe('handleOptOut', () => {
  it('suppresses the contact, halts active workflow enrollments, and confirms exactly once across repeated STOPs', () => {
    const maria = db.select().from(schema.contacts).all().find((c) => c.firstName === 'Maria')!;
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const workflow = db.insert(schema.workflows).values({ name: 'Test Nurture', trigger: { kind: 'lead_created' } }).returning().get();
    const enrollment = db.insert(schema.enrollments).values({ workflowId: workflow.id, leadId: lead.id, state: 'active' }).returning().get();
    const scheduledAction = db.insert(schema.scheduledActions).values({ leadId: lead.id, kind: 'send_message', runAt: new Date().toISOString(), status: 'queued' }).returning().get();

    const first = handleOptOut(db, { contactId: maria.id, channel: 'imessage' });
    expect(first).toEqual({ alreadySuppressed: false, confirmationQueued: true });

    const second = handleOptOut(db, { contactId: maria.id, channel: 'imessage' });
    expect(second).toEqual({ alreadySuppressed: true, confirmationQueued: false });

    const updatedContact = db.select().from(schema.contacts).where(eq(schema.contacts.id, maria.id)).get()!;
    expect(updatedContact.doNotContact).toBe(true);

    const updatedEnrollment = db.select().from(schema.enrollments).where(eq(schema.enrollments.id, enrollment.id)).get()!;
    expect(updatedEnrollment.state).toBe('exited');

    const updatedAction = db.select().from(schema.scheduledActions).where(eq(schema.scheduledActions.id, scheduledAction.id)).get()!;
    expect(updatedAction.status).toBe('cancelled');

    const phoneSuppression = db.select().from(schema.suppressions).where(eq(schema.suppressions.value, '+15555550101')).get();
    expect(phoneSuppression).toBeTruthy();

    const confirmations = db.select().from(schema.messages).where(eq(schema.messages.contactId, maria.id)).all()
      .filter((message) => message.generatedBy === 'workflow_template');
    expect(confirmations).toHaveLength(1);
  });
});
