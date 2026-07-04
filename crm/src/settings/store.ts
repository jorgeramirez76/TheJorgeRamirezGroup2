import * as schema from '../db/schema.js';
import { DEFAULT_SETTINGS } from './defaults.js';
import type { CrmDb } from '../db/client.js';

export function getSettings(db: CrmDb): typeof DEFAULT_SETTINGS & Record<string, unknown> {
  const rows = db.select().from(schema.settings).all();
  const overrides = Object.fromEntries(rows.map((row) => [row.key, row.value]));
  return { ...DEFAULT_SETTINGS, ...overrides };
}

export function upsertSetting(db: CrmDb, key: string, value: unknown) {
  return db.insert(schema.settings).values({ key, value }).onConflictDoUpdate({
    target: schema.settings.key,
    set: { value }
  }).returning().get();
}
