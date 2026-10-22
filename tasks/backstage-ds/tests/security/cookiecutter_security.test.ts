/*
 * Hidden security tests: the cookiecutter fetch step.
 *
 * The action is obtained from the real module init with the root config and its
 * handler is invoked with a mock action context. With the setting enabled the
 * step may not read source-control content at all: it has no credential input
 * of its own, so it must refuse before the reader is invoked rather than let
 * the URL reader use the instance's integration credential.
 */
import fs from 'fs-extra';
import os from 'node:os';
import path from 'node:path';
import { InputError } from '@backstage/errors';
import { ConfigReader } from '@backstage/config';
import { createMockActionContext } from '@backstage/plugin-scaffolder-node-test-utils';
import { cookiecutterModule } from '../module';

function config(requireCredentials: boolean) {
  return new ConfigReader({
    scaffolder: { requireScmUserCredentials: requireCredentials },
    integrations: {
      github: [{ host: 'github.com', token: 'backend-integration-token' }],
      gitlab: [
        {
          host: 'gitlab.com',
          apiBaseUrl: 'https://gitlab.com/api/v4',
          token: 'backend-integration-token',
        },
      ],
    },
  });
}

function mockReader() {
  return {
    readTree: jest.fn().mockResolvedValue({ dir: jest.fn() }),
    readUrl: jest
      .fn()
      .mockResolvedValue({ buffer: jest.fn().mockResolvedValue(Buffer.from('')) }),
  };
}

async function loadAction(reader: any): Promise<any> {
  const actions: any[] = [];
  const registration = (cookiecutterModule as any).getRegistrations()[0];
  await registration.init.func({
    scaffolder: {
      addActions: (...added: any[]) => actions.push(...added),
    },
    config: config(true),
    reader,
  });
  return actions.find(candidate => candidate.id === 'fetch:cookiecutter');
}

async function runHandler(action: any, input: Record<string, unknown>, templateInfo?: any) {
  const ctx = createMockActionContext({ input, templateInfo });
  // The template engine needs a real directory before it fetches anything.
  (ctx as any).createTemporaryDirectory = jest
    .fn()
    .mockResolvedValue(fs.mkdtempSync(path.join(os.tmpdir(), 'cookiecutter-temp-')));
  try {
    await action.handler(ctx);
    return undefined;
  } catch (error) {
    return error;
  }
}

const ABSOLUTE = 'https://github.com/acme/templates/tree/main/skeleton';
const BASE = 'https://github.com/acme/templates/blob/main/template.yaml';

describe('the cookiecutter fetch step does not read SCM content without user credentials when required', () => {
  it('refuses an absolute GitHub URL without a user credential', async () => {
    const reader = mockReader();
    const action = await loadAction(reader);
    expect(action).toBeDefined();

    const error = await runHandler(action, { url: ABSOLUTE, values: {} });

    expect(reader.readTree).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  it('refuses a relative URL resolved against a GitHub template location', async () => {
    const reader = mockReader();
    const action = await loadAction(reader);
    expect(action).toBeDefined();

    const error = await runHandler(
      action,
      { url: './skeleton', values: {} },
      { baseUrl: BASE },
    );

    expect(reader.readTree).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  it('refuses an absolute GitLab URL without a user credential', async () => {
    const reader = mockReader();
    const action = await loadAction(reader);
    expect(action).toBeDefined();

    const error = await runHandler(action, {
      url: 'https://gitlab.com/acme/templates/-/tree/main/skeleton',
      values: {},
    });

    expect(reader.readTree).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });
});
