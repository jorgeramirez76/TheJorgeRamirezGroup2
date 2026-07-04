import Database from 'better-sqlite3';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq } from 'drizzle-orm';
import * as schema from '../src/db/schema.js';
import { applyMigrations } from '../src/db/migrate.js';
import { seedCoreData } from '../src/db/seed.js';
import { DEFAULT_SETTINGS } from '../src/settings/defaults.js';

let sqlite: Database.Database;

beforeEach(() => {
  sqlite = new Database(':memory:');
  applyMigrations(sqlite);
});

afterEach(() => sqlite.close());

describe('database schema and seed data', () => {
  it('creates every locked Phase 1 table', () => {
    const tables = sqlite.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all() as Array<{name: string}>;
    expect(tables.map((t) => t.name)).toEqual(expect.arrayContaining([
      'audit_log', 'contact_tags', 'contacts', 'conversation_summaries', 'custom_fields',
      'enrollments', 'events', 'leads', 'messages', 'pipelines', 'scheduled_actions',
      'settings', 'stages', 'suppressions', 'tags', 'videos', 'workflow_steps', 'workflows'
    ]));
  });

  it('seeds buyer/seller pipelines, locked stages, defaults, fake inbox data', () => {
    const db = drizzle(sqlite, { schema });
    seedCoreData(db);

    const pipelines = db.select().from(schema.pipelines).all();
    expect(pipelines.map((p) => p.name).sort()).toEqual(['Buyer', 'Seller']);

    const stages = db.select().from(schema.stages).all();
    expect(stages.map((s) => s.name)).toEqual(expect.arrayContaining([
      'New', 'Attempting Contact', 'Engaged (AI)', 'Hot / Hand-Raiser',
      'Appointment Set', 'Valuation Delivered', 'Listing Appt', 'Long-Term Nurture'
    ]));

    const settings = db.select().from(schema.settings).all();
    expect(settings).toHaveLength(Object.keys(DEFAULT_SETTINGS).length);
    expect(settings.find((s) => s.key === 'quiet_hours')!.value).toEqual({
      timezone: 'America/New_York', start: '08:30', end: '20:30'
    });
    expect(settings.find((s) => s.key === 'global_pause')!.value).toBe(false);

    expect(db.select().from(schema.contacts).all().length).toBeGreaterThanOrEqual(3);
    expect(db.select().from(schema.leads).all().length).toBeGreaterThanOrEqual(2);
    expect(db.select().from(schema.messages).all().length).toBeGreaterThanOrEqual(3);
  });

  it('dedupes external messages by channel and external_id', () => {
    const db = drizzle(sqlite, { schema });
    const contact = db.insert(schema.contacts).values({ firstName: 'Test', phones: ['+15555550100'], consentSms: true, consentSource: 'test' }).returning().get();
    db.insert(schema.messages).values({ contactId: contact.id, channel: 'imessage', direction: 'in', body: 'hello', externalId: 'bb-1', status: 'received' }).run();
    expect(() => db.insert(schema.messages).values({ contactId: contact.id, channel: 'imessage', direction: 'in', body: 'dupe', externalId: 'bb-1', status: 'received' }).run()).toThrow();
  });
});
