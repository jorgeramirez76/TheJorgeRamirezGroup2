import type { EmailChannel, EmailSendResult, OutboundEmail } from './types.js';
import type { GmailApiClient } from './gmail-client.js';
import { buildRawMessage } from './gmail-mime.js';

export type GmailChannelConfig = { client: GmailApiClient; from: string };

export class GmailChannel implements EmailChannel {
  private readonly client: GmailApiClient;
  private readonly from: string;

  constructor(config: GmailChannelConfig) {
    this.client = config.client;
    this.from = config.from;
  }

  async send(msg: OutboundEmail): Promise<EmailSendResult> {
    const raw = buildRawMessage({
      from: this.from,
      to: msg.to,
      subject: msg.subject,
      body: msg.body,
      inReplyTo: msg.inReplyTo,
      references: msg.references,
      listUnsubscribe: msg.listUnsubscribe
    });

    const result = await this.client.sendRaw({ raw, threadId: msg.threadId });
    return { externalId: result.id, threadId: result.threadId };
  }
}
