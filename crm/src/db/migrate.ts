import Database from 'better-sqlite3';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { getDatabasePath } from './path.js';

const here = dirname(fileURLToPath(import.meta.url));
const migrationSql = readFileSync(join(here, 'migrations', '0001_initial.sql'), 'utf8');

export function applyMigrations(sqlite: Database.Database) {
  sqlite.pragma('foreign_keys = ON');
  sqlite.exec(migrationSql);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const sqlite = new Database(getDatabasePath());
  applyMigrations(sqlite);
  sqlite.close();
  console.log('Applied CRM migrations');
}
