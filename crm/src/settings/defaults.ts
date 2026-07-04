export const DEFAULT_SETTINGS = {
  quiet_hours: { timezone: 'America/New_York', start: '08:30', end: '20:30' },
  per_lead_daily_cap: 2,
  global_daily_cap: 100,
  imessage_min_seconds_between_sends: 45,
  global_pause: false,
  autonomy_default: 'approval',
  sms_consent_required: true,
  email_consent_required: true,
  cold_texting_scraped_lists_enabled: false,
  stop_regex: "(?i)\\b(stop|unsubscribe|stop texting|do not text|don't text)\\b",
  can_spam_footer_enabled: true,
  // Phase 3: Gmail channel
  email_campaign_daily_cap: 100,
  email_campaign_min_seconds_between_sends: 20,
  email_campaign_state: { lastSentAt: null, countByDate: {} },
  // gmail_history_id is intentionally not seeded here (drizzle's json-mode column rejects a bare
  // top-level `null` — NOT NULL constraint — see DECISIONS.md). The poller creates it lazily via
  // upsertSetting on its very first run; until then `settings.gmail_history_id` is `undefined`,
  // which the poller's `if (!cursor)` check treats the same as null.
  // TODO(jorge-verify): fill in via the dashboard/API before any real campaign send goes out —
  // CAN-SPAM requires a physical mailing address in the footer.
  business_name: 'The Jorge Ramirez Group',
  business_mailing_address: ''
} as const;

export type SettingKey = keyof typeof DEFAULT_SETTINGS;
