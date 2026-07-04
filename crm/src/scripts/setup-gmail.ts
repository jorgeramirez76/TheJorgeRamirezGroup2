import { createServer } from 'node:http';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';
import { google } from 'googleapis';
import { parseAuthCallback, parseRedirectUri } from './oauth-callback.js';
import { upsertEnvVar } from './env-file.js';

const here = dirname(fileURLToPath(import.meta.url));
const envPath = join(here, '..', '..', '.env');

const SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send'];

function loadEnvText(): string {
  return existsSync(envPath) ? readFileSync(envPath, 'utf8') : '';
}

async function waitForAuthCode(port: number, path: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const server = createServer((req, res) => {
      if (!req.url) return;
      const outcome = parseAuthCallback(req.url, `http://localhost:${port}`);
      const url = new URL(req.url, `http://localhost:${port}`);
      if (url.pathname !== path) {
        res.writeHead(404).end();
        return;
      }

      if ('error' in outcome) {
        res.writeHead(400, { 'content-type': 'text/plain' }).end(`Authorization failed: ${outcome.error}`);
        server.close();
        reject(new Error(`Google OAuth authorization failed: ${outcome.error}`));
        return;
      }

      res.writeHead(200, { 'content-type': 'text/plain' }).end('Gmail connected. You can close this tab and return to the terminal.');
      server.close();
      resolve(outcome.code);
    });
    server.listen(port);
  });
}

async function main() {
  config({ path: envPath });

  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = process.env.GOOGLE_REDIRECT_URI ?? 'http://localhost:4820/oauth/google/callback';

  if (!clientId || !clientSecret) {
    console.error(
      'Missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET in crm/.env.\n' +
      'See crm/SETUP.md → "Gmail (Phase 3)" for how to create OAuth credentials in Google Cloud Console.'
    );
    process.exitCode = 1;
    return;
  }

  const { port, path } = parseRedirectUri(redirectUri);
  const oauth2Client = new google.auth.OAuth2(clientId, clientSecret, redirectUri);

  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    prompt: 'consent', // forces a refresh_token every run, even on a Google account that already granted access once
    scope: SCOPES
  });

  console.log('\nOpen this URL in a browser signed into Jorge\'s Gmail account:\n');
  console.log(authUrl);
  console.log(`\nWaiting for the redirect on ${redirectUri} ...`);

  const code = await waitForAuthCode(port, path);
  const { tokens } = await oauth2Client.getToken(code);

  if (!tokens.refresh_token) {
    console.error(
      '\nGoogle did not return a refresh_token. This happens if this account already granted access\n' +
      'and Google is reusing a prior consent. Revoke prior access at https://myaccount.google.com/permissions\n' +
      'for this app, then re-run `npm run setup:gmail`.'
    );
    process.exitCode = 1;
    return;
  }

  oauth2Client.setCredentials(tokens);
  const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
  const profile = await gmail.users.getProfile({ userId: 'me' });

  let envText = loadEnvText();
  envText = upsertEnvVar(envText, 'GMAIL_REFRESH_TOKEN', tokens.refresh_token);
  envText = upsertEnvVar(envText, 'GMAIL_FROM', profile.data.emailAddress ?? process.env.GMAIL_FROM ?? '');
  // Debug/reference only — the CRM server tracks its live poll cursor in settings.gmail_history_id,
  // not this file, so it survives restarts without needing `.env` rewritten (see DECISIONS.md).
  envText = upsertEnvVar(envText, 'GMAIL_HISTORY_ID', String(profile.data.historyId ?? ''));
  writeFileSync(envPath, envText);

  console.log(`\nGmail connected as ${profile.data.emailAddress}.`);
  console.log('Saved GMAIL_REFRESH_TOKEN (and GMAIL_FROM) to crm/.env.');
  console.log('Restart the CRM server (or run `npm run dev`) to start sending/polling.\n');
}

main().catch((err) => {
  console.error('\nGmail setup failed:', err instanceof Error ? err.message : err);
  process.exitCode = 1;
});
