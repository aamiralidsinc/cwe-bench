import { afterEach, describe, expect, it } from '@rstest/core';
import {
  disposeSdk,
  httpRequest,
  startSdk,
  tryHttp,
  type Started,
} from '../support/helpers';

describe('legitimate local clients keep working', () => {
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

  it('serves a client that sends no origin header', async () => {
    first = await startSdk();
    const res = await httpRequest({ port: first.port, path: '/api/env' });

    expect(res.status).toBe(200);
    expect(JSON.parse(res.body).port).toBe(first.port);
  });

  it('serves a browser page on a loopback origin', async () => {
    first = await startSdk();
    const res = await httpRequest({
      port: first.port,
      path: '/api/env',
      headers: {
        Host: `127.0.0.1:${first.port}`,
        Origin: `http://127.0.0.1:${first.port}`,
      },
    });

    expect(res.status).toBe(200);
    expect(res.headers['access-control-allow-origin']).toBeDefined();
  });

  it('serves a browser page on a localhost origin', async () => {
    first = await startSdk();
    const res = await httpRequest({
      port: first.port,
      path: '/api/env',
      headers: {
        Host: `localhost:${first.port}`,
        Origin: `http://localhost:${first.port}`,
      },
    });

    expect(res.status).toBe(200);
  });

  it('serves a page on one local port that reads a second local port', async () => {
    first = await startSdk();
    second = await startSdk();
    const res = await httpRequest({
      port: first.port,
      path: '/api/env',
      headers: {
        Host: `127.0.0.1:${first.port}`,
        Origin: `http://127.0.0.1:${second.port}`,
      },
    });

    expect(res.status).toBe(200);
  });

  it('serves a named localhost page whose name matches the host', async () => {
    first = await startSdk();
    const res = await httpRequest({
      port: first.port,
      path: '/api/env',
      headers: {
        Host: `preview.localhost:${first.port}`,
        Origin: `http://preview.localhost:${first.port}`,
      },
    });

    expect(res.status).toBe(200);
  });

  it('serves a request addressed to the IPv6 loopback host', async () => {
    first = await startSdk();
    const res = await httpRequest({
      port: first.port,
      path: '/api/env',
      headers: { Host: `[::1]:${first.port}` },
    });

    expect(res.status).toBe(200);
  });

  it('serves the report page to a local client', async () => {
    first = await startSdk();
    const res = await httpRequest({ port: first.port, path: '/index.html' });

    expect(res.status).toBe(200);
    expect(res.body.toLowerCase()).toContain('<html');
  });
});
