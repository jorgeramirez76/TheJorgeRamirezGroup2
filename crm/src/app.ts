import Fastify, { type FastifyInstance } from 'fastify';
import cors from '@fastify/cors';
import { asc, eq } from 'drizzle-orm';
import type { CrmDb } from './db/client.js';
import * as schema from './db/schema.js';
import { seedCoreData } from './db/seed.js';
import { DEFAULT_SETTINGS } from './settings/defaults.js';
import {
  ContactInput, ContactPatchInput, CustomFieldInput, LeadInput, LeadPatchInput,
  MessageInput, MessagePatchInput, PipelineInput, SettingInput, StageInput, TagInput
} from './validation.js';
import { parseSettings } from './serializers.js';

export type BuildAppOptions = { db: CrmDb; logger?: boolean | object };

type RouteParams = { id: string };
type ContactFieldParams = { id: string; key: string };
type ContactTagParams = { id: string; tagId: string };

type PipelineWithStages = typeof schema.pipelines.$inferSelect & { stages: Array<typeof schema.stages.$inferSelect> };

function parseId(id: string) {
  const parsed = Number(id);
  if (!Number.isInteger(parsed) || parsed < 1) throw new Error('Invalid id');
  return parsed;
}

function touch() {
  return new Date().toISOString();
}

function notFound(app: FastifyInstance, entity: string) {
  const error = new Error(`${entity} not found`) as Error & { statusCode: number };
  error.statusCode = 404;
  return error;
}

function insertSettingsDefaults(db: CrmDb) {
  for (const [key, value] of Object.entries(DEFAULT_SETTINGS)) {
    db.insert(schema.settings).values({ key, value }).onConflictDoNothing().run();
  }
}

export function buildApp({ db, logger = { level: process.env.CRM_LOG_LEVEL ?? 'info' } }: BuildAppOptions) {
  const app = Fastify({ logger });
  app.register(cors, { origin: false });

  app.get('/healthz', async () => ({ ok: true, service: 'jrg-crm' }));

  app.post('/api/seed', async (_request, reply) => {
    seedCoreData(db);
    return reply.code(204).send();
  });

  app.get('/api/contacts', async () => db.select().from(schema.contacts).orderBy(asc(schema.contacts.id)).all());

  app.post('/api/contacts', async (request, reply) => {
    const input = ContactInput.parse(request.body);
    const row = db.insert(schema.contacts).values({
      ...input,
      utm: input.utm ?? {},
      phones: input.phones ?? [],
      emails: input.emails ?? [],
      consentAt: input.consentAt ?? (input.consentSource ? touch() : null)
    }).returning().get();
    return reply.code(201).send(row);
  });

  app.get<{ Params: RouteParams }>('/api/contacts/:id', async (request) => {
    const row = db.select().from(schema.contacts).where(eq(schema.contacts.id, parseId(request.params.id))).get();
    if (!row) throw notFound(app, 'contact');
    return row;
  });

  app.patch<{ Params: RouteParams }>('/api/contacts/:id', async (request) => {
    const id = parseId(request.params.id);
    const input = ContactPatchInput.parse(request.body);
    const row = db.update(schema.contacts).set({ ...input, updatedAt: touch() }).where(eq(schema.contacts.id, id)).returning().get();
    if (!row) throw notFound(app, 'contact');
    return row;
  });

  app.delete<{ Params: RouteParams }>('/api/contacts/:id', async (request, reply) => {
    db.delete(schema.contacts).where(eq(schema.contacts.id, parseId(request.params.id))).run();
    return reply.code(204).send();
  });

  app.get('/api/tags', async () => db.select().from(schema.tags).orderBy(asc(schema.tags.name)).all());

  app.post('/api/tags', async (request, reply) => {
    const input = TagInput.parse(request.body);
    const row = db.insert(schema.tags).values(input).onConflictDoUpdate({ target: schema.tags.name, set: { name: input.name } }).returning().get();
    return reply.code(201).send(row);
  });

  app.patch<{ Params: RouteParams }>('/api/tags/:id', async (request) => {
    const input = TagInput.parse(request.body);
    const row = db.update(schema.tags).set(input).where(eq(schema.tags.id, parseId(request.params.id))).returning().get();
    if (!row) throw notFound(app, 'tag');
    return row;
  });

  app.delete<{ Params: RouteParams }>('/api/tags/:id', async (request, reply) => {
    db.delete(schema.tags).where(eq(schema.tags.id, parseId(request.params.id))).run();
    return reply.code(204).send();
  });

  app.post<{ Params: ContactTagParams }>('/api/contacts/:id/tags/:tagId', async (request, reply) => {
    db.insert(schema.contactTags).values({ contactId: parseId(request.params.id), tagId: parseId(request.params.tagId) }).onConflictDoNothing().run();
    return reply.code(204).send();
  });

  app.delete<{ Params: ContactTagParams }>('/api/contacts/:id/tags/:tagId', async (request, reply) => {
    db.delete(schema.contactTags).where(eq(schema.contactTags.contactId, parseId(request.params.id))).run();
    return reply.code(204).send();
  });

  app.get<{ Params: RouteParams }>('/api/contacts/:id/custom-fields', async (request) => {
    return db.select().from(schema.customFields).where(eq(schema.customFields.contactId, parseId(request.params.id))).orderBy(asc(schema.customFields.key)).all();
  });

  app.put<{ Params: ContactFieldParams }>('/api/contacts/:id/custom-fields/:key', async (request) => {
    const contactId = parseId(request.params.id);
    const input = CustomFieldInput.parse(request.body);
    return db.insert(schema.customFields).values({ contactId, key: request.params.key, value: input.value }).onConflictDoUpdate({
      target: [schema.customFields.contactId, schema.customFields.key], set: { value: input.value }
    }).returning().get();
  });

  app.delete<{ Params: ContactFieldParams }>('/api/contacts/:id/custom-fields/:key', async (request, reply) => {
    db.delete(schema.customFields).where(eq(schema.customFields.contactId, parseId(request.params.id))).run();
    return reply.code(204).send();
  });

  app.get('/api/pipelines', async () => {
    const pipelines = db.select().from(schema.pipelines).orderBy(asc(schema.pipelines.id)).all();
    return pipelines.map((pipeline): PipelineWithStages => ({
      ...pipeline,
      stages: db.select().from(schema.stages).where(eq(schema.stages.pipelineId, pipeline.id)).orderBy(asc(schema.stages.position)).all()
    }));
  });

  app.post('/api/pipelines', async (request, reply) => {
    const input = PipelineInput.parse(request.body);
    const row = db.insert(schema.pipelines).values(input).returning().get();
    return reply.code(201).send(row);
  });

  app.patch<{ Params: RouteParams }>('/api/pipelines/:id', async (request) => {
    const input = PipelineInput.parse(request.body);
    const row = db.update(schema.pipelines).set(input).where(eq(schema.pipelines.id, parseId(request.params.id))).returning().get();
    if (!row) throw notFound(app, 'pipeline');
    return row;
  });

  app.delete<{ Params: RouteParams }>('/api/pipelines/:id', async (request, reply) => {
    db.delete(schema.pipelines).where(eq(schema.pipelines.id, parseId(request.params.id))).run();
    return reply.code(204).send();
  });

  app.get('/api/stages', async () => db.select().from(schema.stages).orderBy(asc(schema.stages.pipelineId), asc(schema.stages.position)).all());

  app.post('/api/stages', async (request, reply) => {
    const input = StageInput.parse(request.body);
    const row = db.insert(schema.stages).values(input).returning().get();
    return reply.code(201).send(row);
  });

  app.patch<{ Params: RouteParams }>('/api/stages/:id', async (request) => {
    const input = StageInput.partial().parse(request.body);
    const row = db.update(schema.stages).set(input).where(eq(schema.stages.id, parseId(request.params.id))).returning().get();
    if (!row) throw notFound(app, 'stage');
    return row;
  });

  app.delete<{ Params: RouteParams }>('/api/stages/:id', async (request, reply) => {
    db.delete(schema.stages).where(eq(schema.stages.id, parseId(request.params.id))).run();
    return reply.code(204).send();
  });

  app.get('/api/leads', async () => db.select().from(schema.leads).orderBy(asc(schema.leads.id)).all());

  app.post('/api/leads', async (request, reply) => {
    const input = LeadInput.parse(request.body);
    const row = db.insert(schema.leads).values({ ...input, scoreBreakdown: input.scoreBreakdown ?? {}, stageEnteredAt: input.stageEnteredAt ?? touch() }).returning().get();
    return reply.code(201).send(row);
  });

  app.patch<{ Params: RouteParams }>('/api/leads/:id', async (request) => {
    const input = LeadPatchInput.parse(request.body);
    const row = db.update(schema.leads).set({ ...input, updatedAt: touch() }).where(eq(schema.leads.id, parseId(request.params.id))).returning().get();
    if (!row) throw notFound(app, 'lead');
    return row;
  });

  app.delete<{ Params: RouteParams }>('/api/leads/:id', async (request, reply) => {
    db.delete(schema.leads).where(eq(schema.leads.id, parseId(request.params.id))).run();
    return reply.code(204).send();
  });

  app.get('/api/messages', async () => db.select().from(schema.messages).orderBy(asc(schema.messages.id)).all());

  app.get<{ Params: RouteParams }>('/api/contacts/:id/messages', async (request) => db.select().from(schema.messages).where(eq(schema.messages.contactId, parseId(request.params.id))).orderBy(asc(schema.messages.createdAt), asc(schema.messages.id)).all());

  app.post('/api/messages', async (request, reply) => {
    const input = MessageInput.parse(request.body);
    const row = db.insert(schema.messages).values({ ...input, attachments: input.attachments ?? [] }).returning().get();
    return reply.code(201).send(row);
  });

  app.patch<{ Params: RouteParams }>('/api/messages/:id', async (request) => {
    const input = MessagePatchInput.parse(request.body);
    const row = db.update(schema.messages).set(input).where(eq(schema.messages.id, parseId(request.params.id))).returning().get();
    if (!row) throw notFound(app, 'message');
    return row;
  });

  app.delete<{ Params: RouteParams }>('/api/messages/:id', async (request, reply) => {
    db.delete(schema.messages).where(eq(schema.messages.id, parseId(request.params.id))).run();
    return reply.code(204).send();
  });

  app.get('/api/settings', async () => {
    insertSettingsDefaults(db);
    return parseSettings(db.select().from(schema.settings).orderBy(asc(schema.settings.key)).all());
  });

  app.put<{ Params: { key: string } }>('/api/settings/:key', async (request) => {
    const { value } = SettingInput.parse(request.body);
    const row = db.insert(schema.settings).values({ key: request.params.key, value }).onConflictDoUpdate({
      target: schema.settings.key,
      set: { value }
    }).returning().get();
    return row;
  });

  return app;
}
