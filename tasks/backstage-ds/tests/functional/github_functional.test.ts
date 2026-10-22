/*
 * Hidden functional tests: the GitHub module keeps its existing credential
 * behaviour in the default configuration and accepts user tokens when the
 * setting is enabled.
 */
import { ConfigReader } from '@backstage/config';
import { createMockActionContext } from '@backstage/plugin-scaffolder-node-test-utils';
import { githubModule } from '../module';
import { Octokit } from 'octokit';

jest.mock('octokit', () => {
  const calls: any[] = [];
  const createIssue = jest
    .fn()
    .mockResolvedValue({
      data: { html_url: 'https://github.com/acme/example/issues/1', number: 1 },
    });
  const createRelease = jest.fn().mockResolvedValue({
    data: { id: 42, html_url: 'https://github.com/acme/example/releases/42' },
  });
  const createWebhook = jest.fn().mockResolvedValue({ data: { id: 7 } });
  const ctor: any = jest.fn((options: any) => {
    calls.push(options);
    return {
      rest: {
        issues: { create: createIssue },
        repos: { createRelease, createWebhook },
      },
    };
  });
  ctor.plugin = jest.fn(() => ctor);
  ctor.__calls = calls;
  return { Octokit: ctor };
});

const octokitMock: any = Octokit;

function config(requireCredentials: boolean) {
  return new ConfigReader({
    ...(requireCredentials
      ? { scaffolder: { requireScmUserCredentials: true } }
      : {}),
    integrations: {
      github: [{ host: 'github.com', token: 'backend-integration-token' }],
    },
  });
}

async function loadAction(
  requireCredentials: boolean,
  id: string,
): Promise<any> {
  const actions: any[] = [];
  const registration = (githubModule as any).getRegistrations()[0];
  await registration.init.func({
    scaffolder: { addActions: (...added: any[]) => actions.push(...added) },
    config: config(requireCredentials),
    catalog: {},
    autocomplete: { addAutocompleteProvider: () => {} },
  });
  return actions.find(candidate => candidate.id === id);
}

const REPO = 'github.com?repo=example&owner=acme';

beforeEach(() => {
  octokitMock.__calls.length = 0;
});

describe('GitHub module credential selection', () => {
  it('uses the integration credential by default when no user token is given', async () => {
    const action = await loadAction(false, 'github:issues:create');

    await action.handler(
      createMockActionContext({ input: { repoUrl: REPO, title: 'Issue' } }),
    );

    expect(octokitMock.__calls).toHaveLength(1);
    expect(octokitMock.__calls[0].auth).toBe('backend-integration-token');
  });

  it('uses the user token when one is given and the setting is enabled', async () => {
    const action = await loadAction(true, 'github:issues:create');

    await action.handler(
      createMockActionContext({
        input: { repoUrl: REPO, title: 'Issue', token: 'user-token' },
      }),
    );

    expect(octokitMock.__calls).toHaveLength(1);
    expect(octokitMock.__calls[0].auth).toBe('user-token');
  });

  it('keeps the integration fallback for the release action by default', async () => {
    const action = await loadAction(false, 'github:release:create');

    await action.handler(
      createMockActionContext({ input: { repoUrl: REPO, tagName: 'v1' } }),
    );

    expect(octokitMock.__calls).toHaveLength(1);
    expect(octokitMock.__calls[0].auth).toBe('backend-integration-token');
  });

  it('uses the user token for the release action when the setting is enabled', async () => {
    const action = await loadAction(true, 'github:release:create');

    await action.handler(
      createMockActionContext({
        input: { repoUrl: REPO, tagName: 'v1', token: 'user-token' },
      }),
    );

    expect(octokitMock.__calls).toHaveLength(1);
    expect(octokitMock.__calls[0].auth).toBe('user-token');
  });

  it('keeps the integration fallback for the webhook action by default', async () => {
    const action = await loadAction(false, 'github:webhook');

    await action.handler(
      createMockActionContext({
        input: { repoUrl: REPO, webhookUrl: 'https://example.com/hook' },
      }),
    );

    expect(octokitMock.__calls).toHaveLength(1);
    expect(octokitMock.__calls[0].auth).toBe('backend-integration-token');
  });

  it('uses the user token for the webhook action when the setting is enabled', async () => {
    const action = await loadAction(true, 'github:webhook');

    await action.handler(
      createMockActionContext({
        input: {
          repoUrl: REPO,
          webhookUrl: 'https://example.com/hook',
          token: 'user-token',
        },
      }),
    );

    expect(octokitMock.__calls).toHaveLength(1);
    expect(octokitMock.__calls[0].auth).toBe('user-token');
  });
});
