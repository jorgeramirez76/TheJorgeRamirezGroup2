import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { buildApp } from '../src/app.js';
import { applyMigrations } from '../src/db/migrate.js';
import { seedCoreData } from '../src/db/seed.js';
import * as schema from '../src/db/schema.js';

export type TestContext = ReturnType<typeof createTestContext>;

export function createTestContext() {
  const sqlite = new Database(':memory:');
  applyMigrations(sqlite);
  const db = drizzle(sqlite, { schema });
  seedCoreData(db);
  const app = buildApp({ db, logger: false });
  return { sqlite, db, app };
}
