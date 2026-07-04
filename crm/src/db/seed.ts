import { eq } from 'drizzle-orm';
import { openDb } from './client.js';
import * as schema from './schema.js';
import { DEFAULT_SETTINGS } from '../settings/defaults.js';
import type { CrmDb } from './client.js';

export const BUYER_STAGES = [
  'New', 'Attempting Contact', 'Engaged (AI)', 'Hot / Hand-Raiser', 'Appointment Set',
  'Active Client', 'Under Contract', 'Closed', 'Long-Term Nurture'
] as const;

export const SELLER_STAGES = [
  'New', 'Attempting Contact', 'Engaged (AI)', 'Valuation Delivered', 'Hot / Hand-Raiser',
  'Listing Appt', 'Listed', 'Under Contract', 'Closed', 'Long-Term Nurture'
] as const;

function upsertSetting(db: CrmDb, key: string, value: unknown) {
  db.insert(schema.settings).values({ key, value }).onConflictDoUpdate({
    target: schema.settings.key,
    set: { value }
  }).run();
}

function ensurePipeline(db: CrmDb, name: 'Buyer' | 'Seller', stageNames: readonly string[]) {
  db.insert(schema.pipelines).values({ name }).onConflictDoNothing().run();
  const pipeline = db.select().from(schema.pipelines).where(eq(schema.pipelines.name, name)).get();
  if (!pipeline) throw new Error(`Could not seed pipeline ${name}`);
  stageNames.forEach((stageName, index) => {
    db.insert(schema.stages).values({ pipelineId: pipeline.id, name: stageName, position: index + 1 }).onConflictDoNothing().run();
  });
  return pipeline;
}

export function seedCoreData(db: CrmDb) {
  for (const [key, value] of Object.entries(DEFAULT_SETTINGS)) upsertSetting(db, key, value);

  const buyer = ensurePipeline(db, 'Buyer', BUYER_STAGES);
  const seller = ensurePipeline(db, 'Seller', SELLER_STAGES);

  db.insert(schema.tags).values([{ name: 'website-lead' }, { name: 'valuation-lead' }, { name: 'needs-review' }]).onConflictDoNothing().run();

  const existing = db.select().from(schema.contacts).all();
  if (existing.length > 0) return;

  const contacts = db.insert(schema.contacts).values([
    {
      firstName: 'Maria', lastName: 'Santos', phones: ['+15555550101'], emails: ['maria@example.com'],
      town: 'Summit', county: 'Union', source: 'website', sourceDetail: '/home-valuation',
      utm: { source: 'google', campaign: 'seller' }, consentSms: true, consentEmail: true,
      consentSource: 'website_form', consentAt: new Date().toISOString(), preferredChannel: 'imessage'
    },
    {
      firstName: 'David', lastName: 'Lee', phones: ['+15555550102'], emails: ['david@example.com'],
      town: 'Westfield', county: 'Union', source: 'manual_import', sourceDetail: 'open house',
      consentSms: true, consentEmail: true, consentSource: 'existing_relationship', consentAt: new Date().toISOString()
    },
    {
      firstName: 'Ana', lastName: 'Rivera', phones: ['+15555550103'], emails: ['ana@example.com'],
      town: 'Cranford', county: 'Union', source: 'website', sourceDetail: '/towns/cranford',
      consentSms: false, consentEmail: true, consentSource: 'website_form', consentAt: new Date().toISOString(), preferredChannel: 'email'
    }
  ]).returning().all();

  const buyerNew = db.select().from(schema.stages).where(eq(schema.stages.pipelineId, buyer.id)).get();
  const sellerNew = db.select().from(schema.stages).where(eq(schema.stages.pipelineId, seller.id)).get();
  if (!buyerNew || !sellerNew) throw new Error('Missing seeded stages');

  const sellerLead = db.insert(schema.leads).values({
    contactId: contacts[0].id, pipelineId: seller.id, stageId: sellerNew.id, intent: 'sell', score: 68,
    scoreBreakdown: { source: 20, valuation_view: 25, fit: 23 }, temperature: 'WARM', stageEnteredAt: new Date().toISOString()
  }).returning().get();
  db.insert(schema.leads).values({
    contactId: contacts[1].id, pipelineId: buyer.id, stageId: buyerNew.id, intent: 'buy', score: 42,
    scoreBreakdown: { source: 15, engagement: 12, fit: 15 }, temperature: 'WARM', stageEnteredAt: new Date().toISOString()
  }).run();

  db.insert(schema.customFields).values([
    { contactId: contacts[0].id, key: 'timeline', value: '3-6 months' },
    { contactId: contacts[0].id, key: 'property_type', value: 'single-family' },
    { contactId: contacts[1].id, key: 'budget', value: '$850k' }
  ]).run();

  db.insert(schema.messages).values([
    { contactId: contacts[0].id, channel: 'imessage', direction: 'in', body: 'I am curious what my Summit home could sell for.', externalId: 'seed-imsg-1', threadKey: 'seed-thread-1', status: 'received' },
    { contactId: contacts[0].id, channel: 'imessage', direction: 'out', body: 'Happy to help — want the full valuation range or just a quick ballpark?', externalId: 'seed-imsg-2', threadKey: 'seed-thread-1', status: 'sent', generatedBy: 'ai', modelUsed: 'claude-sonnet-5', tokensIn: 800, tokensOut: 42, sentAt: new Date().toISOString() },
    { contactId: contacts[1].id, channel: 'email', direction: 'out', subject: 'Westfield homes', body: 'I pulled together a few Westfield market notes for you.', externalId: 'seed-email-1', threadKey: 'seed-gmail-thread-1', status: 'sent', generatedBy: 'human', sentAt: new Date().toISOString() }
  ]).run();

  db.insert(schema.scheduledActions).values({ leadId: sellerLead.id, kind: 'send_message', payload: { channel: 'auto', goal: 'seller speed-to-lead follow-up' }, runAt: new Date().toISOString(), status: 'queued' }).run();
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const { sqlite, db } = openDb();
  seedCoreData(db);
  sqlite.close();
  console.log('Seeded CRM pipelines, settings, and fake inbox data');
}
