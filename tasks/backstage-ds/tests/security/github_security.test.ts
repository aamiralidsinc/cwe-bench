/*
 * Hidden security tests: GitHub scaffolder credential fallback.
 *
 * Every action is obtained from the real GitHub module init (the same function
 * the backend calls with the root config), and its handler is invoked with a
 * mock action context. The SCM client is mocked at the library boundary; a
 * request that would authenticate with the backend integration credential is
 * visible as a client construction carrying that token.
 */
import { InputError } from '@backstage/errors';
import { ConfigReader } from '@backstage/config';
import { ScmIntegrations } from '@backstage/integration';
import { createMockActionContext } from '@backstage/plugin-scaffolder-node-test-utils';
import { githubModule } from '../module';
import { createGithubIssuesCreateAction } from '../actions/githubIssuesCreate';
import { Octokit } from 'octokit';

jest.mock('octokit', () => {
  const calls: any[] = [];
  const ctor: any = jest.fn((options: any) => {
    calls.push(options);
    return { rest: {} };
  });
  ctor.plugin = jest.fn(() => ctor);
  ctor.__calls = calls;
  return { Octokit: ctor };
});

const octokitMock: any = Octokit;

function enabledConfig() {
  return new ConfigReader({
    scaffolder: { requireScmUserCredentials: true },
    integrations: {
      github: [{ host: 'github.com', token: 'backend-integration-token' }],
    },
  });
}

async function loadActions(config: ConfigReader): Promise<any[]> {
  const actions: any[] = [];
  const registration = (githubModule as any).getRegistrations()[0];
  await registration.init.func({
    scaffolder: {
      addActions: (...added: any[]) => actions.push(...added),
    },
    config,
    catalog: {},
    autocomplete: { addAutocompleteProvider: () => {} },
  });
  return actions;
}

async function runHandler(action: any, input: Record<string, unknown>) {
  const ctx = createMockActionContext({ input });
  try {
    await action.handler(ctx);
    return undefined;
  } catch (error) {
    return error;
  }
}

beforeEach(() => {
  octokitMock.__calls.length = 0;
});

const REPO = 'github.com?repo=example&owner=acme';

const cases: Array<{ id: string; input: Record<string, unknown> }> = [
  { id: 'publish:github', input: { repoUrl: REPO } },
  { id: 'github:repo:create', input: { repoUrl: REPO } },
  { id: 'github:repo:push', input: { repoUrl: REPO } },
  {
    id: 'github:actions:dispatch',
    input: { repoUrl: REPO, workflowId: 'deploy.yml', branchOrTagName: 'main' },
  },
  {
    id: 'github:autolinks:create',
    input: {
      repoUrl: REPO,
      keyPrefix: 'JIRA-',
      urlTemplate: 'https://jira.example.com/browse/JIRA-',
    },
  },
  {
    id: 'github:branch-protection:create',
    input: { repoUrl: REPO, branch: 'main' },
  },
  {
    id: 'github:deployKey:create',
    input: {
      repoUrl: REPO,
      publicKey: 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQ==',
      privateKey: '-----BEGIN PRIVATE KEY-----',
      deployKeyName: 'Deploy Key',
    },
  },
  { id: 'github:environment:create', input: { repoUrl: REPO, name: 'prod' } },
  { id: 'github:issues:create', input: { repoUrl: REPO, title: 'Issue' } },
  {
    id: 'github:issues:label',
    input: { repoUrl: REPO, number: 1, labels: ['bug'] },
  },
  { id: 'github:pages:enable', input: { repoUrl: REPO } },
  {
    id: 'github:webhook',
    input: { repoUrl: REPO, webhookUrl: 'https://example.com/hook' },
  },
  {
    id: 'publish:github:pull-request',
    input: { repoUrl: REPO, branchName: 'change', title: 'Change' },
  },
  { id: 'github:release:create', input: { repoUrl: REPO, tagName: 'v1.0.0' } },
];

describe('GitHub actions do not use the backend integration credential when user credentials are required', () => {
  it.each(cases)(
    '$id refuses without a user token and never creates an authenticated client',
    async ({ id, input }) => {
      const actions = await loadActions(enabledConfig());
      const action = actions.find(candidate => candidate.id === id);
      expect(action).toBeDefined();

      const error = await runHandler(action, input);

      expect(octokitMock.__calls).toHaveLength(0);
      expect(error).toBeInstanceOf(InputError);
    },
  );

  it('publish:github treats an empty user token as no user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(
      candidate => candidate.id === 'publish:github',
    );

    const error = await runHandler(action, { repoUrl: REPO, token: '' });

    expect(octokitMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });

  it('github:issues:create treats an empty user token as no user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(
      candidate => candidate.id === 'github:issues:create',
    );

    const error = await runHandler(action, {
      repoUrl: REPO,
      title: 'Issue',
      token: '',
    });

    expect(octokitMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });

  it('publish:github:pull-request treats an empty user token as no user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(
      candidate => candidate.id === 'publish:github:pull-request',
    );

    const error = await runHandler(action, {
      repoUrl: REPO,
      branchName: 'change',
      title: 'Change',
      token: '',
    });

    expect(octokitMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });

  it('github:release:create treats an empty user token as no user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(
      candidate => candidate.id === 'github:release:create',
    );

    const error = await runHandler(action, {
      repoUrl: REPO,
      tagName: 'v1.0.0',
      token: '',
    });

    expect(octokitMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });

  it('github:issues:create refuses when the integration entry has no token', async () => {
    const action = createGithubIssuesCreateAction({
      integrations: ScmIntegrations.fromConfig(
        new ConfigReader({ integrations: { github: [{ host: 'github.com' }] } }),
      ),
      // The setting alone must forbid the operation; a credential the provider
      // could otherwise fall back to must not be used.
      githubCredentialsProvider: {
        getCredentials: async () => ({ token: 'provider-fallback-token' }),
      } as any,
      requireScmUserCredentials: true,
    } as any);

    const error = await runHandler(action, { repoUrl: REPO, title: 'Issue' });

    expect(octokitMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });
});
