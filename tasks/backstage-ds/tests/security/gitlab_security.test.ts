/*
 * Hidden security tests: GitLab scaffolder credential fallback.
 *
 * Actions come from the real GitLab module init with the root config; the
 * GitLab client library is mocked so that any construction records the
 * credential it would authenticate with.
 */
import { InputError } from '@backstage/errors';
import { ConfigReader } from '@backstage/config';
import { createMockActionContext } from '@backstage/plugin-scaffolder-node-test-utils';
import { gitlabModule } from '../module';
import { Gitlab } from '@gitbeaker/rest';

jest.mock('@gitbeaker/rest', () => {
  const calls: any[] = [];
  const ctor: any = jest.fn((options: any) => {
    calls.push(options);
    // A working client so an implementation that proceeds with a user
    // credential can complete; the recorded construction is what matters.
    return {
      ProjectMembers: {
        add: jest.fn().mockResolvedValue({}),
        show: jest.fn().mockResolvedValue({ username: 'someone' }),
      },
    };
  });
  ctor.__calls = calls;
  return { Gitlab: ctor };
});

const gitlabMock: any = Gitlab;

function enabledConfig() {
  return new ConfigReader({
    scaffolder: { requireScmUserCredentials: true },
    integrations: {
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

async function loadActions(config: ConfigReader): Promise<any[]> {
  const actions: any[] = [];
  const registration = (gitlabModule as any).getRegistrations()[0];
  await registration.init.func({
    scaffolder: {
      addActions: (...added: any[]) => actions.push(...added),
    },
    config,
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
  gitlabMock.__calls.length = 0;
});

const REPO = 'gitlab.com?repo=example&owner=acme';

const cases: Array<{ id: string; input: Record<string, unknown> }> = [
  { id: 'publish:gitlab', input: { repoUrl: REPO } },
  { id: 'gitlab:group:ensureExists', input: { repoUrl: REPO, path: 'acme' } },
  {
    id: 'gitlab:group:access',
    input: { repoUrl: REPO, path: 'acme', userIds: [1] },
  },
  {
    id: 'gitlab:issues:create',
    input: { repoUrl: REPO, projectId: 1, title: 'Issue' },
  },
  {
    id: 'gitlab:issue:edit',
    input: { repoUrl: REPO, projectId: 1, issueIid: 1 },
  },
  { id: 'gitlab:pipeline:trigger', input: { repoUrl: REPO, projectId: 1 } },
  {
    id: 'gitlab:projectAccessToken:create',
    input: { repoUrl: REPO, projectId: 1 },
  },
  {
    id: 'gitlab:projectDeployToken:create',
    input: {
      repoUrl: REPO,
      projectId: 1,
      name: 'deploy token',
      scopes: ['read_repository'],
    },
  },
  {
    id: 'gitlab:projectVariable:create',
    input: { repoUrl: REPO, projectId: 1, key: 'KEY', value: 'value' },
  },
  {
    id: 'publish:gitlab:merge-request',
    input: {
      repoUrl: REPO,
      title: 'Change',
      branchName: 'change',
      targetBranchName: 'main',
    },
  },
  {
    id: 'gitlab:repo:push',
    input: { repoUrl: REPO, branchName: 'change' },
  },
  {
    id: 'gitlab:projectMember:create',
    input: { repoUrl: REPO, userId: 2 },
  },
  { id: 'gitlab:user:info', input: { repoUrl: REPO } },
  {
    id: 'gitlab:group:migrate',
    input: {
      destinationAccessToken: '',
      destinationUrl: REPO,
      sourceAccessToken: 'source-token',
      sourceFullPath: 'acme/example',
      sourceUrl: 'https://gitlab.com/',
    },
  },
];

describe('GitLab actions do not use the backend integration credential when user credentials are required', () => {
  it.each(cases)(
    '$id refuses without a user token and never creates an authenticated client',
    async ({ id, input }) => {
      const actions = await loadActions(enabledConfig());
      const action = actions.find(candidate => candidate.id === id);
      expect(action).toBeDefined();

      const error = await runHandler(action, input);

      expect(gitlabMock.__calls).toHaveLength(0);
      expect(error).toBeInstanceOf(InputError);
    },
  );

  it('publish:gitlab treats an empty user token as no user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(candidate => candidate.id === 'publish:gitlab');

    const error = await runHandler(action, { repoUrl: REPO, token: '' });

    expect(gitlabMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });

  it('gitlab:issues:create treats an empty user token as no user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(
      candidate => candidate.id === 'gitlab:issues:create',
    );

    const error = await runHandler(action, {
      repoUrl: REPO,
      projectId: 1,
      title: 'Issue',
      token: '',
    });

    expect(gitlabMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });

  it('gitlab:projectAccessToken:create treats an empty user token as no user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(
      candidate => candidate.id === 'gitlab:projectAccessToken:create',
    );

    const error = await runHandler(action, {
      repoUrl: REPO,
      projectId: 1,
      name: 'access token',
      scopes: ['api'],
      token: '',
    });

    expect(gitlabMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });

  it('gitlab:repo:push treats an empty user token as no user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(
      candidate => candidate.id === 'gitlab:repo:push',
    );

    const error = await runHandler(action, {
      repoUrl: REPO,
      branchName: 'change',
      token: '',
    });

    expect(gitlabMock.__calls).toHaveLength(0);
    expect(error).toBeInstanceOf(InputError);
  });

  it('gitlab:projectMember:create never re-resolves the backend integration credential when a user token is given', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(
      candidate => candidate.id === 'gitlab:projectMember:create',
    );

    const error = await runHandler(action, {
      repoUrl: REPO,
      userId: 2,
      token: 'user-token',
    });

    // The step may proceed with the user's credential, but no operation it
    // performs may authenticate with the instance integration credential.
    expect(error).toBeUndefined();
    const integrationCalls = gitlabMock.__calls.filter(
      (call: any) =>
        call.token === 'backend-integration-token' ||
        call.oauthToken === 'backend-integration-token',
    );
    expect(integrationCalls).toHaveLength(0);
    expect(gitlabMock.__calls.length).toBeGreaterThan(0);
  });

  it('publish:gitlab refuses the privileged ownership assignment with a user token', async () => {
    const actions = await loadActions(enabledConfig());
    const action = actions.find(candidate => candidate.id === 'publish:gitlab');

    const setUserAsOwnerError = await runHandler(action, {
      repoUrl: REPO,
      token: 'user-oauth-token',
      setUserAsOwner: true,
    });
    expect(gitlabMock.__calls).toHaveLength(0);
    expect(setUserAsOwnerError).toBeInstanceOf(InputError);

    const ownerUsernameError = await runHandler(action, {
      repoUrl: REPO,
      token: 'user-oauth-token',
      ownerUsername: 'someone',
    });
    expect(gitlabMock.__calls).toHaveLength(0);
    expect(ownerUsernameError).toBeInstanceOf(InputError);
  });
});
