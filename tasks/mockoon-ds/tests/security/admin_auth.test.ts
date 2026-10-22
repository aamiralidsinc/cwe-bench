/**
 * Security: the management API answers only callers that present the
 * configured bearer token. Every test drives a real listener started through
 * the public server class; a refusal must be a client error and must not have
 * the requested effect.
 */
import assert from 'node:assert';
import { describe, it } from 'node:test';
import { MockoonServer } from '/app/packages/commons-server/src/index';
import {
  TXN_MARKER,
  allocator,
  assertClientError,
  authHeaders,
  delay,
  makeEnvironment,
  readFor,
  request,
  seedTransaction,
  withServer,
  collectWebSocket
} from '../support/env';

const TOKEN = 'admin-token-auth-suite';
const nextPort = allocator(4300);

describe('management API authentication', () => {
  it('an unauthenticated request cannot read recorded transactions', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        const res = await request(`${base}/mockoon-admin/logs`);

        assertClientError(res.status, 'unauthenticated log read');
        assert.ok(
          !res.text.includes(TXN_MARKER),
          'transaction data was returned without a token'
        );
      },
      {},
      nextPort()
    );
  });

  it('an unauthenticated global variable write has no effect', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const res = await request(`${base}/mockoon-admin/global-vars`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ key: 'probe-key', value: 'pwned-value' })
        });

        assertClientError(res.status, 'unauthenticated global variable write');

        const check = await request(
          `${base}/mockoon-admin/global-vars/probe-key`,
          { headers: authHeaders(TOKEN) }
        );

        assert.ok(check.status < 500, 'reading back the value failed');
        assert.ok(
          !check.text.includes('pwned-value'),
          'the variable was written without a token'
        );
      },
      {},
      nextPort()
    );
  });

  it('an unauthenticated environment variable write has no effect', async () => {
    const variable = 'UNSCOPED_AUTH_WRITE_9137';
    delete process.env[variable];

    try {
      await withServer(
        MockoonServer,
        { adminApiAuthToken: TOKEN },
        async ({ base }) => {
          const res = await request(`${base}/mockoon-admin/env-vars`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: variable, value: 'pwned-value' })
          });

          assertClientError(
            res.status,
            'unauthenticated environment variable write'
          );
          assert.strictEqual(
            process.env[variable],
            undefined,
            'the environment variable was written without a token'
          );
        },
        {},
        nextPort()
      );
    } finally {
      delete process.env[variable];
      delete process.env[`MOCKOON_${variable}`];
    }
  });

  it('an unauthenticated environment update has no effect', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base, port }) => {
        const updated = makeEnvironment(port, {
          headers: [
            { key: 'Content-Type', value: 'text/plain' },
            { key: 'X-Injected-Header', value: 'pwned-header' }
          ]
        });

        const res = await request(`${base}/mockoon-admin/environment`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updated)
        });

        assertClientError(res.status, 'unauthenticated environment update');

        const probe = await request(`${base}/hello`);
        assert.strictEqual(
          probe.headers.get('x-injected-header'),
          null,
          'the environment was updated without a token'
        );
      },
      {},
      nextPort()
    );
  });

  it('an unauthenticated event stream delivers no recorded transactions', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        const res = await readFor(`${base}/mockoon-admin/events`, {}, 1000);

        assert.ok(
          !res.body.includes(TXN_MARKER),
          'the event stream delivered transaction data without a token'
        );
        assert.ok(
          !res.body.includes('transaction-complete'),
          'the event stream delivered transaction events without a token'
        );
      },
      {},
      nextPort()
    );
  });

  it('an unauthenticated management stream delivers no recorded transactions', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base, port }) => {
        await seedTransaction(base);

        const messages = await collectWebSocket(
          `ws://127.0.0.1:${port}/mockoon-admin/logs/stream`
        );
        const received = messages.join('');

        assert.ok(
          !received.includes(TXN_MARKER),
          'the management stream delivered transaction data without a token'
        );
      },
      {},
      nextPort()
    );
  });

  it('a wrong bearer token is refused', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        const res = await request(`${base}/mockoon-admin/logs`, {
          headers: authHeaders('definitely-not-the-token')
        });

        assertClientError(res.status, 'wrong bearer token');
        assert.ok(
          !res.text.includes(TXN_MARKER),
          'transaction data was returned for a wrong token'
        );
      },
      {},
      nextPort()
    );
  });

  it('the bearer scheme is required in the authorization header', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        for (const value of [TOKEN, `Basic ${TOKEN}`, `Bearer`]) {
          const res = await request(`${base}/mockoon-admin/logs`, {
            headers: { Authorization: value }
          });

          assertClientError(res.status, `malformed authorization (${value})`);
          assert.ok(
            !res.text.includes(TXN_MARKER),
            `transaction data was returned for authorization '${value}'`
          );
        }
      },
      {},
      nextPort()
    );
  });

  it('a token in the query string does not authorize an ordinary request', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        const res = await request(
          `${base}/mockoon-admin/logs?token=${encodeURIComponent(TOKEN)}`
        );

        assertClientError(res.status, 'query token on an ordinary endpoint');
        assert.ok(
          !res.text.includes(TXN_MARKER),
          'transaction data was returned for a query token on an ordinary endpoint'
        );
      },
      {},
      nextPort()
    );
  });

  it('management stays closed when no token is configured', async () => {
    const previous = process.env['MOCKOON_ADMIN_API_TOKEN'];
    delete process.env['MOCKOON_ADMIN_API_TOKEN'];

    try {
      await withServer(
        MockoonServer,
        { enableAdminApi: true },
        async ({ base }) => {
          await seedTransaction(base);

          const res = await request(`${base}/mockoon-admin/logs`);

          assertClientError(res.status, 'unconfigured token');
          assert.ok(
            !res.text.includes(TXN_MARKER),
            'transaction data was returned when no token was configured'
          );
        },
        {},
        nextPort()
      );
    } finally {
      if (previous !== undefined) {
        process.env['MOCKOON_ADMIN_API_TOKEN'] = previous;
      }
    }
  });

  it('a refusal has no side effect on data buckets', async () => {
    const bucket = {
      uuid: '44444444-4444-4444-8444-444444444444',
      id: 'bucket-id',
      name: 'bucket-name',
      documentation: '',
      value: '{"a":1}'
    };

    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const purge = await request(`${base}/mockoon-admin/data-buckets`, {
          method: 'PURGE'
        });

        assertClientError(purge.status, 'unauthenticated data bucket purge');

        const listed = await request(`${base}/mockoon-admin/data-buckets`, {
          headers: authHeaders(TOKEN)
        });

        assert.ok(listed.status >= 200 && listed.status < 300);
        assert.ok(
          listed.text.includes('bucket-name'),
          'the unauthenticated purge removed data buckets'
        );
      },
      { data: [bucket] },
      nextPort()
    );
  });
});
