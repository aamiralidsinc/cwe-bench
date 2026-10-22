import { afterEach, describe, expect, it } from '@rstest/core';
import {
  closeWs,
  connectWs,
  disposeSdk,
  readWsMessage,
  startSdk,
  type Started,
} from '../support/helpers';

describe('the first-party realtime client keeps working', () => {
  let started: Started | undefined;

  afterEach(async () => {
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  it('connects with the endpoint value the server publishes', async () => {
    started = await startSdk();
    const endpoint: string = started.sdk.server.socketUrl.socketUrl;
    const outcome = await connectWs(endpoint);

    expect(outcome.opened).toBe(true);
    if (outcome.ws) {
      closeWs(outcome.ws);
    }
  });

  it('answers data requests over the published endpoint', async () => {
    started = await startSdk();
    started.sdk.addClientRoutes(['Overall']);
    const endpoint: string = started.sdk.server.socketUrl.socketUrl;
    const outcome = await connectWs(endpoint);
    expect(outcome.opened).toBe(true);
    if (!outcome.ws) {
      return;
    }

    try {
      const message = readWsMessage(outcome.ws);
      outcome.ws.send(
        JSON.stringify({
          type: 'request',
          id: 'req-1',
          api: '/api/routes',
          body: {},
        }),
      );
      const reply = await message;
      expect(reply.type).toBe('response');
      expect(Array.isArray(reply.payload)).toBe(true);
      expect(reply.payload).toContain('Overall');
    } finally {
      closeWs(outcome.ws);
    }
  });
});
