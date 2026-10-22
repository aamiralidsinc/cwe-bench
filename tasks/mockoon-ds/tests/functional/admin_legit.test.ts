/**
 * Functional: legitimate use must keep working exactly as before. These drive
 * the same real entry points with the configured token and check the coupled
 * behaviour next to each security lever: mock routes and their environment
 * CORS, the management endpoints, event and log streams, environment-variable
 * reads and prefixed writes, runtime transaction logging, and the serverless
 * wrapper.
 */
import assert from 'node:assert';
import { describe, it } from 'node:test';
import {
  MockoonServer,
  listenServerEvents
} from '/app/packages/commons-server/src/index';
import { MockoonServerless } from '/app/packages/serverless/src/libs/serverless';
import {
  DEFAULT_PREFIX,
  TXN_URL,
  allocator,
  assertGrantsOrigin,
  authHeaders,
  captureLogger,
  collectWebSocket,
  delay,
  makeEnvironment,
  readFor,
  request,
  seedTransaction,
  serveListener,
  withServer
} from '../support/env';

const TOKEN = 'admin-token-functional-suite';
const nextPort = allocator(4800);

describe('legitimate server use', () => {
  it('mock routes keep their environment headers and CORS behaviour', async () => {
    const environmentHeaders = [
      {
        key: 'Access-Control-Allow-Origin',
        value: 'https://mock-allowed.example'
      },
      { key: 'X-Env-Header', value: 'env-header-value' }
    ];

    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const res = await request(`${base}/hello`);

        assert.strictEqual(res.status, 200);
        assert.strictEqual(res.text, 'hello-body');
        assert.strictEqual(
          res.headers.get('access-control-allow-origin'),
          'https://mock-allowed.example'
        );
        assert.strictEqual(res.headers.get('x-env-header'), 'env-header-value');

        const preflight = await request(`${base}/hello`, {
          method: 'OPTIONS',
          headers: {
            Origin: 'https://mock-allowed.example',
            'Access-Control-Request-Method': 'GET'
          }
        });

        assert.strictEqual(preflight.status, 200);
        assert.strictEqual(
          preflight.headers.get('access-control-allow-origin'),
          'https://mock-allowed.example'
        );
        assert.strictEqual(
          preflight.headers.get('x-env-header'),
          'env-header-value'
        );
      },
      { cors: true, headers: environmentHeaders },
      nextPort()
    );
  });

  it('management endpoints work with the configured token', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        const welcome = await request(`${base}/mockoon-admin`, {
          headers: authHeaders(TOKEN)
        });
        assert.ok(welcome.status >= 200 && welcome.status < 300);

        const logs = await request(`${base}/mockoon-admin/logs`, {
          headers: authHeaders(TOKEN)
        });
        assert.ok(logs.status >= 200 && logs.status < 300);
        const parsed = JSON.parse(logs.text);
        assert.ok(Array.isArray(parsed) && parsed.length >= 1);
        assert.strictEqual(parsed[0].request.urlPath, TXN_URL);
      },
      {},
      nextPort()
    );
  });

  it('global variables can be written and read with the token', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const write = await request(`${base}/mockoon-admin/global-vars`, {
          method: 'POST',
          headers: {
            ...authHeaders(TOKEN),
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ key: 'functional-key', value: 'functional-value' })
        });
        assert.ok(write.status >= 200 && write.status < 300);

        const read = await request(
          `${base}/mockoon-admin/global-vars/functional-key`,
          { headers: authHeaders(TOKEN) }
        );
        assert.ok(read.status >= 200 && read.status < 300);
        assert.strictEqual(JSON.parse(read.text).value, 'functional-value');
      },
      {},
      nextPort()
    );
  });

  it('environment variable reads keep their automatic prefix', async () => {
    process.env[`${DEFAULT_PREFIX}READ_AUTO_9137`] = 'prefixed-value';

    try {
      await withServer(
        MockoonServer,
        { adminApiAuthToken: TOKEN },
        async ({ base }) => {
          const read = await request(`${base}/mockoon-admin/env-vars/READ_AUTO_9137`, {
            headers: authHeaders(TOKEN)
          });

          assert.ok(read.status >= 200 && read.status < 300);
          const parsed = JSON.parse(read.text);
          assert.strictEqual(
            parsed.key,
            `${DEFAULT_PREFIX}READ_AUTO_9137`,
            'the read did not use the configured prefix'
          );
          assert.strictEqual(parsed.value, 'prefixed-value');
        },
        {},
        nextPort()
      );
    } finally {
      delete process.env[`${DEFAULT_PREFIX}READ_AUTO_9137`];
    }
  });

  it('prefixed environment variable writes work', async () => {
    const name = `${DEFAULT_PREFIX}WRITE_OK_9137`;
    delete process.env[name];

    try {
      await withServer(
        MockoonServer,
        { adminApiAuthToken: TOKEN },
        async ({ base }) => {
          const write = await request(`${base}/mockoon-admin/env-vars`, {
            method: 'POST',
            headers: {
              ...authHeaders(TOKEN),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key: name, value: 'written-value' })
          });

          assert.ok(write.status >= 200 && write.status < 300);
          assert.strictEqual(process.env[name], 'written-value');
        },
        {},
        nextPort()
      );
    } finally {
      delete process.env[name];
    }
  });

  it('prefixed bulk imports work', async () => {
    const name = `${DEFAULT_PREFIX}BULK_OK_9137`;
    delete process.env[name];

    try {
      await withServer(
        MockoonServer,
        { adminApiAuthToken: TOKEN },
        async ({ base }) => {
          const write = await request(`${base}/mockoon-admin/env-vars/import`, {
            method: 'POST',
            headers: {
              ...authHeaders(TOKEN),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ variables: { [name]: 'bulk-value' } })
          });

          assert.ok(write.status >= 200 && write.status < 300);
          assert.strictEqual(process.env[name], 'bulk-value');
        },
        {},
        nextPort()
      );
    } finally {
      delete process.env[name];
    }
  });

  it('data bucket listing works with the token', async () => {
    const bucket = {
      uuid: '55555555-5555-4555-8555-555555555555',
      id: 'bucket-functional',
      name: 'functional-bucket',
      documentation: '',
      value: '{"a":1}'
    };

    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const listed = await request(`${base}/mockoon-admin/data-buckets`, {
          headers: authHeaders(TOKEN)
        });

        assert.ok(listed.status >= 200 && listed.status < 300);
        assert.ok(
          listed.text.includes('functional-bucket'),
          'the data bucket list did not include the configured bucket'
        );
      },
      { data: [bucket] },
      nextPort()
    );
  });

  it('environment updates work with the token', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base, port }) => {
        const updated = makeEnvironment(port, {
          headers: [
            { key: 'Content-Type', value: 'text/plain' },
            { key: 'X-Updated-Header', value: 'updated-value' }
          ]
        });

        const write = await request(`${base}/mockoon-admin/environment`, {
          method: 'PUT',
          headers: {
            ...authHeaders(TOKEN),
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(updated)
        });
        assert.ok(write.status >= 200 && write.status < 300);

        const probe = await request(`${base}/hello`);
        assert.strictEqual(
          probe.headers.get('x-updated-header'),
          'updated-value',
          'the environment update did not take effect'
        );
      },
      {},
      nextPort()
    );
  });

  it('the event stream delivers live transactions with the token', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        const reading = readFor(
          `${base}/mockoon-admin/events?token=${encodeURIComponent(TOKEN)}`,
          {},
          1500
        );

        await delay(150);
        await seedTransaction(base);

        const res = await reading;
        assert.ok(
          res.body.includes('transaction-complete'),
          'no transaction event was delivered'
        );
        assert.ok(
          res.body.includes(TXN_URL),
          'the delivered transaction did not contain the request path'
        );
      },
      {},
      nextPort()
    );
  });

  it('the management stream delivers transactions with the token', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base, port }) => {
        await seedTransaction(base);

        const messages = await collectWebSocket(
          `ws://127.0.0.1:${port}/mockoon-admin/logs/stream?token=${encodeURIComponent(
            TOKEN
          )}`,
          1500
        );
        const received = messages.join('');
        assert.ok(
          received.includes('transaction-complete'),
          'the management stream delivered no transaction'
        );
        assert.ok(
          received.includes(TXN_URL),
          'the delivered transaction did not contain the request path'
        );
      },
      {},
      nextPort()
    );
  });

  it('a configured origin is granted access to the management API', async () => {
    const origin = 'https://app.example';

    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN, adminApiCorsOrigins: [origin] },
      async ({ base }) => {
        await seedTransaction(base);

        const res = await request(`${base}/mockoon-admin/logs`, {
          headers: { ...authHeaders(TOKEN), Origin: origin }
        });

        assert.ok(res.status >= 200 && res.status < 300);
        assertGrantsOrigin(
          res.headers.get('access-control-allow-origin'),
          origin,
          'management response'
        );
      },
      {},
      nextPort()
    );
  });

  it('a configured origin can preflight the management API', async () => {
    const origin = 'https://app.example';

    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN, adminApiCorsOrigins: [origin] },
      async ({ base }) => {
        const res = await request(`${base}/mockoon-admin/logs`, {
          method: 'OPTIONS',
          headers: {
            Origin: origin,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization'
          }
        });

        assert.ok(res.status >= 200 && res.status < 300);
        assertGrantsOrigin(
          res.headers.get('access-control-allow-origin'),
          origin,
          'management preflight'
        );
      },
      {},
      nextPort()
    );
  });

  it('runtime transaction logging still records transactions', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base, server, port }) => {
        const { logger, text } = captureLogger();
        listenServerEvents(server, makeEnvironment(port), logger, true);

        await seedTransaction(base);

        const logged = text();
        assert.ok(
          logged.includes(TXN_URL),
          'the runtime transaction log did not contain the request path'
        );
        assert.ok(
          logged.includes('transaction'),
          'the runtime transaction log did not contain the transaction'
        );
      },
      {},
      nextPort()
    );
  });

  it('the serverless listener serves mocks and the management API with the token', async () => {
    const port = nextPort();
    const wrapper = new MockoonServerless(makeEnvironment(0), {
      enableAdminApi: true,
      adminApiAuthToken: TOKEN
    });
    const mounted = await serveListener(wrapper.requestListener(), port);

    try {
      const mock = await request(`${mounted.base}/hello`);
      assert.strictEqual(mock.status, 200);
      assert.strictEqual(mock.text, 'hello-body');

      await seedTransaction(mounted.base);

      const logs = await request(`${mounted.base}/mockoon-admin/logs`, {
        headers: authHeaders(TOKEN)
      });
      assert.ok(logs.status >= 200 && logs.status < 300);
      assert.ok(Array.isArray(JSON.parse(logs.text)));
    } finally {
      await mounted.close();
    }
  });

  it('the serverless listener honours the environment token', async () => {
    const previous = process.env['MOCKOON_ADMIN_API_TOKEN'];
    process.env['MOCKOON_ADMIN_API_TOKEN'] = TOKEN;
    const port = nextPort();

    try {
      const wrapper = new MockoonServerless(makeEnvironment(0), {
        enableAdminApi: true
      });
      const mounted = await serveListener(wrapper.requestListener(), port);

      try {
        const logs = await request(`${mounted.base}/mockoon-admin/logs`, {
          headers: authHeaders(TOKEN)
        });
        assert.ok(logs.status >= 200 && logs.status < 300);
        assert.ok(Array.isArray(JSON.parse(logs.text)));
      } finally {
        await mounted.close();
      }
    } finally {
      if (previous === undefined) {
        delete process.env['MOCKOON_ADMIN_API_TOKEN'];
      } else {
        process.env['MOCKOON_ADMIN_API_TOKEN'] = previous;
      }
    }
  });
});
