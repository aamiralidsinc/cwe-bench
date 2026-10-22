import { afterEach, describe, expect, it } from '@rstest/core';
import {
  closeWs,
  connectWs,
  disposeSdk,
  startSdk,
  tokenOf,
  wsUrlFor,
  type Started,
} from '../support/helpers';

describe('the realtime channel requires the per-server credential', () => {
  let first: Started | undefined;
  let second: Started | undefined;

  afterEach(async () => {
    if (first) {
      await disposeSdk(first.sdk);
      first = undefined;
    }
    if (second) {
      await disposeSdk(second.sdk);
      second = undefined;
    }
  });

  it('refuses a handshake without a credential', async () => {
    first = await startSdk();
    const outcome = await connectWs(wsUrlFor(first.port));
    if (outcome.ws) {
      closeWs(outcome.ws);
    }

    expect(outcome.opened).toBe(false);
  });

  it('refuses a handshake with a wrong credential', async () => {
    first = await startSdk();
    const outcome = await connectWs(wsUrlFor(first.port, '?token=not-it'));
    if (outcome.ws) {
      closeWs(outcome.ws);
    }

    expect(outcome.opened).toBe(false);
  });

  it("refuses another server's credential", async () => {
    first = await startSdk();
    second = await startSdk();
    const foreignToken = tokenOf(first.sdk.server.socketUrl.socketUrl);
    const outcome = await connectWs(
      wsUrlFor(second.port, `?token=${encodeURIComponent(foreignToken)}`),
    );
    if (outcome.ws) {
      closeWs(outcome.ws);
    }

    expect(outcome.opened).toBe(false);
  });
});
