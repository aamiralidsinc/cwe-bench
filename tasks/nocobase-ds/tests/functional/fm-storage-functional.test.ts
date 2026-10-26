import { createMockServer } from '@nocobase/test';
import fs from 'fs';
import fsp from 'fs/promises';
import os from 'os';
import path from 'path';
import PluginFileManagerServer from '../../server';

const LOCAL_ROOT = () => path.join(process.cwd(), 'storage', 'uploads');
const outsideDir = () => fsp.mkdtemp(path.join(os.tmpdir(), 'nb-verify-ext-'));
const attachmentInput = () => path.join(process.env.NB_VERIFY_TMP as string, 'upload.txt');

describe('file storage legitimate use', () => {
  let app: any;
  let agent: any;
  let db: any;
  let plugin: PluginFileManagerServer;
  let defaultStorage: any;
  let tmp: string;

  beforeAll(async () => {
    tmp = await fsp.mkdtemp(path.join(os.tmpdir(), 'nb-verify-input-'));
    process.env.NB_VERIFY_TMP = tmp;
    await fsp.writeFile(attachmentInput(), 'Hello world!');
  });

  afterAll(async () => {
    await fsp.rm(tmp, { recursive: true, force: true });
    delete process.env.NB_VERIFY_TMP;
  });

  beforeEach(async () => {
    app = await createMockServer({
      cors: { origin: '*' },
      plugins: ['field-sort', 'users', 'auth', 'file-manager'],
    });
    agent = app.agent();
    db = app.db;
    plugin = app.pm.get(PluginFileManagerServer) as PluginFileManagerServer;
    defaultStorage = await db.getRepository('storages').findOne();
  }, 120000);

  afterEach(async () => {
    await app.destroy();
  });

  function bindStorageCollection(collectionName: string, fieldName: string, storageName: string) {
    db.collection({
      name: collectionName,
      fields: [{ name: fieldName, type: 'belongsTo', target: 'attachments', storage: storageName }],
    });
  }

  it('uploads to the default local storage', async () => {
    const response = await agent.resource('attachments').create({ file: attachmentInput() });
    expect(response.status).toBe(200);
    const filename = response.body.data.filename;
    const expected = path.join(LOCAL_ROOT(), filename);
    expect(fs.existsSync(expected)).toBe(true);
    await fsp.rm(expected, { force: true });
  });

  it('uploads under a configured storage sub-path', async () => {
    const storageName = 'verify_sub_path';
    await db.getRepository('storages').create({
      values: {
        name: storageName,
        type: 'local',
        path: 'team/files',
        baseUrl: '/verify-sub',
        rules: { mimetype: ['text/*'] },
        options: { documentRoot: 'storage/uploads' },
      },
    });
    bindStorageCollection('verifySubFiles', 'file', storageName);
    const response = await agent.resource('attachments').create({
      attachmentField: 'verifySubFiles.file',
      file: attachmentInput(),
    });
    expect(response.status).toBe(200);
    const expected = path.join(LOCAL_ROOT(), 'team', 'files', response.body.data.filename);
    expect(fs.existsSync(expected)).toBe(true);
    await fsp.rm(path.join(LOCAL_ROOT(), 'team'), { recursive: true, force: true });
  });

  it('normalises leading and trailing slashes in a storage sub-path', async () => {
    const storageName = 'verify_slash_path';
    await db.getRepository('storages').create({
      values: {
        name: storageName,
        type: 'local',
        path: '/verify/path//',
        baseUrl: '/verify-slash',
        rules: { mimetype: ['text/*'] },
        options: { documentRoot: 'storage/uploads' },
      },
    });
    bindStorageCollection('verifySlashFiles', 'file', storageName);
    const response = await agent.resource('attachments').create({
      attachmentField: 'verifySlashFiles.file',
      file: attachmentInput(),
    });
    expect(response.status).toBe(200);
    const expected = path.join(LOCAL_ROOT(), 'verify', 'path', response.body.data.filename);
    expect(fs.existsSync(expected)).toBe(true);
    await fsp.rm(path.join(LOCAL_ROOT(), 'verify'), { recursive: true, force: true });
  });

  it('uploads to a trusted absolute root outside the application directory', async () => {
    const external = await outsideDir();
    const storageName = 'verify_external_root';
    try {
      await db.getRepository('storages').create({
        values: {
          name: storageName,
          type: 'local',
          path: 'trusted',
          baseUrl: '/verify-external',
          rules: { mimetype: ['text/*'] },
          options: { documentRoot: external },
        },
      });
      bindStorageCollection('verifyExternalFiles', 'file', storageName);
      const response = await agent.resource('attachments').create({
        attachmentField: 'verifyExternalFiles.file',
        file: attachmentInput(),
      });
      expect(response.status).toBe(200);
      const expected = path.join(external, 'trusted', response.body.data.filename);
      expect(fs.existsSync(expected)).toBe(true);
    } finally {
      await fsp.rm(external, { recursive: true, force: true });
    }
  });

  it('updates a storage sub-path without changing the root', async () => {
    const response = await agent.resource('storages').update({
      filterByTk: defaultStorage.id,
      values: { path: 'updated/sub' },
    });
    expect(response.status).toBe(200);
    const upload = await agent.resource('attachments').create({ file: attachmentInput() });
    expect(upload.status).toBe(200);
    const expected = path.join(LOCAL_ROOT(), 'updated', 'sub', upload.body.data.filename);
    expect(fs.existsSync(expected)).toBe(true);
    await fsp.rm(path.join(LOCAL_ROOT(), 'updated'), { recursive: true, force: true });
  });

  it('probes a storage under its configured root', async () => {
    const response = await agent.resource('storages').probe({
      filterByTk: defaultStorage.name,
      values: { path: 'probe-ok' },
    });
    expect(response.status).toBe(200);
    expect(fs.existsSync(path.join(LOCAL_ROOT(), 'probe-ok', '.nocobase-storage-probe'))).toBe(true);
    await fsp.rm(path.join(LOCAL_ROOT(), 'probe-ok'), { recursive: true, force: true });
  });
});
