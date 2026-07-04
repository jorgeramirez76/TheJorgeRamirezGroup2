import { config } from 'dotenv';
import { buildApp } from './app.js';
import { openDb } from './db/client.js';
import { applyMigrations } from './db/migrate.js';
import { seedCoreData } from './db/seed.js';

config();

const host = process.env.CRM_HOST ?? '127.0.0.1';
const port = Number(process.env.CRM_PORT ?? 4820);

const { sqlite, db } = openDb();
applyMigrations(sqlite);
seedCoreData(db);

const app = buildApp({ db });

const signals: NodeJS.Signals[] = ['SIGINT', 'SIGTERM'];
for (const signal of signals) {
  process.on(signal, async () => {
    await app.close();
    sqlite.close();
    process.exit(0);
  });
}

await app.listen({ host, port });
