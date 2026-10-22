import { describe, expect, it } from '@rstest/core';
import { RsdoctorSDKController } from '/workspace/packages/sdk/dist/index.js';
import { disposeSdk, freePort, httpRequest } from '../support/helpers';

describe('a second report server for multi-compiler builds serves locally', () => {
  it('answers a local client', async () => {
    const controller = new RsdoctorSDKController('/workspace');
    const port = await freePort();
    const slave: any = controller.createSlave({
      name: 'slave-local',
      type: 0,
      extraConfig: { server: { port } },
    });

    try {
      await slave.bootstrap();
      const res = await httpRequest({
        port: slave.server.port,
        path: '/api/env',
      });
      expect(res.status).toBe(200);
      expect(JSON.parse(res.body).port).toBe(slave.server.port);
    } finally {
      await disposeSdk(slave);
    }
  });
});
