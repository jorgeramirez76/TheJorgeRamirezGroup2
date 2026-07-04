import { eq } from 'drizzle-orm';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import * as schema from '../../src/db/schema.js';
import { createTestContext, type TestContext } from '../helpers.js';
import { recordEmailOpen, TRANSPARENT_GIF } from '../../src/channels/tracking.js';

let ctx: TestContext;

beforeEach(() => {
  ctx = createTestContext();
});

afterEach(async () => {
  await ctx.app.close();
  ctx.sqlite.close();
});

function contactByFirstName(name: string) {
  return ctx.db.select().from(schema.contacts).all().find((c) => c.firstName === name)!;
}

describe('recordEmailOpen', () => {
  it('records an email_open event for a known outbound message', () => {
    const maria = contactByFirstName('Maria');
    const message = ctx.db.insert(schema.messages).values({
      contactId: maria.id, channel: 'email', direction: 'out', body: 'hi', subject: 's',
      externalId: 'gmail-msg-1', status: 'sent'
    }).returning().get();

    const outcome = recordEmailOpen(ctx.db, 'gmail-msg-1');

    expect(outcome).toEqual({ recorded: true, messageId: message.id });
    const events = ctx.db.select().from(schema.events).where(eq(schema.events.contactId, maria.id)).all();
    expect(events.some((e) => e.kind === 'email_open')).toBe(true);
  });

  it('is a silent no-op for an unknown or missing message id', () => {
    expect(recordEmailOpen(ctx.db, 'no-such-message')).toEqual({ recorded: false });
    expect(recordEmailOpen(ctx.db, undefined)).toEqual({ recorded: false });
    expect(ctx.db.select().from(schema.events).all()).toHaveLength(0);
  });
});

describe('GET /t.gif', () => {
  it('always returns the pixel and records the open when the message id matches', async () => {
    const maria = contactByFirstName('Maria');
    ctx.db.insert(schema.messages).values({
      contactId: maria.id, channel: 'email', direction: 'out', body: 'hi', subject: 's',
      externalId: 'gmail-msg-2', status: 'sent'
    }).run();

    const res = await ctx.app.inject({ method: 'GET', url: '/t.gif?m=gmail-msg-2' });

    expect(res.statusCode).toBe(200);
    expect(res.headers['content-type']).toBe('image/gif');
    expect(Buffer.from(res.rawPayload)).toEqual(TRANSPARENT_GIF);

    const events = ctx.db.select().from(schema.events).where(eq(schema.events.contactId, maria.id)).all();
    expect(events.some((e) => e.kind === 'email_open')).toBe(true);
  });

  it('still returns the pixel when `m` is missing or unknown, without erroring', async () => {
    const missingParam = await ctx.app.inject({ method: 'GET', url: '/t.gif' });
    expect(missingParam.statusCode).toBe(200);

    const unknownId = await ctx.app.inject({ method: 'GET', url: '/t.gif?m=nope' });
    expect(unknownId.statusCode).toBe(200);
    expect(ctx.db.select().from(schema.events).all()).toHaveLength(0);
  });
});
