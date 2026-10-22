import { describe, expect, it } from '@rstest/core';
import { disposeSdk, freePort, startSdk } from '../support/helpers';

describe('the disabled client server stays usable', () => {
  it('bootstraps and disposes without a client server', async () => {
    const port = await freePort();
    const started = await startSdk({ noServer: true, port });

    try {
      expect(started.sdk.server.port).toBe(port);
      expect(typeof started.sdk.getManifestData()).toBe('object');
    } finally {
      await disposeSdk(started.sdk);
    }
  });
});
