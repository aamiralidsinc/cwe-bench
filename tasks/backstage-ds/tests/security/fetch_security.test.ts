/*
 * Hidden security tests: built-in template fetch actions.
 *
 * The four built-in fetch actions are public action factories. They read SCM
 * content through a URL reader; with the setting enabled and no user token they
 * must refuse before the reader is invoked. One case starts the real scaffolder
 * plugin from its normal startup wiring, so an implementation that only accepts
 * the option when it is passed by hand is not enough.
 */
import fs from 'fs-extra';
import os from 'node:os';
import path from 'node:path';
import { InputError } from '@backstage/errors';
import { ConfigReader } from '@backstage/config';
import { ScmIntegrations } from '@backstage/integration';
import { createMockActionContext } from '@backstage/plugin-scaffolder-node-test-utils';
import { createFetchPlainAction } from '../plain';
import { createFetchPlainFileAction } from '../plainFile';
import { createFetchTemplateAction } from '../template';
import { createFetchTemplateFileAction } from '../templateFile';

jest.mock('../../../../../service/router', () => ({
  createRouter: jest.fn(async () => ({})),
}));
jest.mock('../../../../../actions', () => ({
  createScaffolderActions: jest.fn(),
}));

// eslint-disable-next-line import/order
import { scaffolderPlugin } from '../../../../../ScaffolderPlugin';
// eslint-disable-next-line import/order
import { createRouter } from '../../../../../service/router';

function config() {
  return new ConfigReader({
    scaffolder: { requireScmUserCredentials: true },
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

function integrations() {
  return ScmIntegrations.fromConfig(config());
}

function mockReader() {
  return {
    readTree: jest.fn().mockResolvedValue({ dir: jest.fn() }),
    readUrl: jest
      .fn()
      .mockResolvedValue({ buffer: jest.fn().mockResolvedValue(Buffer.from('')) }),
  };
}

async function runHandler(action: any, input: Record<string, unknown>, templateInfo?: any) {
  const ctx = createMockActionContext({
    input,
    templateInfo,
  });
  // The mock context's createTemporaryDirectory returns undefined, but the template actions need a
  // real directory before they fetch (same set-up as functional/fetch_functional.test.ts). Without
  // it, a correct fix that refuses inside the shared fetch helpers crashed here with a TypeError.
  (ctx as any).createTemporaryDirectory = jest
    .fn()
    .mockResolvedValue(fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-temp-')));
  try {
    await action.handler(ctx);
    return undefined;
  } catch (error) {
    return error;
  }
}

async function loadPluginActions(reader: any): Promise<any[]> {
  const registration = (scaffolderPlugin as any).getRegistrations()[0];
  const logger = {
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
    child: jest.fn(),
  };
  await registration.init.func({
    logger,
    config: config(),
    lifecycle: {},
    reader,
    permissions: {},
    permissionsRegistry: {},
    database: {},
    auth: {},
    httpRouter: { use: jest.fn() },
    httpAuth: {},
    auditor: {},
    catalog: {},
    events: {},
    actionsRegistry: {},
    actionsRegistryService: {},
    scaffolderService: {},
    scheduler: {},
    metrics: {},
  });
  const calls = (createRouter as jest.Mock).mock.calls;
  return calls[calls.length - 1][0].actions;
}

const ABSOLUTE = 'https://github.com/acme/templates/tree/main/skeleton';
const ABSOLUTE_FILE =
  'https://github.com/acme/templates/blob/main/template.yaml';

beforeEach(() => {
  (createRouter as jest.Mock).mockClear();
});

describe('built-in fetch actions do not read SCM content without user credentials when required', () => {
  it('fetch:plain refuses an absolute GitHub URL without a user token', async () => {
    const reader = mockReader();
    const action = createFetchPlainAction({
      reader: reader as any,
      integrations: integrations(),
      requireScmUserCredentials: true,
    } as any);

    const error = await runHandler(action, { url: ABSOLUTE });

    expect(reader.readTree).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  it('fetch:plain refuses a relative URL resolved against a GitHub template location', async () => {
    const reader = mockReader();
    const action = createFetchPlainAction({
      reader: reader as any,
      integrations: integrations(),
      requireScmUserCredentials: true,
    } as any);

    const error = await runHandler(
      action,
      { url: './skeleton' },
      {
        baseUrl:
          'https://github.com/acme/templates/blob/main/template.yaml',
      },
    );

    expect(reader.readTree).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  it('fetch:plain refuses an absolute GitLab URL without a user token', async () => {
    const reader = mockReader();
    const action = createFetchPlainAction({
      reader: reader as any,
      integrations: integrations(),
      requireScmUserCredentials: true,
    } as any);

    const error = await runHandler(action, {
      url: 'https://gitlab.com/acme/templates/-/tree/main/skeleton',
    });

    expect(reader.readTree).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  it('fetch:plain refuses a GitHub URL when the integration entry has no token', async () => {
    const reader = mockReader();
    const action = createFetchPlainAction({
      reader: reader as any,
      integrations: ScmIntegrations.fromConfig(
        new ConfigReader({ integrations: { github: [{ host: 'github.com' }] } }),
      ),
      requireScmUserCredentials: true,
    } as any);

    const error = await runHandler(action, { url: ABSOLUTE });

    expect(reader.readTree).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  it('fetch:plain:file refuses without a user token', async () => {
    const reader = mockReader();
    const action = createFetchPlainFileAction({
      reader: reader as any,
      integrations: integrations(),
      requireScmUserCredentials: true,
    } as any);

    const error = await runHandler(action, {
      url: ABSOLUTE_FILE,
      targetPath: './',
    });

    expect(reader.readUrl).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  it('fetch:template refuses without a user token', async () => {
    const reader = mockReader();
    const action = createFetchTemplateAction({
      reader: reader as any,
      integrations: integrations(),
      requireScmUserCredentials: true,
    } as any);

    const error = await runHandler(action, { url: ABSOLUTE, values: {} });

    expect(reader.readTree).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  it('fetch:template:file refuses without a user token', async () => {
    const reader = mockReader();
    const action = createFetchTemplateFileAction({
      reader: reader as any,
      integrations: integrations(),
      requireScmUserCredentials: true,
    } as any);

    const error = await runHandler(action, {
      url: ABSOLUTE_FILE,
      targetPath: './',
      values: {},
    });

    expect(reader.readUrl).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(InputError);
  });

  const pluginCases: Array<{
    id: string;
    input: Record<string, unknown>;
    readerMethod: 'readTree' | 'readUrl';
  }> = [
    { id: 'fetch:plain', input: { url: ABSOLUTE }, readerMethod: 'readTree' },
    {
      id: 'fetch:plain:file',
      input: { url: ABSOLUTE_FILE, targetPath: './' },
      readerMethod: 'readUrl',
    },
    {
      id: 'fetch:template',
      input: { url: ABSOLUTE, values: {} },
      readerMethod: 'readTree',
    },
    {
      id: 'fetch:template:file',
      input: { url: ABSOLUTE_FILE, targetPath: './', values: {} },
      readerMethod: 'readUrl',
    },
  ];

  it.each(pluginCases)(
    '$id registered through the plugin startup refuses GitHub content without a user token',
    async ({ id, input, readerMethod }) => {
      const reader = mockReader();
      const actions = await loadPluginActions(reader);
      const action = actions.find(candidate => candidate.id === id);
      expect(action).toBeDefined();

      const error = await runHandler(action, input);

      expect(reader[readerMethod]).not.toHaveBeenCalled();
      expect(error).toBeInstanceOf(InputError);
    },
  );
});
