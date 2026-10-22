/**
 * Security: recorded transactions carry credentials in their request and
 * response headers. Every management output that exposes transactions must
 * keep the header names but never the sensitive values.
 */
import assert from 'node:assert';
import { describe, it } from 'node:test';
import {
  MockoonServer,
  listenServerEvents
} from '/app/packages/commons-server/src/index';
import {
  SECRET_APIKEY,
  SECRET_COOKIE,
  TXN_MARKER,
  TXN_URL,
  allocator,
  assertNoSecrets,
  authHeaders,
  captureLogger,
  collectWebSocket,
  delay,
  makeEnvironment,
  readFor,
  request,
  seedTransaction,
  withServer
} from '../support/env';

const TOKEN = 'admin-token-redaction-suite';
const nextPort = allocator(4400);

describe('transaction redaction', () => {
  it('the logs endpoint keeps header names but redacts sensitive values', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        const res = await request(`${base}/mockoon-admin/logs`, {
          headers: authHeaders(TOKEN)
        });

        assert.ok(res.status >= 200 && res.status < 300);
        assert.ok(
          res.text.includes(TXN_MARKER),
          'the transaction log did not contain the recorded transaction'
        );
        assert.ok(
          res.text.includes('x-api-key'),
          'the header name was dropped instead of its value being redacted'
        );
        assertNoSecrets(res.text, 'logs endpoint');
      },
      {},
      nextPort()
    );
  });

  it('the event stream replay keeps header names but redacts sensitive values', async () => {
    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base }) => {
        await seedTransaction(base);

        const res = await readFor(
          `${base}/mockoon-admin/events?token=${encodeURIComponent(TOKEN)}`,
          {},
          1000
        );

        assert.ok(
          res.body.includes('transaction-complete'),
          'the event stream delivered no replayed transaction'
        );
        assert.ok(
          res.body.includes(TXN_MARKER),
          'the replayed transaction did not match the recorded one'
        );
        assertNoSecrets(res.body, 'event stream replay');
      },
      {},
      nextPort()
    );
  });

  it('the event stream live events keep header names but redact sensitive values', async () => {
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
          'the event stream delivered no live transaction'
        );
        assertNoSecrets(res.body, 'event stream live');
      },
      {},
      nextPort()
    );
  });

  it('the management stream keeps header names but redacts sensitive values', async () => {
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
          received.includes('x-api-key'),
          'the header name was dropped instead of its value being redacted'
        );
        assertNoSecrets(received, 'management stream');
      },
      {},
      nextPort()
    );
  });

  it('runtime transaction logging keeps header names but redacts sensitive values', async () => {
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
          'the runtime transaction log did not contain the recorded request'
        );
        assert.ok(
          logged.includes('x-api-key'),
          'the header name was dropped instead of its value being redacted'
        );
        assertNoSecrets(logged, 'runtime transaction log');
        assert.ok(
          !logged.includes(SECRET_COOKIE) && !logged.includes(SECRET_APIKEY),
          'a credential value was written to the runtime transaction log'
        );
      },
      {},
      nextPort()
    );
  });

  it('a credential reproduced in a recorded response is redacted wherever it is exposed', async () => {
    // A mock response may reproduce a request header in a field other than the
    // header it arrived in. The recorded credential must not leave the server
    // in any of the forms that expose that record.
    const template = ['authorization', 'cookie', 'x-api-key', 'x-auth-token']
      .map((header) => `{{{header '${header}'}}}`)
      .join('|');
    const baseEnvironment = makeEnvironment(0);
    const echoingEnvironment = {
      routes: [
        {
          ...baseEnvironment.routes[0],
          responses: [
            {
              ...baseEnvironment.routes[0].responses[0],
              headers: [{ key: 'X-Echoed-Key', value: "{{{header 'x-api-key'}}}" }],
              body: template
            }
          ]
        }
      ]
    };

    await withServer(
      MockoonServer,
      { adminApiAuthToken: TOKEN },
      async ({ base, server, port }) => {
        const { logger, text } = captureLogger();
        listenServerEvents(server, makeEnvironment(port), logger, true);

        const liveReading = readFor(
          `${base}/mockoon-admin/events?token=${encodeURIComponent(TOKEN)}`,
          {},
          1500
        );
        await delay(150);
        await seedTransaction(base);
        const live = await liveReading;

        assert.ok(
          live.body.includes('transaction-complete'),
          'the live update did not contain the recorded transaction'
        );
        assertNoSecrets(live.body, 'a live update of the reproduced credential');

        const logs = await request(`${base}/mockoon-admin/logs`, {
          headers: authHeaders(TOKEN)
        });

        assert.ok(logs.status >= 200 && logs.status < 300);
        assert.ok(
          logs.text.includes(TXN_MARKER),
          'the recorded transaction was not returned'
        );
        assertNoSecrets(logs.text, 'the log listing of the reproduced credential');

        const replay = await readFor(
          `${base}/mockoon-admin/events?token=${encodeURIComponent(TOKEN)}`,
          {},
          1000
        );

        assert.ok(
          replay.body.includes('transaction-complete'),
          'the replayed update did not contain the recorded transaction'
        );
        assertNoSecrets(
          replay.body,
          'a replayed update of the reproduced credential'
        );

        const messages = await collectWebSocket(
          `ws://127.0.0.1:${port}/mockoon-admin/logs/stream?token=${encodeURIComponent(
            TOKEN
          )}`,
          1500
        );

        assertNoSecrets(
          messages.join(''),
          'a live update of the reproduced credential'
        );

        assert.ok(
          text().includes(TXN_URL),
          'the runtime transaction log did not contain the recorded request'
        );
        assertNoSecrets(text(), 'the runtime log of the reproduced credential');
      },
      echoingEnvironment,
      nextPort()
    );
  });
});
