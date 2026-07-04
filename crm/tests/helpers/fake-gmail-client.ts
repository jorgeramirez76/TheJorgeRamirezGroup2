import type { GmailApiClient, GmailHistoryRecord, GmailMessage } from '../../src/channels/gmail-client.js';

export type FakeInboundMessageInput = {
  id: string;
  threadId: string;
  from: string;
  to?: string;
  subject?: string;
  body: string;
  messageIdHeader?: string;
  labelIds?: string[];
};

export type FakeSentMessage = { id: string; threadId: string; headers: Record<string, string>; body: string };

/**
 * An in-memory stand-in for the Gmail API, implementing just the slice this CRM calls
 * (`GmailApiClient`). Used instead of mocking HTTP calls into the generated `googleapis`
 * client, which would mean asserting against that SDK's internals rather than our own code.
 */
export class FakeGmailClient implements GmailApiClient {
  private historyId = 1000;
  private history: GmailHistoryRecord[] = [];
  private messages = new Map<string, GmailMessage>();
  private sendCounter = 0;
  private nextHistoryCallFails = false;
  public sent: FakeSentMessage[] = [];

  /** Registers a new inbound message and advances the history cursor past it. */
  addInboundMessage(input: FakeInboundMessageInput): string {
    this.historyId += 1;
    const messageIdHeader = input.messageIdHeader ?? `<${input.id}@mail.gmail.com>`;
    const labelIds = input.labelIds ?? ['INBOX'];
    const message: GmailMessage = {
      id: input.id,
      threadId: input.threadId,
      labelIds,
      payload: {
        headers: [
          { name: 'From', value: input.from },
          { name: 'To', value: input.to ?? 'jorgeramirez76@gmail.com' },
          { name: 'Subject', value: input.subject ?? '' },
          { name: 'Message-ID', value: messageIdHeader }
        ],
        body: { data: Buffer.from(input.body, 'utf8').toString('base64url') }
      }
    };
    this.messages.set(input.id, message);
    this.history.push({
      id: String(this.historyId),
      messagesAdded: [{ message: { id: input.id, threadId: input.threadId, labelIds } }]
    });
    return String(this.historyId);
  }

  /** Makes the next `listHistory` call reject, simulating a `startHistoryId` too old for Gmail to diff. */
  simulateHistoryGap() {
    this.nextHistoryCallFails = true;
  }

  currentHistoryId(): string {
    return String(this.historyId);
  }

  async getProfile() {
    return { historyId: String(this.historyId) };
  }

  async listHistory({ startHistoryId }: { startHistoryId: string }) {
    if (this.nextHistoryCallFails) {
      this.nextHistoryCallFails = false;
      throw new Error('startHistoryId too old');
    }
    const start = Number(startHistoryId);
    return { history: this.history.filter((r) => Number(r.id) > start), historyId: String(this.historyId) };
  }

  async getMessage(id: string) {
    const message = this.messages.get(id);
    if (!message) throw new Error(`FakeGmailClient: no message ${id}`);
    return message;
  }

  async sendRaw({ raw, threadId }: { raw: string; threadId?: string | null }) {
    this.sendCounter += 1;
    const id = `sent-${this.sendCounter}`;
    const resolvedThreadId = threadId ?? `thread-${id}`;

    const decoded = Buffer.from(raw, 'base64url').toString('utf8');
    const [headerBlock, ...bodyParts] = decoded.split('\r\n\r\n');
    const headers: Record<string, string> = {};
    for (const line of headerBlock.split('\r\n')) {
      const idx = line.indexOf(': ');
      if (idx > -1) headers[line.slice(0, idx)] = line.slice(idx + 2);
    }

    this.sent.push({ id, threadId: resolvedThreadId, headers, body: bodyParts.join('\r\n\r\n') });
    return { id, threadId: resolvedThreadId };
  }
}
