import { readFile } from 'node:fs/promises';
import { basename } from 'node:path';
import type { Channel, OutboundMessage, SendResult } from './types.js';

export type BlueBubblesConfig = {
  baseUrl: string;
  password: string;
  fetchImpl?: typeof fetch;
};

type BlueBubblesEnvelope<T> = { status?: number; message?: string; data?: T };

export class BlueBubblesChannel implements Channel {
  private readonly baseUrl: string;
  private readonly password: string;
  private readonly fetchImpl: typeof fetch;

  constructor(config: BlueBubblesConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.password = config.password;
    this.fetchImpl = config.fetchImpl ?? fetch;
  }

  private url(path: string): string {
    const url = new URL(this.baseUrl + path);
    url.searchParams.set('password', this.password);
    return url.toString();
  }

  async ping(): Promise<boolean> {
    try {
      const res = await this.fetchImpl(this.url('/api/v1/ping'));
      return res.ok;
    } catch {
      return false;
    }
  }

  async createChat(addresses: string[]): Promise<{ chatGuid: string }> {
    const res = await this.fetchImpl(this.url('/api/v1/chat/new'), {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ addresses, service: 'iMessage' })
    });
    if (!res.ok) throw new Error(`BlueBubbles createChat failed: ${res.status}`);
    const json = (await res.json()) as BlueBubblesEnvelope<{ guid: string }>;
    const chatGuid = json.data?.guid;
    if (!chatGuid) throw new Error('BlueBubbles createChat response missing chat guid');
    return { chatGuid };
  }

  private async resolveChatGuid(msg: OutboundMessage): Promise<string> {
    if (msg.chatGuid) return msg.chatGuid;
    if (msg.address) return (await this.createChat([msg.address])).chatGuid;
    throw new Error('OutboundMessage requires chatGuid or address to resolve a BlueBubbles chat');
  }

  async send(msg: OutboundMessage): Promise<SendResult> {
    const chatGuid = await this.resolveChatGuid(msg);

    if (msg.attachmentPath) {
      const externalId = await this.sendAttachment({ chatGuid, filePath: msg.attachmentPath, name: msg.attachmentName ?? undefined });
      return { externalId, chatGuid };
    }

    const res = await this.fetchImpl(this.url('/api/v1/message/text'), {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chatGuid, message: msg.body, method: 'apple-script' })
    });
    if (!res.ok) throw new Error(`BlueBubbles send failed: ${res.status}`);
    const json = (await res.json()) as BlueBubblesEnvelope<{ guid: string }>;
    const externalId = json.data?.guid;
    if (!externalId) throw new Error('BlueBubbles send response missing message guid');
    return { externalId, chatGuid };
  }

  async sendAttachment(params: { chatGuid: string; filePath: string; name?: string }): Promise<string> {
    const bytes = await readFile(params.filePath);
    const name = params.name ?? basename(params.filePath);
    const form = new FormData();
    form.set('chatGuid', params.chatGuid);
    form.set('method', 'apple-script');
    form.set('name', name);
    form.set('attachment', new Blob([bytes]), name);

    const res = await this.fetchImpl(this.url('/api/v1/message/attachment'), { method: 'POST', body: form });
    if (!res.ok) throw new Error(`BlueBubbles sendAttachment failed: ${res.status}`);
    const json = (await res.json()) as BlueBubblesEnvelope<{ guid: string }>;
    const externalId = json.data?.guid;
    if (!externalId) throw new Error('BlueBubbles sendAttachment response missing message guid');
    return externalId;
  }
}
