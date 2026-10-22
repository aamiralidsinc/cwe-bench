import { describe, expect, it } from '@rstest/core';
import { disposeSdk, freePort, startSdk, tryHttp } from '../support/helpers';

describe('a disabled client server starts no listener', () => {
  it('leaves nothing reachable on the requested port', async () => {
    const port = await freePort();
    const started = await startSdk({ noServer: true, port });
    try {
      const outcome = await tryHttp({ port: started.port, path: '/api/env' });
      expect(outcome.result).toBeUndefined();
      expect(outcome.error).toBeDefined();
    } finally {
      await disposeSdk(started.sdk);
    }
  });
});
