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
  can_spam_footer_enabled: true
} as const;

export type SettingKey = keyof typeof DEFAULT_SETTINGS;
