import { createMockServer } from '@nocobase/test';
import fs from 'fs';
import fsp from 'fs/promises';
import os from 'os';
import path from 'path';

const MARKER_VERSION = '9.9.9-VERIFY-MARKER';

async function makeMarkerModule(dir: string) {
  const dirPath = await fsp.mkdtemp(path.join(dir, 'module-'));
  const marker = path.join(dirPath, 'loaded.txt');
  const modulePath = path.join(dirPath, 'entry.js');
  await fsp.writeFile(
    modulePath,
    `const fs = require('fs');\nfs.writeFileSync(${JSON.stringify(marker)}, 'loaded');\nmodule.exports = function Entry() {};\n`,
  );
  return { dirPath, marker, modulePath };
}

describe('plugin identifier confinement', () => {
  let app: any;
  let agent: any;
  let tmp: string;

  beforeAll(async () => {
    tmp = await fsp.mkdtemp(path.join(os.tmpdir(), 'nb-verify-pm-'));
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

  it('does not load code from a filesystem location used as a plugin name', async () => {
    const { marker, modulePath } = await makeMarkerModule(tmp);
    try {
      await app.pm.enable(modulePath);
    } catch (error) {
      // a refusal is expected; the observable requirement is the absence of the load
    }
    expect(fs.existsSync(marker)).toBe(false);
  });

  it('does not load code from a filesystem location given to the plugin command', async () => {
    const { marker, modulePath } = await makeMarkerModule(tmp);
    try {
      await app.runAsCLI(['pm', 'enable', modulePath], { from: 'user', throwError: true });
    } catch (error) {
      // a refusal is expected; the observable requirement is the absence of the load
    }
    expect(fs.existsSync(marker)).toBe(false);
  });

  it('does not delete a directory named as a plugin', async () => {
    const dirPath = await fsp.mkdtemp(path.join(tmp, 'delete-'));
    const keep = path.join(dirPath, 'keep.txt');
    await fsp.writeFile(keep, 'keep');
    try {
      await app.pm.remove(dirPath);
    } catch (error) {
      // a refusal is expected; the observable requirement is that nothing was removed
    }
    expect(fs.existsSync(dirPath)).toBe(true);
    expect(fs.existsSync(keep)).toBe(true);
  });

  it('does not read package metadata from a location outside the plugin packages', async () => {
    const dirPath = await fsp.mkdtemp(path.join(tmp, 'info-'));
    await fsp.writeFile(
      path.join(dirPath, 'package.json'),
      JSON.stringify({ name: 'outside-package', version: MARKER_VERSION }),
    );
    let response: any;
    try {
      response = await agent.resource('pm').info({ values: { packageName: dirPath } });
    } catch (error) {
      response = undefined;
    }
    expect(JSON.stringify(response?.body ?? {})).not.toContain(MARKER_VERSION);
  });
});
