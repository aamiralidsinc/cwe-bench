/**
 * Security: the serverless wrapper is another supported way to run the same
 * server. Its request listener must enforce the configured management token,
 * whether the token comes from an option or from the runtime environment.
 */
import assert from 'node:assert';
import { describe, it } from 'node:test';
import { MockoonServerless } from '/app/packages/serverless/src/libs/serverless';
import {
  TXN_MARKER,
  allocator,
  assertClientError,
  authHeaders,
  makeEnvironment,
  request,
  seedTransaction,
  serveListener
} from '../support/env';

const TOKEN = 'admin-token-serverless-suite';
const nextPort = allocator(4700);

describe('serverless management authentication', () => {
  it('a configured token is required by the serverless listener', async () => {
    const port = nextPort();
    const wrapper = new MockoonServerless(makeEnvironment(0), {
      enableAdminApi: true,
      adminApiAuthToken: TOKEN
    });
    const mounted = await serveListener(wrapper.requestListener(), port);

    try {
      await seedTransaction(mounted.base);

      const refused = await request(`${mounted.base}/mockoon-admin/logs`);

      assertClientError(refused.status, 'serverless without a token');
      assert.ok(
        !refused.text.includes(TXN_MARKER),
        'the serverless listener returned transaction data without a token'
      );

      const wrong = await request(`${mounted.base}/mockoon-admin/logs`, {
        headers: authHeaders('definitely-not-the-token')
      });

      assertClientError(wrong.status, 'serverless with a wrong token');
    } finally {
      await mounted.close();
    }
  });

  it('the environment token is required when no option is given', async () => {
    const previous = process.env['MOCKOON_ADMIN_API_TOKEN'];
    process.env['MOCKOON_ADMIN_API_TOKEN'] = TOKEN;
    const port = nextPort();

    try {
      const wrapper = new MockoonServerless(makeEnvironment(0), {
        enableAdminApi: true
      });
      const mounted = await serveListener(wrapper.requestListener(), port);

      try {
        const refused = await request(`${mounted.base}/mockoon-admin/logs`);

        assertClientError(refused.status, 'serverless with no supplied token');

        const wrong = await request(`${mounted.base}/mockoon-admin/logs`, {
          headers: authHeaders('definitely-not-the-token')
        });

        assertClientError(
          wrong.status,
          'serverless with a wrong token from the environment'
        );
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
