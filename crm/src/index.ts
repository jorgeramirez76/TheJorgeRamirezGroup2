import { config } from 'dotenv';
import { buildApp } from './app.js';
import { openDb } from './db/client.js';
import { applyMigrations } from './db/migrate.js';
import { seedCoreData } from './db/seed.js';
import { BlueBubblesChannel } from './channels/bluebubbles.js';
import { startBlueBubblesHealthCheck } from './channels/health.js';

config();

const host = process.env.CRM_HOST ?? '127.0.0.1';
const port = Number(process.env.CRM_PORT ?? 4820);

const { sqlite, db } = openDb();
applyMigrations(sqlite);
seedCoreData(db);

const app = buildApp({ db });

let stopHealthCheck: (() => void) | undefined;
if (process.env.BLUEBUBBLES_BASE_URL && process.env.BLUEBUBBLES_PASSWORD) {
  const bluebubbles = new BlueBubblesChannel({
    baseUrl: process.env.BLUEBUBBLES_BASE_URL,
    password: process.env.BLUEBUBBLES_PASSWORD
  });
  stopHealthCheck = startBlueBubblesHealthCheck(db, bluebubbles);
} else {
  app.log.warn('BLUEBUBBLES_BASE_URL/BLUEBUBBLES_PASSWORD not set — iMessage sending and health checks are disabled');
}

const signals: NodeJS.Signals[] = ['SIGINT', 'SIGTERM'];
for (const signal of signals) {
  process.on(signal, async () => {
    stopHealthCheck?.();
    await app.close();
    sqlite.close();
    process.exit(0);
  });
}

await app.listen({ host, port });
