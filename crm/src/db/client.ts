import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema.js';
import { getDatabasePath } from './path.js';

export function openSqlite(path = getDatabasePath()) {
  const sqlite = new Database(path);
  sqlite.pragma('foreign_keys = ON');
  sqlite.pragma('journal_mode = WAL');
  return sqlite;
}

export function openDb(path = getDatabasePath()) {
  const sqlite = openSqlite(path);
  return { sqlite, db: drizzle(sqlite, { schema }) };
}

export type CrmDb = ReturnType<typeof openDb>['db'];
