/**
 * Security: environment-variable writes may only affect variables under the
 * configured prefix. The configured prefix is part of the server options; the
 * server may refuse such a write or store it under the prefix, but the bare key
 * must never reach the process environment. With no prefix configured, writes
 * are refused.
 */
import assert from 'node:assert';
import { describe, it } from 'node:test';
import { MockoonServer } from '/app/packages/commons-server/src/index';
import {
  DEFAULT_PREFIX,
  allocator,
  assertClientError,
  authHeaders,
  request,
  withServer
} from '../support/env';

const TOKEN = 'admin-token-env-suite';
const nextPort = allocator(4600);

const clean = (...names: string[]) => {
  for (const name of names) {
    delete process.env[name];
    delete process.env[`${DEFAULT_PREFIX}${name}`];
  }
};

describe('environment variable write scope', () => {
  it('a write outside the configured prefix leaves the bare key unset', async () => {
    const variable = 'UNSCOPED_WRITE_9137';
    clean(variable);

    try {
      await withServer(
        MockoonServer,
        { adminApiAuthToken: TOKEN, envVarsPrefix: DEFAULT_PREFIX },
        async ({ base }) => {
          const res = await request(`${base}/mockoon-admin/env-vars`, {
            method: 'POST',
            headers: {
              ...authHeaders(TOKEN),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key: variable, value: 'pwned-value' })
          });

          assert.strictEqual(
            process.env[variable],
            undefined,
            'a variable outside the configured prefix was written'
          );
        },
        {},
        nextPort()
      );
    } finally {
      clean(variable);
    }
  });

  it('a write is refused when the configured prefix is empty', async () => {
    const variable = 'UNSCOPED_EMPTY_PREFIX_9137';
    clean(variable);

    try {
      await withServer(
        MockoonServer,
        { adminApiAuthToken: TOKEN, envVarsPrefix: '' },
        async ({ base }) => {
          const res = await request(`${base}/mockoon-admin/env-vars`, {
            method: 'POST',
            headers: {
              ...authHeaders(TOKEN),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key: variable, value: 'pwned-value' })
          });

          assertClientError(res.status, 'write with an empty prefix');
          assert.strictEqual(
            process.env[variable],
            undefined,
            'a variable was written with an empty prefix'
          );
        },
        {},
        nextPort()
      );
    } finally {
      clean(variable);
    }
  });

  it('a bulk import outside the configured prefix leaves the bare key unset', async () => {
    const variable = 'UNSCOPED_BULK_9137';
    clean(variable);

    try {
      await withServer(
        MockoonServer,
        { adminApiAuthToken: TOKEN, envVarsPrefix: DEFAULT_PREFIX },
        async ({ base }) => {
          const res = await request(`${base}/mockoon-admin/env-vars/import`, {
            method: 'POST',
            headers: {
              ...authHeaders(TOKEN),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              variables: { [variable]: 'pwned-value' }
            })
          });

          assert.strictEqual(
            process.env[variable],
            undefined,
            'a bulk import wrote a variable outside the configured prefix'
          );
        },
        {},
        nextPort()
      );
    } finally {
      clean(variable);
    }
  });

  it('a bulk import is refused when the configured prefix is empty', async () => {
    const variable = 'UNSCOPED_BULK_EMPTY_9137';
    clean(variable);

    try {
      await withServer(
        MockoonServer,
        { adminApiAuthToken: TOKEN, envVarsPrefix: '' },
        async ({ base }) => {
          const res = await request(`${base}/mockoon-admin/env-vars/import`, {
            method: 'POST',
            headers: {
              ...authHeaders(TOKEN),
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              variables: { [variable]: 'pwned-value' }
            })
          });

          assertClientError(res.status, 'bulk import with an empty prefix');
          assert.strictEqual(
            process.env[variable],
            undefined,
            'a bulk import wrote a variable with an empty prefix'
          );
        },
        {},
        nextPort()
      );
    } finally {
      clean(variable);
    }
  });
});
