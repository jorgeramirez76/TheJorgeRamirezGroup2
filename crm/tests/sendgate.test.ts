import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq } from 'drizzle-orm';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import * as schema from '../src/db/schema.js';
import { applyMigrations } from '../src/db/migrate.js';
import { seedCoreData } from '../src/db/seed.js';
import { evaluateSendGate } from '../src/sendgate/index.js';
import { sendOutboundMessage } from '../src/sendgate/send.js';
import { upsertSetting } from '../src/settings/store.js';
import type { Channel } from '../src/channels/types.js';

let sqlite: Database.Database;
let db: ReturnType<typeof drizzle<typeof schema>>;

beforeEach(() => {
  sqlite = new Database(':memory:');
  applyMigrations(sqlite);
  db = drizzle(sqlite, { schema });
  seedCoreData(db);
  // Seed fixtures include a real-timestamped iMessage outbound row (for the inbox demo data),
  // which would otherwise collide with the 45s pacing gate against these tests' synthetic `now`.
  db.delete(schema.messages).run();
});

afterEach(() => sqlite.close());

function contactByFirstName(name: string) {
  return db.select().from(schema.contacts).all().find((c) => c.firstName === name)!;
}

// 2026-07-03T16:00:00Z = noon America/New_York (EDT, UTC-4) — inside the default 08:30-20:30 window.
function midday() {
  return new Date('2026-07-03T16:00:00.000Z');
}

// 2026-07-03T03:00:00Z = 11pm America/New_York the prior night — outside the default window.
function lateNight() {
  return new Date('2026-07-03T03:00:00.000Z');
}

describe('evaluateSendGate', () => {
  it('blocks a suppressed contact', () => {
    const maria = contactByFirstName('Maria');
    db.insert(schema.suppressions).values({ kind: 'contact', value: String(maria.id), reason: 'test' }).run();
    expect(evaluateSendGate(db, { contactId: maria.id, channel: 'imessage', now: midday() })).toEqual({ allowed: false, reason: 'suppressed' });
  });

  it('blocks a contact without SMS consent', () => {
    const ana = contactByFirstName('Ana'); // seeded with consentSms: false
    expect(evaluateSendGate(db, { contactId: ana.id, channel: 'imessage', now: midday() })).toEqual({ allowed: false, reason: 'no_consent' });
  });

  it('blocks and reschedules outside quiet hours instead of dropping', () => {
    const maria = contactByFirstName('Maria');
    const result = evaluateSendGate(db, { contactId: maria.id, channel: 'imessage', now: lateNight() });
    expect(result.allowed).toBe(false);
    if (!result.allowed) {
      expect(result.reason).toBe('quiet_hours');
      expect(result.retryAt).toBeDefined();
      expect(new Date(result.retryAt!).getTime()).toBeGreaterThan(lateNight().getTime());
    }
  });

  it('enforces the per-lead daily cap, but exempts replies', () => {
    // Uses the email channel so the (imessage-only) 45s pacing gate can't interfere with
    // isolating the per-lead cap check itself.
    const maria = contactByFirstName('Maria');
    const now = midday();
    for (let i = 0; i < 2; i++) {
      db.insert(schema.messages).values({ contactId: maria.id, channel: 'email', direction: 'out', body: `t${i}`, status: 'sent', createdAt: now.toISOString() }).run();
    }
    expect(evaluateSendGate(db, { contactId: maria.id, channel: 'email', now })).toEqual(expect.objectContaining({ allowed: false, reason: 'per_lead_cap' }));
    expect(evaluateSendGate(db, { contactId: maria.id, channel: 'email', now, isReply: true }).allowed).toBe(true);
  });

  it('enforces the global daily cap across all contacts', () => {
    upsertSetting(db, 'global_daily_cap', 1);
    const now = midday();
    const maria = contactByFirstName('Maria');
    const david = contactByFirstName('David');
    db.insert(schema.messages).values({ contactId: maria.id, channel: 'imessage', direction: 'out', body: 'first', status: 'sent', createdAt: now.toISOString() }).run();
    expect(evaluateSendGate(db, { contactId: david.id, channel: 'imessage', now })).toEqual(expect.objectContaining({ allowed: false, reason: 'global_cap' }));
  });

  it('enforces 45s pacing between iMessage sends regardless of which contact is next', () => {
    const maria = contactByFirstName('Maria');
    const david = contactByFirstName('David');
    const now = midday();
    db.insert(schema.messages).values({ contactId: maria.id, channel: 'imessage', direction: 'out', body: 'first', status: 'sent', createdAt: now.toISOString(), sentAt: now.toISOString() }).run();
    const tooSoon = new Date(now.getTime() + 10_000);
    const result = evaluateSendGate(db, { contactId: david.id, channel: 'imessage', now: tooSoon });
    expect(result).toEqual(expect.objectContaining({ allowed: false, reason: 'imessage_pacing' }));
  });

  it('blocks iMessage sends while the BlueBubbles health check is down', () => {
    const maria = contactByFirstName('Maria');
    upsertSetting(db, 'imessage_health', { ok: false, lastCheckedAt: midday().toISOString(), lastError: 'ping failed', downSince: midday().toISOString() });
    expect(evaluateSendGate(db, { contactId: maria.id, channel: 'imessage', now: midday() })).toEqual(expect.objectContaining({ allowed: false, reason: 'channel_unhealthy' }));
  });
});

describe('sendOutboundMessage', () => {
  it('reschedules via scheduled_actions instead of sending or silently dropping when outside quiet hours', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    let sendCalled = false;
    const fakeChannel: Channel = { send: async () => { sendCalled = true; return { externalId: 'x', chatGuid: 'x' }; } };

    const result = await sendOutboundMessage(db, fakeChannel, {
      leadId: lead.id, contactId: maria.id, channel: 'imessage', body: 'hello', now: lateNight()
    });

    expect(sendCalled).toBe(false);
    expect(result.sent).toBe(false);
    if (!result.sent) {
      expect(result.reason).toBe('quiet_hours');
      const scheduled = db.select().from(schema.scheduledActions).where(eq(schema.scheduledActions.id, result.scheduledActionId)).get()!;
      expect(scheduled.status).toBe('queued');
      expect(scheduled.runAt).toBe(result.retryAt);
      expect(scheduled.kind).toBe('send_message');
    }

    const sentRows = db.select().from(schema.messages).where(eq(schema.messages.contactId, maria.id)).all().filter((m) => m.body === 'hello');
    expect(sentRows).toHaveLength(0);
  });

  it('sends immediately and records the message when the gate allows it', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const fakeChannel: Channel = { send: async () => ({ externalId: 'ext-1', chatGuid: 'chat-1' }) };

    const result = await sendOutboundMessage(db, fakeChannel, {
      leadId: lead.id, contactId: maria.id, channel: 'imessage', body: 'hello', now: midday()
    });

    expect(result.sent).toBe(true);
    if (result.sent) {
      const row = db.select().from(schema.messages).where(eq(schema.messages.id, result.messageId)).get()!;
      expect(row.status).toBe('sent');
      expect(row.externalId).toBe('ext-1');
    }
  });
});
