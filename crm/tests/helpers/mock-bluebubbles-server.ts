import Fastify from 'fastify';

export type MockBlueBubblesState = {
  pingOk: boolean;
  createdChats: Array<{ addresses: string[] }>;
  sentTexts: Array<{ chatGuid: string; message: string }>;
  attachments: Array<{ size: number }>;
};

/** A minimal stand-in for a real BlueBubbles server, used to test BlueBubblesChannel over real HTTP. */
export function createMockBlueBubblesServer(password: string) {
  const state: MockBlueBubblesState = { pingOk: true, createdChats: [], sentTexts: [], attachments: [] };
  const app = Fastify();

  app.addContentTypeParser('multipart/form-data', { parseAs: 'buffer' }, (_req, body, done) => done(null, body));

  app.addHook('onRequest', async (request, reply) => {
    const url = new URL(request.url, 'http://127.0.0.1');
    if (url.searchParams.get('password') !== password) {
      return reply.code(401).send({ status: 401, message: 'Invalid password' });
    }
  });

  app.get('/api/v1/ping', async (_request, reply) => {
    if (!state.pingOk) return reply.code(503).send({ status: 503, message: 'Server down' });
    return { status: 200, message: 'Success', data: 'pong' };
  });

  app.post('/api/v1/chat/new', async (request) => {
    const body = request.body as { addresses: string[] };
    state.createdChats.push({ addresses: body.addresses });
    return { status: 200, message: 'Success', data: { guid: `chat-${state.createdChats.length}` } };
  });

  app.post('/api/v1/message/text', async (request) => {
    const body = request.body as { chatGuid: string; message: string };
    state.sentTexts.push({ chatGuid: body.chatGuid, message: body.message });
    return { status: 200, message: 'Success', data: { guid: `msg-${state.sentTexts.length}` } };
  });

  app.post('/api/v1/message/attachment', async (request) => {
    const raw = request.body as Buffer;
    state.attachments.push({ size: raw.length });
    return { status: 200, message: 'Success', data: { guid: `att-${state.attachments.length}` } };
  });

  return { app, state };
}
