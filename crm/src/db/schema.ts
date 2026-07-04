import { sql } from 'drizzle-orm';
import { integer, primaryKey, sqliteTable, text, uniqueIndex } from 'drizzle-orm/sqlite-core';

const timestamps = {
  createdAt: text('created_at').notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text('updated_at').notNull().default(sql`CURRENT_TIMESTAMP`)
};

export const contacts = sqliteTable('contacts', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  firstName: text('first_name'),
  lastName: text('last_name'),
  phones: text('phones', { mode: 'json' }).$type<string[]>().notNull().default(sql`'[]'`),
  emails: text('emails', { mode: 'json' }).$type<string[]>().notNull().default(sql`'[]'`),
  address: text('address'),
  town: text('town'),
  county: text('county'),
  source: text('source'),
  sourceDetail: text('source_detail'),
  utm: text('utm', { mode: 'json' }).$type<Record<string, unknown>>().notNull().default(sql`'{}'`),
  timezone: text('timezone').notNull().default('America/New_York'),
  imessageHandle: text('imessage_handle'),
  preferredChannel: text('preferred_channel', { enum: ['imessage', 'email'] }),
  consentSms: integer('consent_sms', { mode: 'boolean' }).notNull().default(false),
  consentEmail: integer('consent_email', { mode: 'boolean' }).notNull().default(false),
  consentSource: text('consent_source'),
  consentAt: text('consent_at'),
  doNotContact: integer('do_not_contact', { mode: 'boolean' }).notNull().default(false),
  archived: integer('archived', { mode: 'boolean' }).notNull().default(false),
  ...timestamps
});

export const tags = sqliteTable('tags', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull().unique()
});

export const contactTags = sqliteTable('contact_tags', {
  contactId: integer('contact_id').notNull().references(() => contacts.id, { onDelete: 'cascade' }),
  tagId: integer('tag_id').notNull().references(() => tags.id, { onDelete: 'cascade' })
}, (table) => ({ pk: primaryKey({ columns: [table.contactId, table.tagId] }) }));

export const customFields = sqliteTable('custom_fields', {
  contactId: integer('contact_id').notNull().references(() => contacts.id, { onDelete: 'cascade' }),
  key: text('key').notNull(),
  value: text('value').notNull()
}, (table) => ({ pk: primaryKey({ columns: [table.contactId, table.key] }) }));

export const pipelines = sqliteTable('pipelines', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull().unique()
});

export const stages = sqliteTable('stages', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  pipelineId: integer('pipeline_id').notNull().references(() => pipelines.id, { onDelete: 'cascade' }),
  name: text('name').notNull(),
  position: integer('position').notNull()
}, (table) => ({ pipelinePositionIdx: uniqueIndex('stages_pipeline_position_idx').on(table.pipelineId, table.position) }));

export const leads = sqliteTable('leads', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  contactId: integer('contact_id').notNull().references(() => contacts.id, { onDelete: 'cascade' }),
  pipelineId: integer('pipeline_id').notNull().references(() => pipelines.id, { onDelete: 'restrict' }),
  stageId: integer('stage_id').notNull().references(() => stages.id, { onDelete: 'restrict' }),
  intent: text('intent', { enum: ['buy', 'sell', 'both'] }).notNull(),
  score: integer('score').notNull().default(0),
  scoreBreakdown: text('score_breakdown', { mode: 'json' }).$type<Record<string, unknown>>().notNull().default(sql`'{}'`),
  temperature: text('temperature', { enum: ['HOT', 'WARM', 'COLD'] }).notNull().default('COLD'),
  assignedAutonomy: text('assigned_autonomy', { enum: ['approval', 'guarded', 'full'] }).notNull().default('approval'),
  stageEnteredAt: text('stage_entered_at'),
  nextTouchAt: text('next_touch_at'),
  lastInboundAt: text('last_inbound_at'),
  lastOutboundAt: text('last_outbound_at'),
  videoSentAt: text('video_sent_at'),
  appointmentAt: text('appointment_at'),
  closedReason: text('closed_reason'),
  ...timestamps
});

export const messages = sqliteTable('messages', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  contactId: integer('contact_id').notNull().references(() => contacts.id, { onDelete: 'cascade' }),
  channel: text('channel', { enum: ['imessage', 'email', 'note', 'call_log', 'video'] }).notNull(),
  direction: text('direction', { enum: ['in', 'out'] }).notNull(),
  body: text('body').notNull(),
  subject: text('subject'),
  attachments: text('attachments', { mode: 'json' }).$type<unknown[]>().notNull().default(sql`'[]'`),
  externalId: text('external_id'),
  threadKey: text('thread_key'),
  status: text('status', { enum: ['queued', 'awaiting_approval', 'sent', 'delivered', 'read', 'failed', 'received'] }).notNull(),
  generatedBy: text('generated_by', { enum: ['ai', 'human', 'workflow_template'] }),
  modelUsed: text('model_used'),
  tokensIn: integer('tokens_in'),
  tokensOut: integer('tokens_out'),
  error: text('error'),
  sentAt: text('sent_at'),
  createdAt: text('created_at').notNull().default(sql`CURRENT_TIMESTAMP`)
}, (table) => ({ messageExternalIdx: uniqueIndex('messages_channel_external_id_idx').on(table.channel, table.externalId) }));

export const conversationSummaries = sqliteTable('conversation_summaries', {
  contactId: integer('contact_id').primaryKey().references(() => contacts.id, { onDelete: 'cascade' }),
  summary: text('summary').notNull(),
  facts: text('facts', { mode: 'json' }).$type<Record<string, unknown>>().notNull().default(sql`'{}'`),
  lastMessageId: integer('last_message_id').references(() => messages.id, { onDelete: 'set null' }),
  updatedAt: text('updated_at').notNull().default(sql`CURRENT_TIMESTAMP`)
});

export const workflows = sqliteTable('workflows', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull().unique(),
  trigger: text('trigger', { mode: 'json' }).$type<Record<string, unknown>>().notNull(),
  enabled: integer('enabled', { mode: 'boolean' }).notNull().default(true)
});

export const workflowSteps = sqliteTable('workflow_steps', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  workflowId: integer('workflow_id').notNull().references(() => workflows.id, { onDelete: 'cascade' }),
  position: integer('position').notNull(),
  step: text('step', { mode: 'json' }).$type<Record<string, unknown>>().notNull()
}, (table) => ({ workflowStepPositionIdx: uniqueIndex('workflow_steps_workflow_position_idx').on(table.workflowId, table.position) }));

export const enrollments = sqliteTable('enrollments', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  workflowId: integer('workflow_id').notNull().references(() => workflows.id, { onDelete: 'cascade' }),
  leadId: integer('lead_id').notNull().references(() => leads.id, { onDelete: 'cascade' }),
  currentStep: integer('current_step').notNull().default(0),
  state: text('state', { enum: ['active', 'paused', 'completed', 'exited'] }).notNull().default('active'),
  wakeAt: text('wake_at'),
  context: text('context', { mode: 'json' }).$type<Record<string, unknown>>().notNull().default(sql`'{}'`),
  createdAt: text('created_at').notNull().default(sql`CURRENT_TIMESTAMP`)
});

export const scheduledActions = sqliteTable('scheduled_actions', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  leadId: integer('lead_id').notNull().references(() => leads.id, { onDelete: 'cascade' }),
  kind: text('kind').notNull(),
  payload: text('payload', { mode: 'json' }).$type<Record<string, unknown>>().notNull().default(sql`'{}'`),
  runAt: text('run_at').notNull(),
  status: text('status', { enum: ['queued', 'running', 'completed', 'failed', 'cancelled'] }).notNull().default('queued'),
  attempts: integer('attempts').notNull().default(0),
  lastError: text('last_error'),
  createdAt: text('created_at').notNull().default(sql`CURRENT_TIMESTAMP`)
});

export const events = sqliteTable('events', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  contactId: integer('contact_id').references(() => contacts.id, { onDelete: 'set null' }),
  kind: text('kind').notNull(),
  payload: text('payload', { mode: 'json' }).$type<Record<string, unknown>>().notNull().default(sql`'{}'`),
  createdAt: text('created_at').notNull().default(sql`CURRENT_TIMESTAMP`)
});

export const videos = sqliteTable('videos', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  leadId: integer('lead_id').notNull().references(() => leads.id, { onDelete: 'cascade' }),
  script: text('script').notNull(),
  higgsfieldJobId: text('higgsfield_job_id'),
  status: text('status', { enum: ['scripted', 'queued', 'rendering', 'ready', 'sent', 'failed'] }).notNull().default('scripted'),
  videoUrl: text('video_url'),
  thumbUrl: text('thumb_url'),
  watchEvents: text('watch_events', { mode: 'json' }).$type<unknown[]>().notNull().default(sql`'[]'`),
  ...timestamps
});

export const suppressions = sqliteTable('suppressions', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  kind: text('kind', { enum: ['phone', 'email', 'contact'] }).notNull(),
  value: text('value').notNull(),
  reason: text('reason').notNull(),
  createdAt: text('created_at').notNull().default(sql`CURRENT_TIMESTAMP`)
}, (table) => ({ suppressionValueIdx: uniqueIndex('suppressions_kind_value_idx').on(table.kind, table.value) }));

export const settings = sqliteTable('settings', {
  key: text('key').primaryKey(),
  value: text('value', { mode: 'json' }).$type<unknown>().notNull()
});

export const auditLog = sqliteTable('audit_log', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  actor: text('actor').notNull(),
  action: text('action').notNull(),
  entity: text('entity').notNull(),
  entityId: text('entity_id'),
  detail: text('detail', { mode: 'json' }).$type<Record<string, unknown>>().notNull().default(sql`'{}'`),
  createdAt: text('created_at').notNull().default(sql`CURRENT_TIMESTAMP`)
});
