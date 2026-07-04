import { google } from 'googleapis';

// `google.auth.OAuth2` (rather than importing the `google-auth-library` package directly) —
// `googleapis` bundles its own copy of that library, and mixing a top-level install of it in
// leads to two structurally-identical-but-nominally-different `OAuth2Client` classes that
// TypeScript refuses to unify (private fields make classes nominal, not structural).
export type OAuth2Client = InstanceType<typeof google.auth.OAuth2>;

export type GmailHeader = { name: string; value: string };

export type GmailMessagePart = {
  mimeType?: string;
  body?: { data?: string | null };
  parts?: GmailMessagePart[];
};

export type GmailMessage = {
  id: string;
  threadId: string;
  labelIds?: string[];
  payload?: { headers?: GmailHeader[]; body?: { data?: string | null }; parts?: GmailMessagePart[] };
  internalDate?: string;
};

export type GmailHistoryRecord = {
  id: string;
  messagesAdded?: Array<{ message: { id: string; threadId: string; labelIds?: string[] } }>;
};

/**
 * The thin slice of the Gmail API this CRM needs. Kept as its own interface (rather than
 * depending on the full `googleapis` SDK shape directly) so tests can supply an in-memory
 * fake instead of mocking HTTP calls into a generated client.
 */
export interface GmailApiClient {
  getProfile(): Promise<{ historyId: string }>;
  listHistory(params: { startHistoryId: string }): Promise<{ history: GmailHistoryRecord[]; historyId: string }>;
  getMessage(id: string): Promise<GmailMessage>;
  sendRaw(params: { raw: string; threadId?: string | null }): Promise<{ id: string; threadId: string }>;
}

export function createGoogleGmailClient(auth: OAuth2Client): GmailApiClient {
  const gmail = google.gmail({ version: 'v1', auth });

  return {
    async getProfile() {
      const res = await gmail.users.getProfile({ userId: 'me' });
      return { historyId: String(res.data.historyId) };
    },

    async listHistory({ startHistoryId }) {
      const res = await gmail.users.history.list({ userId: 'me', startHistoryId, historyTypes: ['messageAdded'] });
      return {
        history: (res.data.history ?? []) as GmailHistoryRecord[],
        historyId: String(res.data.historyId ?? startHistoryId)
      };
    },

    async getMessage(id) {
      const res = await gmail.users.messages.get({ userId: 'me', id, format: 'full' });
      return res.data as GmailMessage;
    },

    async sendRaw({ raw, threadId }) {
      const res = await gmail.users.messages.send({ userId: 'me', requestBody: { raw, threadId: threadId ?? undefined } });
      return { id: String(res.data.id), threadId: String(res.data.threadId) };
    }
  };
}

export function getHeader(message: GmailMessage, name: string): string | null {
  const header = message.payload?.headers?.find((h) => h.name.toLowerCase() === name.toLowerCase());
  return header?.value ?? null;
}

function decodeBase64Url(data: string): string {
  return Buffer.from(data, 'base64url').toString('utf8');
}

function findPart(parts: GmailMessagePart[] | undefined, mimeType: string): GmailMessagePart | undefined {
  if (!parts) return undefined;
  for (const part of parts) {
    if (part.mimeType === mimeType && part.body?.data) return part;
    const nested = findPart(part.parts, mimeType);
    if (nested) return nested;
  }
  return undefined;
}

/** Extracts a plain-text body from a Gmail message, preferring text/plain over text/html. */
export function extractPlainTextBody(message: GmailMessage): string {
  const payload = message.payload;
  if (!payload) return '';
  if (payload.body?.data) return decodeBase64Url(payload.body.data);

  const plain = findPart(payload.parts, 'text/plain');
  if (plain?.body?.data) return decodeBase64Url(plain.body.data);

  const html = findPart(payload.parts, 'text/html');
  if (html?.body?.data) return decodeBase64Url(html.body.data).replace(/<[^>]+>/g, '');

  return '';
}
