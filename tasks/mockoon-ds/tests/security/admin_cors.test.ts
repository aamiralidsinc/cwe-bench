/**
 * Security: browser origins other than the explicitly allowed ones must not be
 * granted access to the management API, neither on ordinary responses nor on
 * preflight. No exact status is required: an omitted grant is enough, and the
 * request must not crash.
 */
import assert from 'node:assert';
import { describe, it } from 'node:test';
import { MockoonServer } from '/app/packages/commons-server/src/index';
import {
  allocator,
  assertNoCorsGrant,
  authHeaders,
  readFor,
  request,
  seedTransaction,
  withServer
} from '../support/env';

const TOKEN = 'admin-token-cors-suite';
const EVIL = 'https://evil.example';
const nextPort = allocator(4500);

describe('management API browser origin policy', () => {
  it('a disallowed origin gets no grant on an ordinary response', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        const res = await request(`${base}/mockoon-admin/logs`, {
          headers: { ...authHeaders(TOKEN), Origin: EVIL }
        });

        assertNoCorsGrant(
          res.headers.get('access-control-allow-origin'),
          EVIL
        );
        assert.ok(res.status < 500, 'the request crashed instead of refusing');
      },
      {},
      nextPort()
    );
  });

  it('a disallowed origin gets no grant on preflight', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const res = await request(`${base}/mockoon-admin/logs`, {
          method: 'OPTIONS',
          headers: {
            Origin: EVIL,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization'
          }
        });

        assert.ok(res.status < 500, 'the preflight crashed');
        assertNoCorsGrant(
          res.headers.get('access-control-allow-origin'),
          EVIL
        );
      },
      {},
      nextPort()
    );
  });

  it('no origin is granted when no origin is configured', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const origin = 'https://app.example';

        const res = await request(`${base}/mockoon-admin/logs`, {
          headers: { ...authHeaders(TOKEN), Origin: origin }
        });

        assertNoCorsGrant(
          res.headers.get('access-control-allow-origin'),
          origin
        );
      },
      {},
      nextPort()
    );
  });

  it('a disallowed origin gets no grant on the event stream', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const res = await readFor(
          `${base}/mockoon-admin/events`,
          { headers: { Origin: EVIL } },
          800
        );

        assertNoCorsGrant(
          res.headers.get('access-control-allow-origin'),
          EVIL
        );
      },
      {},
      nextPort()
    );
  });
});
