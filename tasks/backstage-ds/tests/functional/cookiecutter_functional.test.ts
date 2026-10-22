/*
 * Hidden functional tests: the cookiecutter fetch step keeps its behaviour.
 *
 * With the setting absent or false the step keeps using the instance's
 * integration credential exactly as it does today; with the setting enabled a
 * location that is not source-control content is still fetched.
 */
import fs from 'fs-extra';
import os from 'node:os';
import path from 'node:path';
import { ConfigReader } from '@backstage/config';
import { createMockActionContext } from '@backstage/plugin-scaffolder-node-test-utils';
import { cookiecutterModule } from '../module';

function config(requireCredentials?: boolean) {
  return new ConfigReader({
    ...(requireCredentials === undefined
      ? {}
      : { scaffolder: { requireScmUserCredentials: requireCredentials } }),
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

async function loadAction(reader: any, configReader: ConfigReader): Promise<any> {
  const actions: any[] = [];
  const registration = (cookiecutterModule as any).getRegistrations()[0];
  await registration.init.func({
    scaffolder: {
      addActions: (...added: any[]) => actions.push(...added),
    },
    config: configReader,
    reader,
  });
  return actions.find(candidate => candidate.id === 'fetch:cookiecutter');
}

// The template engine itself is not installed here; the fetch is what matters,
// so the handler's later failure is ignored and the reader call is asserted.
async function runHandler(action: any, input: Record<string, unknown>) {
  const ctx = createMockActionContext({ input });
  (ctx as any).createTemporaryDirectory = jest
    .fn()
    .mockResolvedValue(fs.mkdtempSync(path.join(os.tmpdir(), 'cookiecutter-temp-')));
  try {
    await action.handler(ctx);
  } catch {
    /* cookiecutter is not installed in the verifier image */
  }
}

const GITHUB = 'https://github.com/acme/templates/tree/main/skeleton';

describe('the cookiecutter fetch step keeps working', () => {
  it('uses the integration credential when the setting is absent', async () => {
    const reader = mockReader();
    const action = await loadAction(reader, config());
    expect(action).toBeDefined();

    await runHandler(action, { url: GITHUB, values: {} });

    expect(reader.readTree).toHaveBeenCalled();
  });

  it('uses the integration credential when the setting is false', async () => {
    const reader = mockReader();
    const action = await loadAction(reader, config(false));
    expect(action).toBeDefined();

    await runHandler(action, { url: GITHUB, values: {} });

    expect(reader.readTree).toHaveBeenCalled();
  });

  it('fetches a plain location that is not source-control content with the setting enabled', async () => {
    const reader = mockReader();
    const action = await loadAction(reader, config(true));
    expect(action).toBeDefined();

    await runHandler(action, {
      url: 'https://example.com/templates/skeleton',
      values: {},
    });

    expect(reader.readTree).toHaveBeenCalled();
  });
});
