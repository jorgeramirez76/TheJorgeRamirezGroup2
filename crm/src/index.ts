import { config } from 'dotenv';
import { google } from 'googleapis';
import { buildApp } from './app.js';
import { openDb } from './db/client.js';
import { applyMigrations } from './db/migrate.js';
import { seedCoreData } from './db/seed.js';
import { BlueBubblesChannel } from './channels/bluebubbles.js';
import { startBlueBubblesHealthCheck } from './channels/health.js';
import { createGoogleGmailClient } from './channels/gmail-client.js';
import { startGmailPolling } from './channels/gmail-poller.js';

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

let stopGmailPolling: (() => void) | undefined;
if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET && process.env.GMAIL_REFRESH_TOKEN) {
  const oauth2Client = new google.auth.OAuth2(process.env.GOOGLE_CLIENT_ID, process.env.GOOGLE_CLIENT_SECRET, process.env.GOOGLE_REDIRECT_URI);
  oauth2Client.setCredentials({ refresh_token: process.env.GMAIL_REFRESH_TOKEN });
  const gmailClient = createGoogleGmailClient(oauth2Client);
  stopGmailPolling = startGmailPolling(db, gmailClient);
} else {
  app.log.warn('GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET/GMAIL_REFRESH_TOKEN not set — run `npm run setup:gmail`; Gmail sending and polling are disabled until then');
}

const signals: NodeJS.Signals[] = ['SIGINT', 'SIGTERM'];
for (const signal of signals) {
  process.on(signal, async () => {
    stopHealthCheck?.();
    stopGmailPolling?.();
    await app.close();
    sqlite.close();
    process.exit(0);
  });
}

await app.listen({ host, port });
