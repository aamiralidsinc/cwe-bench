import { createMockServer } from '@nocobase/test';
import fsp from 'fs/promises';
import os from 'os';
import path from 'path';

describe('plugin management legitimate use', () => {
  let app: any;
  let agent: any;
  let tmp: string;

  beforeAll(async () => {
    tmp = await fsp.mkdtemp(path.join(os.tmpdir(), 'nb-verify-pm-fn-'));
  });

  afterAll(async () => {
    await fsp.rm(tmp, { recursive: true, force: true });
  });

  beforeEach(async () => {
    app = await createMockServer({ plugins: ['field-sort', 'users', 'auth'] });
    agent = app.agent();
    app.tryReloadOrRestart = async () => undefined;
  }, 120000);

  afterEach(async () => {
    await app.destroy();
  });

  it('enables an installed plugin by its name', async () => {
    await app.pm.enable('users');
    const plugin = app.pm.get('users');
    expect(plugin).toBeTruthy();
    expect(plugin.enabled).toBe(true);
  });

  it('reads package metadata for an installed plugin package', async () => {
    const response = await agent.resource('pm').info({
      values: { packageName: '@nocobase/plugin-users' },
    });
    expect(response.status).toBe(200);
    expect(response.body.data.name).toBe('@nocobase/plugin-users');
  });
});
