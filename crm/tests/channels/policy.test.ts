import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq } from 'drizzle-orm';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import * as schema from '../../src/db/schema.js';
import { applyMigrations } from '../../src/db/migrate.js';
import { seedCoreData } from '../../src/db/seed.js';
import { selectPrimaryChannel, sendWithChannelFallback } from '../../src/channels/policy.js';
import { upsertSetting } from '../../src/settings/store.js';
import type { Channel, EmailChannel } from '../../src/channels/types.js';

let sqlite: Database.Database;
let db: ReturnType<typeof drizzle<typeof schema>>;

beforeEach(() => {
  sqlite = new Database(':memory:');
  applyMigrations(sqlite);
  db = drizzle(sqlite, { schema });
  seedCoreData(db);
  db.delete(schema.messages).run();
});

afterEach(() => sqlite.close());

function contactByFirstName(name: string) {
  return db.select().from(schema.contacts).all().find((c) => c.firstName === name)!;
}

function midday() {
  return new Date('2026-07-03T16:00:00.000Z');
}

describe('selectPrimaryChannel', () => {
  it('prefers iMessage when the contact has phone + SMS consent and no explicit preference', () => {
    const maria = contactByFirstName('Maria'); // consentSms + consentEmail both true, no preferredChannel override besides imessage
    expect(selectPrimaryChannel(maria)).toBe('imessage');
  });

  it('falls back to email when there is no SMS consent', () => {
    const ana = contactByFirstName('Ana'); // consentSms: false, consentEmail: true
    expect(selectPrimaryChannel(ana)).toBe('email');
  });

  it('honors an explicit preferred_channel over the default ordering', () => {
    const ana = contactByFirstName('Ana'); // preferredChannel: 'email' in seed data
    expect(ana.preferredChannel).toBe('email');
    expect(selectPrimaryChannel(ana)).toBe('email');
  });

  it('returns null when no channel has both contact info and consent', () => {
    const contact = db.insert(schema.contacts).values({ phones: [], emails: [], consentSms: false, consentEmail: false }).returning().get();
    expect(selectPrimaryChannel(contact)).toBeNull();
  });
});

describe('sendWithChannelFallback', () => {
  it('sends on the primary channel (iMessage) when it is healthy', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const imessage: Channel = { send: async () => ({ externalId: 'ext-1', chatGuid: 'chat-1' }) };
    const email: EmailChannel = { send: async () => { throw new Error('should not be called'); } };

    const result = await sendWithChannelFallback(db, maria, { imessage, email }, {
      leadId: lead.id, contactId: maria.id, body: 'hi', subject: 'n/a', now: midday()
    });

    expect(result).toEqual(expect.objectContaining({ sent: true, channel: 'imessage' }));
  });

  it('falls back to email when iMessage is unhealthy and the contact has email consent', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    upsertSetting(db, 'imessage_health', { ok: false, lastCheckedAt: midday().toISOString(), lastError: 'down', downSince: midday().toISOString() });

    const imessage: Channel = { send: async () => { throw new Error('should not be called while unhealthy'); } };
    const email: EmailChannel = { send: async () => ({ externalId: 'email-ext-1', threadId: 'thread-1' }) };

    const result = await sendWithChannelFallback(db, maria, { imessage, email }, {
      leadId: lead.id, contactId: maria.id, body: 'hi', subject: 'Following up', now: midday()
    });

    expect(result).toEqual(expect.objectContaining({ sent: true, channel: 'email' }));
    const row = db.select().from(schema.messages).where(eq(schema.messages.id, (result as { messageId: number }).messageId)).get()!;
    expect(row.channel).toBe('email');
  });

  it('falls back to email when the iMessage channel throws', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const imessage: Channel = { send: async () => { throw new Error('BlueBubbles network error'); } };
    const email: EmailChannel = { send: async () => ({ externalId: 'email-ext-2', threadId: 'thread-2' }) };

    const result = await sendWithChannelFallback(db, maria, { imessage, email }, {
      leadId: lead.id, contactId: maria.id, body: 'hi', subject: 'Following up', now: midday()
    });

    expect(result).toEqual(expect.objectContaining({ sent: true, channel: 'email' }));
  });

  it('does not fall back on a policy denial that also governs email (quiet hours)', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const imessage: Channel = { send: async () => ({ externalId: 'x', chatGuid: 'x' }) };
    const email: EmailChannel = { send: async () => { throw new Error('should not be called'); } };
    const lateNight = new Date('2026-07-03T03:00:00.000Z');

    const result = await sendWithChannelFallback(db, maria, { imessage, email }, {
      leadId: lead.id, contactId: maria.id, body: 'hi', subject: 'n/a', now: lateNight
    });

    expect(result).toEqual(expect.objectContaining({ sent: false, channel: 'imessage', reason: 'quiet_hours' }));
  });

  it('reports no_eligible_channel when the contact has no usable consent/contact info', async () => {
    const contact = db.insert(schema.contacts).values({ phones: [], emails: [], consentSms: false, consentEmail: false }).returning().get();
    const lead = db.insert(schema.leads).values({
      contactId: contact.id, pipelineId: db.select().from(schema.pipelines).all()[0].id,
      stageId: db.select().from(schema.stages).all()[0].id, intent: 'buy'
    }).returning().get();
    const imessage: Channel = { send: async () => ({ externalId: 'x', chatGuid: 'x' }) };

    const result = await sendWithChannelFallback(db, contact, { imessage }, {
      leadId: lead.id, contactId: contact.id, body: 'hi', subject: 'n/a', now: midday()
    });

    expect(result).toEqual({ sent: false, channel: null, reason: 'no_eligible_channel' });
  });
});
