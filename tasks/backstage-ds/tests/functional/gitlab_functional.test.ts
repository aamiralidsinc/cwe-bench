/*
 * Hidden functional tests: the GitLab module keeps its existing credential
 * behaviour in the default configuration and accepts user tokens when the
 * setting is enabled.
 */
import { ConfigReader } from '@backstage/config';
import { createMockActionContext } from '@backstage/plugin-scaffolder-node-test-utils';
import { gitlabModule } from '../module';
import { Gitlab } from '@gitbeaker/rest';

jest.mock('@gitbeaker/rest', () => {
  const calls: any[] = [];
  const add = jest.fn().mockResolvedValue({});
  const createDeployToken = jest
    .fn()
    .mockResolvedValue({ token: 'deploy-token', username: 'deploy-user' });
  const ctor: any = jest.fn((options: any) => {
    calls.push(options);
    return {
      DeployTokens: { create: createDeployToken },
      ProjectMembers: {
        add,
        show: jest.fn().mockResolvedValue({ username: 'someone' }),
      },
      Repositories: {
        allRepositoryTrees: jest.fn().mockResolvedValue([]),
      },
      Branches: { show: jest.fn().mockResolvedValue({}) },
      Commits: { create: jest.fn().mockResolvedValue({ id: 'abc123' }) },
    };
  });
  ctor.__calls = calls;
  return { Gitlab: ctor };
});

const gitlabMock: any = Gitlab;

function config(requireCredentials: boolean) {
  return new ConfigReader({
    ...(requireCredentials
      ? { scaffolder: { requireScmUserCredentials: true } }
      : {}),
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

async function loadAction(
  requireCredentials: boolean,
  id: string,
): Promise<any> {
  const actions: any[] = [];
  const registration = (gitlabModule as any).getRegistrations()[0];
  await registration.init.func({
    scaffolder: { addActions: (...added: any[]) => actions.push(...added) },
    config: config(requireCredentials),
    autocomplete: { addAutocompleteProvider: () => {} },
  });
  return actions.find(candidate => candidate.id === id);
}

const REPO = 'gitlab.com?repo=example&owner=acme';

// The user credential must reach the client and the backend integration
// credential must not, whichever field the implementation chooses.
function expectUserTokenOnly(call: any) {
  expect(call.oauthToken ?? call.token).toBe('user-token');
  expect(call.oauthToken).not.toBe('backend-integration-token');
  expect(call.token).not.toBe('backend-integration-token');
}

beforeEach(() => {
  gitlabMock.__calls.length = 0;
});

describe('GitLab module credential selection', () => {
  it('uses the integration credential by default when no user token is given', async () => {
    const action = await loadAction(false, 'gitlab:projectDeployToken:create');

    await action.handler(
      createMockActionContext({
        input: {
          repoUrl: REPO,
          projectId: 1,
          name: 'deploy token',
          scopes: ['read_repository'],
        },
      }),
    );

    expect(gitlabMock.__calls).toHaveLength(1);
    expect(gitlabMock.__calls[0].token).toBe('backend-integration-token');
  });

  it('uses the user token when one is given and the setting is enabled', async () => {
    const action = await loadAction(true, 'gitlab:projectDeployToken:create');

    await action.handler(
      createMockActionContext({
        input: {
          repoUrl: REPO,
          projectId: 1,
          name: 'deploy token',
          scopes: ['read_repository'],
          token: 'user-token',
        },
      }),
    );

    expect(gitlabMock.__calls).toHaveLength(1);
    expectUserTokenOnly(gitlabMock.__calls[0]);
  });

  it('keeps the integration fallback for the project member action by default', async () => {
    const action = await loadAction(false, 'gitlab:projectMember:create');

    await action.handler(
      createMockActionContext({ input: { repoUrl: REPO, userId: 2 } }),
    );

    expect(gitlabMock.__calls.length).toBeGreaterThan(0);
    for (const call of gitlabMock.__calls) {
      expect(call.token).toBe('backend-integration-token');
    }
  });

  it('uses the user token for the project member action when the setting is enabled', async () => {
    const action = await loadAction(true, 'gitlab:projectMember:create');
    const ctx = createMockActionContext({
      input: { repoUrl: REPO, userId: 2, token: 'user-token' },
    });

    await action.handler(ctx);

    // The operation itself must act as the user; the step still reports its
    // result.
    expectUserTokenOnly(gitlabMock.__calls[0]);
    expect(ctx.output).toHaveBeenCalledWith('username', 'someone');
  });

  it('keeps the integration fallback for the repo push action by default', async () => {
    const action = await loadAction(false, 'gitlab:repo:push');

    await action.handler(
      createMockActionContext({
        input: { repoUrl: REPO, branchName: 'change' },
      }),
    );

    expect(gitlabMock.__calls).toHaveLength(1);
    expect(gitlabMock.__calls[0].token).toBe('backend-integration-token');
  });

  it('uses the user token for the repo push action when the setting is enabled', async () => {
    const action = await loadAction(true, 'gitlab:repo:push');

    await action.handler(
      createMockActionContext({
        input: { repoUrl: REPO, branchName: 'change', token: 'user-token' },
      }),
    );

    expect(gitlabMock.__calls).toHaveLength(1);
    expectUserTokenOnly(gitlabMock.__calls[0]);
  });
});
