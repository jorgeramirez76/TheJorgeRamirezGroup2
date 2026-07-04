import { z } from 'zod';

export const jsonObject = z.record(z.string(), z.unknown()).default({});
export const jsonArray = z.array(z.unknown()).default([]);

export const ContactInput = z.object({
  firstName: z.string().optional().nullable(),
  lastName: z.string().optional().nullable(),
  phones: z.array(z.string()).default([]),
  emails: z.array(z.string().email()).default([]),
  address: z.string().optional().nullable(),
  town: z.string().optional().nullable(),
  county: z.string().optional().nullable(),
  source: z.string().optional().nullable(),
  sourceDetail: z.string().optional().nullable(),
  utm: jsonObject.optional(),
  timezone: z.string().default('America/New_York'),
  imessageHandle: z.string().optional().nullable(),
  preferredChannel: z.enum(['imessage', 'email']).optional().nullable(),
  consentSms: z.boolean().default(false),
  consentEmail: z.boolean().default(false),
  consentSource: z.string().optional().nullable(),
  consentAt: z.string().datetime().optional().nullable(),
  doNotContact: z.boolean().default(false),
  archived: z.boolean().default(false)
});

export const ContactPatchInput = ContactInput.partial();
export const TagInput = z.object({ name: z.string().min(1) });
export const CustomFieldInput = z.object({ value: z.string() });

export const PipelineInput = z.object({ name: z.string().min(1) });
export const StageInput = z.object({ pipelineId: z.number().int().positive(), name: z.string().min(1), position: z.number().int().positive() });

export const LeadInput = z.object({
  contactId: z.number().int().positive(),
  pipelineId: z.number().int().positive(),
  stageId: z.number().int().positive(),
  intent: z.enum(['buy', 'sell', 'both']),
  score: z.number().int().min(0).max(100).default(0),
  scoreBreakdown: jsonObject.optional(),
  temperature: z.enum(['HOT', 'WARM', 'COLD']).default('COLD'),
  assignedAutonomy: z.enum(['approval', 'guarded', 'full']).default('approval'),
  stageEnteredAt: z.string().optional().nullable(),
  nextTouchAt: z.string().optional().nullable(),
  lastInboundAt: z.string().optional().nullable(),
  lastOutboundAt: z.string().optional().nullable(),
  videoSentAt: z.string().optional().nullable(),
  appointmentAt: z.string().optional().nullable(),
  closedReason: z.string().optional().nullable()
});
export const LeadPatchInput = LeadInput.partial();

export const MessageInput = z.object({
  contactId: z.number().int().positive(),
  channel: z.enum(['imessage', 'email', 'note', 'call_log', 'video']),
  direction: z.enum(['in', 'out']),
  body: z.string().min(1),
  subject: z.string().optional().nullable(),
  attachments: jsonArray.optional(),
  externalId: z.string().optional().nullable(),
  threadKey: z.string().optional().nullable(),
  status: z.enum(['queued', 'awaiting_approval', 'sent', 'delivered', 'read', 'failed', 'received']),
  generatedBy: z.enum(['ai', 'human', 'workflow_template']).optional().nullable(),
  modelUsed: z.string().optional().nullable(),
  tokensIn: z.number().int().optional().nullable(),
  tokensOut: z.number().int().optional().nullable(),
  error: z.string().optional().nullable(),
  sentAt: z.string().optional().nullable()
});
export const MessagePatchInput = MessageInput.partial();
export const SettingInput = z.object({ value: z.unknown() });
