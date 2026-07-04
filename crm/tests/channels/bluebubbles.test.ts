import { rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { AddressInfo } from 'node:net';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { BlueBubblesChannel } from '../../src/channels/bluebubbles.js';
import { createMockBlueBubblesServer, type MockBlueBubblesState } from '../helpers/mock-bluebubbles-server.js';

describe('BlueBubblesChannel against a mock BlueBubbles server', () => {
  let mockApp: Awaited<ReturnType<typeof createMockBlueBubblesServer>>['app'];
  let state: MockBlueBubblesState;
  let baseUrl: string;

  beforeEach(async () => {
    const mock = createMockBlueBubblesServer('test-pass');
    mockApp = mock.app;
    state = mock.state;
    await mockApp.listen({ port: 0, host: '127.0.0.1' });
    const address = mockApp.server.address() as AddressInfo;
    baseUrl = `http://127.0.0.1:${address.port}`;
  });

  afterEach(async () => {
    await mockApp.close();
  });

  it('reports health via ping and flips when the server goes down', async () => {
    const channel = new BlueBubblesChannel({ baseUrl, password: 'test-pass' });
    expect(await channel.ping()).toBe(true);
    state.pingOk = false;
    expect(await channel.ping()).toBe(false);
  });

  it('creates a chat from an address then sends text through it', async () => {
    const channel = new BlueBubblesChannel({ baseUrl, password: 'test-pass' });
    const result = await channel.send({ contactId: 1, channel: 'imessage', body: 'hi there', address: '+15555550101' });
    expect(result.chatGuid).toMatch(/^chat-/);
    expect(result.externalId).toMatch(/^msg-/);
    expect(state.createdChats).toEqual([{ addresses: ['+15555550101'] }]);
    expect(state.sentTexts).toEqual([{ chatGuid: result.chatGuid, message: 'hi there' }]);
  });

  it('reuses an existing chatGuid instead of creating a new chat', async () => {
    const channel = new BlueBubblesChannel({ baseUrl, password: 'test-pass' });
    await channel.send({ contactId: 1, channel: 'imessage', body: 'hi again', chatGuid: 'chat-existing' });
    expect(state.createdChats).toHaveLength(0);
    expect(state.sentTexts).toEqual([{ chatGuid: 'chat-existing', message: 'hi again' }]);
  });

  it('sends an attachment (e.g. a lead video) through the attachment endpoint', async () => {
    const filePath = join(tmpdir(), `bb-attachment-${Date.now()}.txt`);
    await writeFile(filePath, 'fake video bytes for the test');
    try {
      const channel = new BlueBubblesChannel({ baseUrl, password: 'test-pass' });
      const result = await channel.send({
        contactId: 1, channel: 'imessage', body: '', chatGuid: 'chat-existing',
        attachmentPath: filePath, attachmentName: 'clip.mp4'
      });
      expect(result.externalId).toMatch(/^att-/);
      expect(state.attachments).toHaveLength(1);
      expect(state.attachments[0].size).toBeGreaterThan(0);
    } finally {
      await rm(filePath);
    }
  });

  it('throws when the password is wrong instead of silently failing', async () => {
    const channel = new BlueBubblesChannel({ baseUrl, password: 'wrong-password' });
    await expect(channel.send({ contactId: 1, channel: 'imessage', body: 'x', chatGuid: 'chat-existing' })).rejects.toThrow();
  });

  it('throws when send is given neither chatGuid nor address', async () => {
    const channel = new BlueBubblesChannel({ baseUrl, password: 'test-pass' });
    await expect(channel.send({ contactId: 1, channel: 'imessage', body: 'x' })).rejects.toThrow(/chatGuid or address/);
  });
});
