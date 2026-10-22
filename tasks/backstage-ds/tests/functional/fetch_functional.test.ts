/*
 * Hidden functional tests: the built-in fetch actions keep working for hosts
 * that have no user-token concept, for local template paths, and in the default
 * configuration.
 */
import fs from 'fs-extra';
import os from 'node:os';
import path from 'node:path';
import { ConfigReader } from '@backstage/config';
import { ScmIntegrations } from '@backstage/integration';
import { createMockActionContext } from '@backstage/plugin-scaffolder-node-test-utils';
import { createFetchPlainAction } from '../plain';
import { createFetchPlainFileAction } from '../plainFile';
import { createFetchTemplateAction } from '../template';
import { createFetchTemplateFileAction } from '../templateFile';

function integrations() {
  return ScmIntegrations.fromConfig(
    new ConfigReader({
      integrations: {
        github: [{ host: 'github.com', token: 'backend-integration-token' }],
        bitbucketServer: [
          { host: 'bitbucket.example.com', token: 'bitbucket-token' },
        ],
      },
    }),
  );
}

function mockReader() {
  return {
    readTree: jest.fn().mockResolvedValue({ dir: jest.fn() }),
    readUrl: jest
      .fn()
      .mockResolvedValue({ buffer: jest.fn().mockResolvedValue(Buffer.from('hello')) }),
  };
}

function options(enabled: boolean, reader: any) {
  return {
    reader,
    integrations: integrations(),
    ...(enabled ? { requireScmUserCredentials: true } : {}),
  } as any;
}

function action(enabled: boolean, reader: any) {
  return createFetchPlainAction(options(enabled, reader));
}

function templateContext(input: Record<string, unknown>, templateInfo?: any) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-temp-'));
  const context = createMockActionContext({ input, templateInfo });
  (context as any).createTemporaryDirectory = jest
    .fn()
    .mockResolvedValue(tempDir);
  return { context, tempDir };
}

describe('built-in fetch actions keep working', () => {
  it('reads a plain HTTPS location with the setting enabled', async () => {
    const reader = mockReader();

    await action(true, reader).handler(
      createMockActionContext({
        input: { url: 'https://example.com/templates/skeleton' },
      }),
    );

    expect(reader.readTree).toHaveBeenCalledTimes(1);
  });

  it('reads a Bitbucket Server location with the setting enabled', async () => {
    const reader = mockReader();

    await action(true, reader).handler(
      createMockActionContext({
        input: {
          url: 'https://bitbucket.example.com/projects/ACME/repos/templates/browse/skeleton',
        },
      }),
    );

    expect(reader.readTree).toHaveBeenCalledTimes(1);
  });

  it('reads GitHub content with a user token when the setting is enabled', async () => {
    const reader = mockReader();

    await action(true, reader).handler(
      createMockActionContext({
        input: {
          url: 'https://github.com/acme/templates/tree/main/skeleton',
          token: 'user-token',
        },
      }),
    );

    expect(reader.readTree).toHaveBeenCalledTimes(1);
    expect(reader.readTree.mock.calls[0][1]).toEqual({ token: 'user-token' });
  });

  it('keeps the integration fallback in the default configuration', async () => {
    const reader = mockReader();

    await action(false, reader).handler(
      createMockActionContext({
        input: { url: 'https://github.com/acme/templates/tree/main/skeleton' },
      }),
    );

    expect(reader.readTree).toHaveBeenCalledTimes(1);
  });

  it('copies a relative local template path with the setting enabled', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-local-'));
    try {
      const templateDir = path.join(root, 'templates');
      fs.mkdirpSync(path.join(templateDir, 'skeleton'));
      fs.writeFileSync(path.join(templateDir, 'skeleton', 'file.txt'), 'hello');

      const reader = mockReader();
      const context = createMockActionContext({
        input: { url: './skeleton' },
        templateInfo: {
          baseUrl: `file://${path.join(templateDir, 'template.yaml')}`,
        },
      });

      await action(true, reader).handler(context);

      expect(reader.readTree).not.toHaveBeenCalled();
    } finally {
      fs.removeSync(root);
    }
  });

  it('fetch:template reads a plain HTTPS location with the setting enabled', async () => {
    const reader = mockReader();
    const { context, tempDir } = templateContext({
      url: 'https://example.com/templates/skeleton',
      values: {},
    });
    try {
      await createFetchTemplateAction(options(true, reader)).handler(context);
    } finally {
      fs.removeSync(tempDir);
    }

    expect(reader.readTree).toHaveBeenCalledTimes(1);
  });

  it('fetch:template reads a Bitbucket Server location with the setting enabled', async () => {
    const reader = mockReader();
    const { context, tempDir } = templateContext({
      url: 'https://bitbucket.example.com/projects/ACME/repos/templates/browse/skeleton',
      values: {},
    });
    try {
      await createFetchTemplateAction(options(true, reader)).handler(context);
    } finally {
      fs.removeSync(tempDir);
    }

    expect(reader.readTree).toHaveBeenCalledTimes(1);
  });

  it('fetch:template copies a relative local template path with the setting enabled', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-template-'));
    try {
      const templateDir = path.join(root, 'templates');
      fs.mkdirpSync(path.join(templateDir, 'skeleton'));
      fs.writeFileSync(path.join(templateDir, 'skeleton', 'file.txt'), 'hello');

      const reader = mockReader();
      const { context, tempDir } = templateContext(
        { url: './skeleton', targetPath: './target', values: {} },
        {
          baseUrl: `file://${path.join(templateDir, 'template.yaml')}`,
        },
      );
      try {
        await createFetchTemplateAction(options(true, reader)).handler(context);
      } finally {
        fs.removeSync(tempDir);
      }

      expect(reader.readTree).not.toHaveBeenCalled();
    } finally {
      fs.removeSync(root);
    }
  });

  it('fetch:plain:file reads a plain HTTPS location with the setting enabled', async () => {
    const reader = mockReader();

    await createFetchPlainFileAction(options(true, reader)).handler(
      createMockActionContext({
        input: {
          url: 'https://example.com/templates/file.txt',
          targetPath: './file.txt',
        },
      }),
    );

    expect(reader.readUrl).toHaveBeenCalledTimes(1);
  });

  it('fetch:plain:file copies a relative local file with the setting enabled', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-file-'));
    try {
      const templateDir = path.join(root, 'templates');
      fs.mkdirpSync(templateDir);
      fs.writeFileSync(path.join(templateDir, 'file.txt'), 'hello');

      const reader = mockReader();
      const context = createMockActionContext({
        input: { url: './file.txt', targetPath: './copied.txt' },
        templateInfo: {
          baseUrl: `file://${path.join(templateDir, 'template.yaml')}`,
        },
      });
      // The fetch helper copies straight into the workspace, which the real
      // task runner creates before invoking a step.
      fs.ensureDirSync(context.workspacePath);

      await createFetchPlainFileAction(options(true, reader)).handler(context);

      expect(reader.readUrl).not.toHaveBeenCalled();
    } finally {
      fs.removeSync(root);
    }
  });

  it('fetch:template:file reads a plain HTTPS location with the setting enabled', async () => {
    const reader = mockReader();
    const { context, tempDir } = templateContext({
      url: 'https://example.com/templates/file.txt',
      targetPath: './rendered.txt',
      values: {},
    });
    try {
      await createFetchTemplateFileAction(options(true, reader)).handler(
        context,
      );
    } finally {
      fs.removeSync(tempDir);
    }

    expect(reader.readUrl).toHaveBeenCalledTimes(1);
  });

  it('fetch:template:file copies a relative local file with the setting enabled', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-template-file-'));
    try {
      const templateDir = path.join(root, 'templates');
      fs.mkdirpSync(templateDir);
      fs.writeFileSync(path.join(templateDir, 'file.txt'), 'hello');

      const reader = mockReader();
      const { context, tempDir } = templateContext(
        { url: './file.txt', targetPath: './rendered.txt', values: {} },
        {
          baseUrl: `file://${path.join(templateDir, 'template.yaml')}`,
        },
      );
      try {
        await createFetchTemplateFileAction(options(true, reader)).handler(
          context,
        );
      } finally {
        fs.removeSync(tempDir);
      }

      expect(reader.readUrl).not.toHaveBeenCalled();
    } finally {
      fs.removeSync(root);
    }
  });
});
