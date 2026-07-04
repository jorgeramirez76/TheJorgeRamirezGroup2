import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { and, eq } from 'drizzle-orm';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import * as schema from '../../src/db/schema.js';
import { applyMigrations } from '../../src/db/migrate.js';
import { seedCoreData } from '../../src/db/seed.js';
import { pollGmailInbox } from '../../src/channels/gmail-poller.js';
import { getSettings, upsertSetting } from '../../src/settings/store.js';
import { FakeGmailClient } from '../helpers/fake-gmail-client.js';

let sqlite: Database.Database;
let db: ReturnType<typeof drizzle<typeof schema>>;

beforeEach(() => {
  sqlite = new Database(':memory:');
  applyMigrations(sqlite);
  db = drizzle(sqlite, { schema });
  seedCoreData(db);
});

afterEach(() => sqlite.close());

function contactByFirstName(name: string) {
  return db.select().from(schema.contacts).all().find((c) => c.firstName === name)!;
}

describe('pollGmailInbox', () => {
  it('seeds the cursor and processes nothing on the very first run (no mailbox replay)', async () => {
    const client = new FakeGmailClient();
    client.addInboundMessage({ id: 'm1', threadId: 't1', from: 'maria@example.com', body: 'hi' }); // predates the seed

    const result = await pollGmailInbox(db, client);

    expect(result.cursorBefore).toBeNull();
    expect(result.processed).toBe(0);
    expect(result.ignored).toBe(0);
    expect(getSettings(db).gmail_history_id).toBe(result.cursorAfter);

    const rows = db.select().from(schema.messages).where(eq(schema.messages.externalId, 'm1')).all();
    expect(rows).toHaveLength(0);
  });

  it('resumes from the persisted cursor on a later poll — proving the cursor survives a restart', async () => {
    const client = new FakeGmailClient();
    await pollGmailInbox(db, client); // seed baseline

    const maria = contactByFirstName('Maria');
    client.addInboundMessage({ id: 'm2', threadId: 't2', from: maria.emails[0], body: 'Curious about my home value.' });

    // A fresh drizzle handle over the same sqlite connection stands in for "the process restarted
    // and reads settings.gmail_history_id back from disk" — nothing about the cursor lives in JS state.
    const dbAfterRestart = drizzle(sqlite, { schema });
    const result = await pollGmailInbox(dbAfterRestart, client);

    expect(result.cursorBefore).not.toBeNull();
    expect(result.processed).toBe(1);
    const row = db.select().from(schema.messages).where(eq(schema.messages.externalId, 'm2')).get()!;
    expect(row.contactId).toBe(maria.id);
    expect(row.direction).toBe('in');
    expect(row.status).toBe('received');
  });

  it('is idempotent: re-processing the same history record does not insert a duplicate row', async () => {
    const client = new FakeGmailClient();
    await pollGmailInbox(db, client); // seed baseline cursor

    const maria = contactByFirstName('Maria');
    client.addInboundMessage({ id: 'm3', threadId: 't3', from: maria.emails[0], body: 'hello again' });

    const cursorBeforeThisMessage = String(getSettings(db).gmail_history_id);
    const first = await pollGmailInbox(db, client);
    expect(first.processed).toBe(1);

    // Simulate the cursor never having been persisted after a prior crash: rewind it and
    // re-poll, forcing the same messagesAdded history record to come back a second time.
    upsertSetting(db, 'gmail_history_id', cursorBeforeThisMessage);
    const second = await pollGmailInbox(db, client);

    expect(second.processed).toBe(0);
    expect(second.ignored).toBe(1);
    const rows = db.select().from(schema.messages).where(eq(schema.messages.externalId, 'm3')).all();
    expect(rows).toHaveLength(1);
  });

  it('ignores mail from unknown senders with no prior CRM thread (Jorge\'s personal inbox)', async () => {
    const client = new FakeGmailClient();
    await pollGmailInbox(db, client);

    client.addInboundMessage({ id: 'm4', threadId: 't4', from: 'stranger@example.com', body: 'unrelated personal email' });
    const result = await pollGmailInbox(db, client);

    expect(result.processed).toBe(0);
    expect(result.ignored).toBe(1);
    expect(db.select().from(schema.messages).where(eq(schema.messages.externalId, 'm4')).all()).toHaveLength(0);
  });

  it('processes a reply from a non-contact address if it lands in a thread the CRM already started', async () => {
    const client = new FakeGmailClient();
    await pollGmailInbox(db, client);

    const maria = contactByFirstName('Maria');
    db.insert(schema.messages).values({
      contactId: maria.id, channel: 'email', direction: 'out', body: 'Intro email', subject: 'Hi',
      externalId: 'outbound-1', threadKey: 'thread-existing', status: 'sent'
    }).run();

    // Maria replies from a different address than the one on file, but within the same Gmail thread.
    client.addInboundMessage({ id: 'm5', threadId: 'thread-existing', from: 'maria.alt@example.com', body: 'replying from my other email' });
    const result = await pollGmailInbox(db, client);

    expect(result.processed).toBe(1);
    const row = db.select().from(schema.messages).where(eq(schema.messages.externalId, 'm5')).get()!;
    expect(row.contactId).toBe(maria.id);
  });

  it('ignores its own sent mail surfacing in history (labelIds includes SENT)', async () => {
    const client = new FakeGmailClient();
    await pollGmailInbox(db, client);

    const maria = contactByFirstName('Maria');
    client.addInboundMessage({ id: 'm6', threadId: 't6', from: maria.emails[0], body: 'echo of my own reply', labelIds: ['SENT'] });
    const result = await pollGmailInbox(db, client);

    expect(result.processed).toBe(0);
    expect(result.ignored).toBe(1);
  });

  it('runs the STOP flow on inbound email before any AI/workflow handling', async () => {
    const client = new FakeGmailClient();
    await pollGmailInbox(db, client);

    const maria = contactByFirstName('Maria');
    client.addInboundMessage({ id: 'm7', threadId: 't7', from: maria.emails[0], body: 'please unsubscribe me' });
    await pollGmailInbox(db, client);

    const updated = db.select().from(schema.contacts).where(eq(schema.contacts.id, maria.id)).get()!;
    expect(updated.doNotContact).toBe(true);
    const confirmations = db.select().from(schema.messages)
      .where(and(eq(schema.messages.contactId, maria.id), eq(schema.messages.generatedBy, 'workflow_template'))).all();
    expect(confirmations).toHaveLength(1);
  });

  it('resets the cursor baseline instead of crashing when startHistoryId is too old for Gmail to diff', async () => {
    const client = new FakeGmailClient();
    await pollGmailInbox(db, client);

    const maria = contactByFirstName('Maria');
    client.addInboundMessage({ id: 'm8', threadId: 't8', from: maria.emails[0], body: 'missed during the gap' });
    client.simulateHistoryGap();

    const result = await pollGmailInbox(db, client);

    expect(result.processed).toBe(0);
    expect(result.cursorAfter).toBe(client.currentHistoryId());
    // The gap message is not retroactively processed — same trade-off as BlueBubbles' cursor.
    expect(db.select().from(schema.messages).where(eq(schema.messages.externalId, 'm8')).all()).toHaveLength(0);

    // Confirm polling recovers cleanly afterwards.
    client.addInboundMessage({ id: 'm9', threadId: 't9', from: maria.emails[0], body: 'after the gap' });
    const recovered = await pollGmailInbox(db, client);
    expect(recovered.processed).toBe(1);
  });
});
