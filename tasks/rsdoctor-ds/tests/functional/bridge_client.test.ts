import { describe, expect, it } from '@rstest/core';
import { startAnalysisBridge } from '/workspace/packages/ai/dist/index.js';
import {
  disposeSdk,
  freePort,
  httpRequest,
  startSdk,
} from '../support/helpers';

describe('the assistant bridge serves local agents', () => {
  it('returns analysis data to a local client', async () => {
    const started = await startSdk();
    started.sdk.addClientRoutes(['Overall']);
    const bridge = await startAnalysisBridge({
      port: await freePort(),
      reportUrl: `http://127.0.0.1:${started.port}`,
    });

    try {
      const health = await httpRequest({
        port: bridge.port,
        path: '/health',
      });
      expect(health.status).toBe(200);

      const res = await httpRequest({
        port: bridge.port,
        path: '/api/analysis',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api: '/api/routes', body: {} }),
      });
      expect(res.status).toBe(200);
      expect(res.body).toContain('Overall');
    } finally {
      await bridge.close();
      await disposeSdk(started.sdk);
    }
  });
});
