import { describe, expect, it } from 'vitest';
import { GmailChannel } from '../../src/channels/gmail.js';
import { FakeGmailClient } from '../helpers/fake-gmail-client.js';

describe('GmailChannel.send', () => {
  it('sends a fresh (non-reply) email with no threadId', async () => {
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });

    const result = await channel.send({ contactId: 1, to: 'lead@example.com', subject: 'Westfield homes', body: 'Here are a few notes.' });

    expect(result.externalId).toBe('sent-1');
    expect(client.sent).toHaveLength(1);
    const sent = client.sent[0];
    expect(sent.headers.To).toBe('lead@example.com');
    expect(sent.headers.Subject).toBe('Westfield homes');
    expect(sent.headers.From).toBe('jorgeramirez76@gmail.com');
    expect(sent.body).toBe('Here are a few notes.');
    expect(sent.headers['In-Reply-To']).toBeUndefined();
    expect(sent.headers.References).toBeUndefined();
  });

  it('threads a reply with In-Reply-To, References, and the existing threadId', async () => {
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });

    const result = await channel.send({
      contactId: 1, to: 'lead@example.com', subject: 'Re: Westfield homes', body: 'Following up.',
      threadId: 'thread-abc', inReplyTo: '<parent-1@mail.gmail.com>', references: ['<parent-1@mail.gmail.com>']
    });

    expect(result.threadId).toBe('thread-abc');
    const sent = client.sent[0];
    expect(sent.headers['In-Reply-To']).toBe('<parent-1@mail.gmail.com>');
    expect(sent.headers.References).toBe('<parent-1@mail.gmail.com>');
  });

  it('adds a List-Unsubscribe header when the caller supplies one (campaign sends)', async () => {
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });

    await channel.send({
      contactId: 1, to: 'lead@example.com', subject: 'Market update', body: 'Body text\n\n--\nfooter',
      listUnsubscribe: '<mailto:jorgeramirez76@gmail.com?subject=unsubscribe>'
    });

    expect(client.sent[0].headers['List-Unsubscribe']).toBe('<mailto:jorgeramirez76@gmail.com?subject=unsubscribe>');
  });

  it('MIME-encodes a non-ASCII subject instead of sending raw bytes', async () => {
    const client = new FakeGmailClient();
    const channel = new GmailChannel({ client, from: 'jorgeramirez76@gmail.com' });

    await channel.send({ contactId: 1, to: 'lead@example.com', subject: 'Casa en Cranford — ¿interesado?', body: 'Hola' });

    expect(client.sent[0].headers.Subject).toMatch(/^=\?UTF-8\?B\?/);
  });
});
