import { and, desc, eq } from 'drizzle-orm';
import * as schema from '../db/schema.js';
import type { CrmDb } from '../db/client.js';
import { getSettings } from '../settings/store.js';
import { isWithinQuietHoursWindow, nextQuietHoursStart, type QuietHoursWindow } from './quiet-hours.js';

export type SendGateChannel = 'imessage' | 'email';

export type SendGateParams = {
  contactId: number;
  channel: SendGateChannel;
  isReply?: boolean;
  /** Non-1:1 bulk/nurture email send (§6.2/§12) — gets its own pacing + daily cap on top of the usual checks. */
  isCampaign?: boolean;
  now?: Date;
};

export type SendGateDenialReason =
  | 'global_pause' | 'suppressed' | 'no_consent' | 'quiet_hours'
  | 'per_lead_cap' | 'global_cap' | 'channel_unhealthy' | 'imessage_pacing'
  | 'email_campaign_pacing' | 'email_campaign_daily_cap';

export type SendGateResult =
  | { allowed: true }
  | { allowed: false; reason: SendGateDenialReason; retryAt?: string };

function isSameUtcDay(a: Date, b: Date) {
  return a.getUTCFullYear() === b.getUTCFullYear() && a.getUTCMonth() === b.getUTCMonth() && a.getUTCDate() === b.getUTCDate();
}

function countOutboundToday(db: CrmDb, now: Date, contactId?: number) {
  const rows = contactId
    ? db.select().from(schema.messages).where(and(eq(schema.messages.contactId, contactId), eq(schema.messages.direction, 'out'))).all()
    : db.select().from(schema.messages).where(eq(schema.messages.direction, 'out')).all();
  return rows.filter((row) => row.status !== 'failed' && isSameUtcDay(new Date(row.createdAt), now)).length;
}

export function evaluateSendGate(db: CrmDb, params: SendGateParams): SendGateResult {
  const now = params.now ?? new Date();
  const settings = getSettings(db);

  if (settings.global_pause) return { allowed: false, reason: 'global_pause' };

  const contact = db.select().from(schema.contacts).where(eq(schema.contacts.id, params.contactId)).get();
  if (!contact) throw new Error(`Contact ${params.contactId} not found`);

  if (contact.doNotContact) return { allowed: false, reason: 'suppressed' };

  const suppressedContact = db.select().from(schema.suppressions)
    .where(and(eq(schema.suppressions.kind, 'contact'), eq(schema.suppressions.value, String(contact.id)))).get();
  if (suppressedContact) return { allowed: false, reason: 'suppressed' };

  if (params.channel === 'imessage') {
    for (const phone of contact.phones) {
      if (db.select().from(schema.suppressions).where(and(eq(schema.suppressions.kind, 'phone'), eq(schema.suppressions.value, phone))).get()) {
        return { allowed: false, reason: 'suppressed' };
      }
    }
    if (!contact.consentSms) return { allowed: false, reason: 'no_consent' };
  } else {
    for (const email of contact.emails) {
      if (db.select().from(schema.suppressions).where(and(eq(schema.suppressions.kind, 'email'), eq(schema.suppressions.value, email))).get()) {
        return { allowed: false, reason: 'suppressed' };
      }
    }
    if (!contact.consentEmail) return { allowed: false, reason: 'no_consent' };
  }

  const quietHours = settings.quiet_hours as QuietHoursWindow;
  if (!isWithinQuietHoursWindow(quietHours, now)) {
    return { allowed: false, reason: 'quiet_hours', retryAt: nextQuietHoursStart(quietHours, now).toISOString() };
  }

  if (!params.isReply) {
    const perLeadCount = countOutboundToday(db, now, contact.id);
    if (perLeadCount >= (settings.per_lead_daily_cap as number)) {
      return { allowed: false, reason: 'per_lead_cap', retryAt: nextQuietHoursStart(quietHours, now).toISOString() };
    }
  }

  const globalCount = countOutboundToday(db, now);
  if (globalCount >= (settings.global_daily_cap as number)) {
    return { allowed: false, reason: 'global_cap', retryAt: nextQuietHoursStart(quietHours, now).toISOString() };
  }

  if (params.channel === 'imessage') {
    const health = settings.imessage_health as { ok: boolean } | undefined;
    if (health && health.ok === false) {
      return { allowed: false, reason: 'channel_unhealthy', retryAt: new Date(now.getTime() + 5 * 60_000).toISOString() };
    }

    const lastImessageOut = db.select().from(schema.messages)
      .where(and(eq(schema.messages.channel, 'imessage'), eq(schema.messages.direction, 'out')))
      .orderBy(desc(schema.messages.id)).get();
    if (lastImessageOut) {
      const lastSentAt = new Date(lastImessageOut.sentAt ?? lastImessageOut.createdAt);
      const minSeconds = settings.imessage_min_seconds_between_sends as number;
      const elapsedMs = now.getTime() - lastSentAt.getTime();
      if (elapsedMs < minSeconds * 1000) {
        return { allowed: false, reason: 'imessage_pacing', retryAt: new Date(lastSentAt.getTime() + minSeconds * 1000).toISOString() };
      }
    }
  }

  if (params.channel === 'email' && params.isCampaign) {
    const campaignState = settings.email_campaign_state as { lastSentAt: string | null; countByDate: Record<string, number> };
    const todayKey = now.toISOString().slice(0, 10);
    const sentToday = campaignState.countByDate[todayKey] ?? 0;
    const dailyCap = settings.email_campaign_daily_cap as number;
    if (sentToday >= dailyCap) {
      return { allowed: false, reason: 'email_campaign_daily_cap', retryAt: nextQuietHoursStart(quietHours, now).toISOString() };
    }

    if (campaignState.lastSentAt) {
      const minSeconds = settings.email_campaign_min_seconds_between_sends as number;
      const elapsedMs = now.getTime() - new Date(campaignState.lastSentAt).getTime();
      if (elapsedMs < minSeconds * 1000) {
        return { allowed: false, reason: 'email_campaign_pacing', retryAt: new Date(new Date(campaignState.lastSentAt).getTime() + minSeconds * 1000).toISOString() };
      }
    }
  }

  return { allowed: true };
}
