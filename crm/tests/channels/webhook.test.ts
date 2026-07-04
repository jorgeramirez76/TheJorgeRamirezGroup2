import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { and, eq } from 'drizzle-orm';
import * as schema from '../../src/db/schema.js';
import { createTestContext, type TestContext } from '../helpers.js';

let ctx: TestContext;

beforeEach(() => {
  ctx = createTestContext();
});

afterEach(async () => {
  await ctx.app.close();
  ctx.sqlite.close();
});

function newMessagePayload(overrides: Partial<{ guid: string; text: string; isFromMe: boolean; address: string }> = {}) {
  return {
    type: 'new-message',
    data: {
      guid: overrides.guid ?? 'bb-guid-1',
      text: overrides.text ?? 'Hello, checking in',
      isFromMe: overrides.isFromMe ?? false,
      handle: { address: overrides.address ?? '+15555550101' },
      chatGuid: 'iMessage;-;+15555550101',
      dateCreated: 1_700_000_000_000
    }
  };
}

describe('POST /webhooks/bluebubbles — inbound normalization', () => {
  it('is idempotent: delivering the same message guid twice inserts exactly one row', async () => {
    const payload = newMessagePayload({ guid: 'dup-guid' });

    const first = await ctx.app.inject({ method: 'POST', url: '/webhooks/bluebubbles', payload });
    expect(first.statusCode).toBe(200);
    expect(first.json().status).toBe('received');

    const second = await ctx.app.inject({ method: 'POST', url: '/webhooks/bluebubbles', payload });
    expect(second.statusCode).toBe(200);
    expect(second.json().status).toBe('ignored_duplicate');

    const rows = ctx.db.select().from(schema.messages)
      .where(and(eq(schema.messages.channel, 'imessage'), eq(schema.messages.externalId, 'dup-guid'))).all();
    expect(rows).toHaveLength(1);
  });

  it('ignores isFromMe messages (Jorge sending from his own phone) and stores nothing', async () => {
    const res = await ctx.app.inject({ method: 'POST', url: '/webhooks/bluebubbles', payload: newMessagePayload({ guid: 'from-me-1', isFromMe: true }) });
    expect(res.json().status).toBe('ignored_from_me');
    const rows = ctx.db.select().from(schema.messages).where(eq(schema.messages.externalId, 'from-me-1')).all();
    expect(rows).toHaveLength(0);
  });

  it('resolves an inbound handle to an existing contact by phone', async () => {
    const res = await ctx.app.inject({ method: 'POST', url: '/webhooks/bluebubbles', payload: newMessagePayload({ guid: 'known-1', address: '+15555550101' }) });
    const body = res.json();
    expect(body.status).toBe('received');
    expect(body.shellContactCreated).toBe(false);

    const maria = ctx.db.select().from(schema.contacts).all().find((c) => c.phones.includes('+15555550101'));
    expect(maria).toBeTruthy();
    expect(body.contactId).toBe(maria!.id);
  });

  it('creates a needs-review shell contact for an unknown sender and does not auto-nurture it', async () => {
    const res = await ctx.app.inject({ method: 'POST', url: '/webhooks/bluebubbles', payload: newMessagePayload({ guid: 'unknown-1', address: '+19995551234' }) });
    const body = res.json();
    expect(body.status).toBe('received');
    expect(body.shellContactCreated).toBe(true);

    const contact = ctx.db.select().from(schema.contacts).where(eq(schema.contacts.id, body.contactId)).get()!;
    expect(contact.consentSms).toBe(false);
    expect(contact.phones).toEqual(['+19995551234']);

    const tag = ctx.db.select().from(schema.tags).where(eq(schema.tags.name, 'needs-review')).get()!;
    const link = ctx.db.select().from(schema.contactTags)
      .where(and(eq(schema.contactTags.contactId, contact.id), eq(schema.contactTags.tagId, tag.id))).get();
    expect(link).toBeTruthy();
  });

  it('updates delivery and read status from updated-message events', async () => {
    await ctx.app.inject({ method: 'POST', url: '/webhooks/bluebubbles', payload: newMessagePayload({ guid: 'status-1' }) });

    const delivered = await ctx.app.inject({
      method: 'POST', url: '/webhooks/bluebubbles',
      payload: { type: 'updated-message', data: { guid: 'status-1', dateDelivered: 1_700_000_001_000 } }
    });
    expect(delivered.json()).toEqual({ status: 'status_updated', messageId: expect.any(Number), newStatus: 'delivered' });

    const read = await ctx.app.inject({
      method: 'POST', url: '/webhooks/bluebubbles',
      payload: { type: 'updated-message', data: { guid: 'status-1', dateDelivered: 1_700_000_001_000, dateRead: 1_700_000_002_000 } }
    });
    expect(read.json().newStatus).toBe('read');

    const row = ctx.db.select().from(schema.messages).where(eq(schema.messages.externalId, 'status-1')).get()!;
    expect(row.status).toBe('read');
  });

  it('runs the STOP flow before anything else and only confirms once even if STOP repeats', async () => {
    const first = await ctx.app.inject({ method: 'POST', url: '/webhooks/bluebubbles', payload: newMessagePayload({ guid: 'stop-1', text: 'STOP' }) });
    expect(first.json().optOut).toBe(true);

    const second = await ctx.app.inject({ method: 'POST', url: '/webhooks/bluebubbles', payload: newMessagePayload({ guid: 'stop-2', text: 'please STOP texting me' }) });
    expect(second.json().optOut).toBe(true);

    const contactId = first.json().contactId;
    const contact = ctx.db.select().from(schema.contacts).where(eq(schema.contacts.id, contactId)).get()!;
    expect(contact.doNotContact).toBe(true);

    const confirmations = ctx.db.select().from(schema.messages)
      .where(and(eq(schema.messages.contactId, contactId), eq(schema.messages.direction, 'out'), eq(schema.messages.generatedBy, 'workflow_template'))).all();
    expect(confirmations).toHaveLength(1);
  });
});
