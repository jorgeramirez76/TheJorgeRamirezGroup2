import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { buildApp } from '../src/app.js';
import { createTestContext, type TestContext } from './helpers.js';

let ctx: TestContext;

beforeEach(() => {
  ctx = createTestContext();
});

afterEach(async () => {
  await ctx.app.close();
  ctx.sqlite.close();
});

describe('core CRUD API', () => {
  it('round-trips contacts, tags, custom fields, leads, and messages', async () => {
    const app = ctx.app;

    const createdContact = await app.inject({ method: 'POST', url: '/api/contacts', payload: {
      firstName: 'Avery', lastName: 'Seller', phones: ['+15555550101'], emails: ['avery@example.com'],
      town: 'Summit', source: 'website', consentSms: true, consentEmail: true, consentSource: 'website_form'
    }});
    expect(createdContact.statusCode).toBe(201);
    const contact = createdContact.json();
    expect(contact.id).toBeTypeOf('number');

    const tagRes = await app.inject({ method: 'POST', url: '/api/tags', payload: { name: 'valuation-lead' }});
    expect(tagRes.statusCode).toBe(201);
    const tag = tagRes.json();

    expect((await app.inject({ method: 'POST', url: `/api/contacts/${contact.id}/tags/${tag.id}` })).statusCode).toBe(204);
    expect((await app.inject({ method: 'PUT', url: `/api/contacts/${contact.id}/custom-fields/timeline`, payload: { value: '60 days' }})).statusCode).toBe(200);

    const pipelines = (await app.inject({ method: 'GET', url: '/api/pipelines' })).json();
    const seller = pipelines.find((p: any) => p.name === 'Seller');
    expect(seller.stages.length).toBeGreaterThan(5);

    const leadRes = await app.inject({ method: 'POST', url: '/api/leads', payload: {
      contactId: contact.id, pipelineId: seller.id, stageId: seller.stages[0].id, intent: 'sell', score: 72,
      scoreBreakdown: { source: 20, engagement: 30, fit: 22 }, temperature: 'HOT'
    }});
    expect(leadRes.statusCode).toBe(201);
    expect(leadRes.json().temperature).toBe('HOT');

    const msgRes = await app.inject({ method: 'POST', url: '/api/messages', payload: {
      contactId: contact.id, channel: 'imessage', direction: 'out', body: 'Thanks for reaching out — want the full number?', status: 'queued', generatedBy: 'human'
    }});
    expect(msgRes.statusCode).toBe(201);

    const thread = (await app.inject({ method: 'GET', url: `/api/contacts/${contact.id}/messages` })).json();
    expect(thread).toHaveLength(1);
    expect(thread[0].body).toContain('full number');
  });

  it('exposes and updates seeded settings safely', async () => {
    const settings = (await ctx.app.inject({ method: 'GET', url: '/api/settings' })).json();
    expect(settings.global_pause).toBe(false);
    expect(settings.quiet_hours).toEqual({ timezone: 'America/New_York', start: '08:30', end: '20:30' });

    const pause = await ctx.app.inject({ method: 'PUT', url: '/api/settings/global_pause', payload: { value: true }});
    expect(pause.statusCode).toBe(200);
    expect(pause.json()).toEqual({ key: 'global_pause', value: true });
  });
});
