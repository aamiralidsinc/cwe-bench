import { afterEach, describe, expect, it } from '@rstest/core';
import { RsdoctorSDKController } from '/workspace/packages/sdk/dist/index.js';
import { Server } from '/workspace/packages/utils/dist/build.js';
import {
  disposeSdk,
  freePort,
  lanIPv4,
  startSdk,
  tryHttp,
  type Started,
} from '../support/helpers';

describe('report servers listen on loopback only', () => {
  let started: Started | undefined;
  let slave: any;

  afterEach(async () => {
    if (slave) {
      await disposeSdk(slave);
      slave = undefined;
    }
    if (started) {
      await disposeSdk(started.sdk);
      started = undefined;
    }
  });

  it('the report server is not reachable through the machine address', async () => {
    const lan = lanIPv4();
    started = await startSdk();
    const local = await tryHttp({ port: started.port, path: '/api/env' });
    expect(local.result?.status).toBe(200);

    if (lan) {
      const remote = await tryHttp({
        hostname: lan,
        port: started.port,
        path: '/api/env',
      });
      expect(remote.result).toBeUndefined();
      expect(remote.error).toBeDefined();
    }
  });

  it('the report server publishes a local address', async () => {
    started = await startSdk();
    const host = new URL(started.sdk.server.origin).hostname;
    expect(
      host === 'localhost' ||
        host === '127.0.0.1' ||
        host === '[::1]' ||
        host === '::1',
    ).toBe(true);
  });

  it('the public server helper binds a loopback address', async () => {
    const server = await Server.createServer(0);
    try {
      const address = server.server.address();
      expect(typeof address).toBe('object');
      const host = (address as { address: string }).address;
      expect(host === '127.0.0.1' || host === '::1').toBe(true);
    } finally {
      await server.close();
    }
  });

  it('a second report server for multi-compiler builds is loopback only', async () => {
    const controller = new RsdoctorSDKController('/workspace');
    const port = await freePort();
    slave = controller.createSlave({
      name: 'slave-a',
      type: 0,
      extraConfig: { server: { port } },
    });
    await slave.bootstrap();

    const local = await tryHttp({ port: slave.server.port, path: '/api/env' });
    expect(local.result?.status).toBe(200);

    const lan = lanIPv4();
    if (lan) {
      const remote = await tryHttp({
        hostname: lan,
        port: slave.server.port,
        path: '/api/env',
      });
      expect(remote.result).toBeUndefined();
      expect(remote.error).toBeDefined();
    }
  });
});
