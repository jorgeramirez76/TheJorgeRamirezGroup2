import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq } from 'drizzle-orm';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import * as schema from '../src/db/schema.js';
import { applyMigrations } from '../src/db/migrate.js';
import { seedCoreData } from '../src/db/seed.js';
import { sendCampaignEmail, sendOutboundEmail } from '../src/sendgate/send.js';
import { upsertSetting } from '../src/settings/store.js';
import { GmailChannel } from '../src/channels/gmail.js';
import { FakeGmailClient } from './helpers/fake-gmail-client.js';

let sqlite: Database.Database;
let db: ReturnType<typeof drizzle<typeof schema>>;

beforeEach(() => {
  sqlite = new Database(':memory:');
  applyMigrations(sqlite);
  db = drizzle(sqlite, { schema });
  seedCoreData(db);
  db.delete(schema.messages).run(); // seed data includes a real-timestamped email row that would collide with pacing checks
});

afterEach(() => sqlite.close());

function contactByFirstName(name: string) {
  return db.select().from(schema.contacts).all().find((c) => c.firstName === name)!;
}

function midday() {
  return new Date('2026-07-03T16:00:00.000Z'); // noon America/New_York, inside the default quiet-hours window
}

function lateNight() {
  return new Date('2026-07-03T03:00:00.000Z'); // 11pm America/New_York the prior night, outside the window
}

describe('sendOutboundEmail', () => {
  it('reschedules via scheduled_actions instead of sending when the gate blocks it', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });

    const result = await sendOutboundEmail(db, channel, client, {
      leadId: lead.id, contactId: maria.id, to: maria.emails[0], subject: 'Hi', body: 'hello', now: lateNight()
    });

    expect(result.sent).toBe(false);
    if (!result.sent) {
      expect(result.reason).toBe('quiet_hours');
      const scheduled = db.select().from(schema.scheduledActions).where(eq(schema.scheduledActions.id, result.scheduledActionId)).get()!;
      expect(scheduled.status).toBe('queued');
      expect(scheduled.kind).toBe('send_message');
    }
    expect(client.sent).toHaveLength(0);
  });

  it('sends a fresh email and records the message with the returned Gmail threadId', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });

    const result = await sendOutboundEmail(db, channel, client, {
      leadId: lead.id, contactId: maria.id, to: maria.emails[0], subject: 'Hi', body: 'hello', now: midday()
    });

    expect(result.sent).toBe(true);
    if (result.sent) {
      const row = db.select().from(schema.messages).where(eq(schema.messages.id, result.messageId)).get()!;
      expect(row.status).toBe('sent');
      expect(row.channel).toBe('email');
      expect(row.threadKey).toBe(result.threadId);
    }
  });

  it('threads a reply onto the contact\'s last inbound email using its Message-ID header', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });

    client.addInboundMessage({ id: 'inbound-1', threadId: 'thread-1', from: maria.emails[0], body: 'question', messageIdHeader: '<inbound-1@mail.gmail.com>' });
    db.insert(schema.messages).values({
      contactId: maria.id, channel: 'email', direction: 'in', body: 'question',
      externalId: 'inbound-1', threadKey: 'thread-1', status: 'received'
    }).run();

    await sendOutboundEmail(db, channel, client, {
      leadId: lead.id, contactId: maria.id, to: maria.emails[0], subject: 'Re: question', body: 'answer',
      isReply: true, now: midday()
    });

    expect(client.sent[0].headers['In-Reply-To']).toBe('<inbound-1@mail.gmail.com>');
    expect(client.sent[0].threadId).toBe('thread-1');
  });
});

describe('sendCampaignEmail', () => {
  it('appends the CAN-SPAM footer and a List-Unsubscribe header', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });

    await sendCampaignEmail(db, channel, {
      leadId: lead.id, contactId: maria.id, to: maria.emails[0], subject: 'Market update', body: 'Prices moved this month.',
      fromEmail: 'jorgeramirez76@gmail.com', now: midday()
    });

    expect(client.sent[0].body).toContain('Prices moved this month.');
    expect(client.sent[0].body).toContain('The Jorge Ramirez Group');
    expect(client.sent[0].body.toLowerCase()).toContain('unsubscribe');
    expect(client.sent[0].headers['List-Unsubscribe']).toBe('<mailto:jorgeramirez76@gmail.com?subject=unsubscribe>');
  });

  it('enforces 20s+ spacing between campaign sends regardless of recipient', async () => {
    const maria = contactByFirstName('Maria');
    const david = contactByFirstName('David');
    const marialead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    const davidLead = db.select().from(schema.leads).where(eq(schema.leads.contactId, david.id)).get()!;
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });
    const now = midday();

    const first = await sendCampaignEmail(db, channel, {
      leadId: marialead.id, contactId: maria.id, to: maria.emails[0], subject: 'Update', body: 'body',
      fromEmail: 'jorgeramirez76@gmail.com', now
    });
    expect(first.sent).toBe(true);

    const tooSoon = new Date(now.getTime() + 5_000);
    const second = await sendCampaignEmail(db, channel, {
      leadId: davidLead.id, contactId: david.id, to: david.emails[0], subject: 'Update', body: 'body',
      fromEmail: 'jorgeramirez76@gmail.com', now: tooSoon
    });

    expect(second.sent).toBe(false);
    if (!second.sent) expect(second.reason).toBe('email_campaign_pacing');
    expect(client.sent).toHaveLength(1);
  });

  it('enforces the campaign daily cap independently of the global daily cap', async () => {
    const maria = contactByFirstName('Maria');
    const lead = db.select().from(schema.leads).where(eq(schema.leads.contactId, maria.id)).get()!;
    upsertSetting(db, 'email_campaign_daily_cap', 1);
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });
    const now = midday();

    const first = await sendCampaignEmail(db, channel, {
      leadId: lead.id, contactId: maria.id, to: maria.emails[0], subject: 'Update 1', body: 'body',
      fromEmail: 'jorgeramirez76@gmail.com', now
    });
    expect(first.sent).toBe(true);

    const second = await sendCampaignEmail(db, channel, {
      leadId: lead.id, contactId: maria.id, to: maria.emails[0], subject: 'Update 2', body: 'body',
      fromEmail: 'jorgeramirez76@gmail.com', now: new Date(now.getTime() + 60_000)
    });

    expect(second.sent).toBe(false);
    if (!second.sent) expect(second.reason).toBe('email_campaign_daily_cap');
  });
});
