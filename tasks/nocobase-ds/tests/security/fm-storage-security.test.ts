import { createMockServer } from '@nocobase/test';
import fs from 'fs';
import fsp from 'fs/promises';
import os from 'os';
import path from 'path';
import PluginFileManagerServer from '../../server';

const LOCAL_ROOT = () => path.join(process.cwd(), 'storage', 'uploads');
const outsideDir = () => fsp.mkdtemp(path.join(os.tmpdir(), 'nb-verify-fm-'));
const attachmentInput = () => path.join(process.env.NB_VERIFY_TMP as string, 'upload.txt');

async function readNames(dir: string) {
  try {
    return await fsp.readdir(dir);
  } catch (error: any) {
    if (error?.code === 'ENOENT') {
      return [];
    }
    throw error;
  }
}

async function removeUploaded(body: any) {
  const filename = body?.data?.filename;
  if (!filename) {
    return;
  }
  await fsp.rm(path.join(LOCAL_ROOT(), filename), { force: true }).catch(() => undefined);
}

describe('file storage confinement', () => {
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

  it('does not write outside the managed area when a submitted storage root changes on update', async () => {
    const outside = await outsideDir();
    try {
      await agent.resource('storages').update({
        filterByTk: defaultStorage.id,
        values: { options: { documentRoot: outside, baseUrl: '/storage/uploads' } },
      });
      const upload = await agent.resource('attachments').create({ file: attachmentInput() });
      expect(await readNames(outside)).toEqual([]);
      await removeUploaded(upload.body);
    } finally {
      await fsp.rm(outside, { recursive: true, force: true });
    }
  });

  it('does not write outside the managed area when a submitted storage root is created', async () => {
    const outside = await outsideDir();
    const storageName = 'verify_create_route';
    try {
      await agent.resource('storages').create({
        values: {
          name: storageName,
          type: 'local',
          baseUrl: '/verify-create',
          options: { documentRoot: outside },
        },
      });
      db.collection({
        name: 'verifyCreateFiles',
        fields: [{ name: 'file', type: 'belongsTo', target: 'attachments', storage: storageName }],
      });
      await agent.resource('attachments').create({
        attachmentField: 'verifyCreateFiles.file',
        file: attachmentInput(),
      });
      expect(await readNames(outside)).toEqual([]);
    } finally {
      await fsp.rm(outside, { recursive: true, force: true });
    }
  });

  it('does not write outside the managed area for a relative storage root that leaves it', async () => {
    const outside = await outsideDir();
    try {
      const relativeRoot = path.relative(process.cwd(), outside);
      await agent.resource('storages').update({
        filterByTk: defaultStorage.id,
        values: { options: { documentRoot: relativeRoot, baseUrl: '/storage/uploads' } },
      });
      const upload = await agent.resource('attachments').create({ file: attachmentInput() });
      expect(await readNames(outside)).toEqual([]);
      await removeUploaded(upload.body);
    } finally {
      await fsp.rm(outside, { recursive: true, force: true });
    }
  });

  it('does not create a directory outside the managed area for a stored path that leaves it', async () => {
    const outside = await outsideDir();
    const escaped = path.join(outside, 'escaped');
    try {
      const cached: any = plugin.storagesCache.get(defaultStorage.id);
      cached.path = path.relative(LOCAL_ROOT(), escaped);
      await agent.resource('attachments').create({ file: attachmentInput() });
      expect(fs.existsSync(escaped)).toBe(false);
    } finally {
      await fsp.rm(outside, { recursive: true, force: true });
    }
  });

  it('does not write outside the managed area when a root is supplied through the create-or-update route', async () => {
    const outside = await outsideDir();
    try {
      await agent.resource('storages').updateOrCreate({
        values: {
          id: defaultStorage.id,
          name: defaultStorage.name,
          type: 'local',
          baseUrl: '/storage/uploads',
          options: { documentRoot: outside, baseUrl: '/storage/uploads' },
        },
        filterKeys: ['id'],
      });
      const upload = await agent.resource('attachments').create({ file: attachmentInput() });
      expect(await readNames(outside)).toEqual([]);
      await removeUploaded(upload.body);
    } finally {
      await fsp.rm(outside, { recursive: true, force: true });
    }
  });

  it('does not write outside the managed area when a root is supplied through the first-or-create route', async () => {
    const outside = await outsideDir();
    const storageName = 'verify_first_route';
    try {
      await agent.resource('storages').firstOrCreate({
        values: {
          name: storageName,
          type: 'local',
          baseUrl: '/verify-first',
          options: { documentRoot: outside },
        },
        filterKeys: ['name'],
      });
      db.collection({
        name: 'verifyFirstFiles',
        fields: [{ name: 'file', type: 'belongsTo', target: 'attachments', storage: storageName }],
      });
      await agent.resource('attachments').create({
        attachmentField: 'verifyFirstFiles.file',
        file: attachmentInput(),
      });
      expect(await readNames(outside)).toEqual([]);
    } finally {
      await fsp.rm(outside, { recursive: true, force: true });
    }
  });

  it('does not use a root that was submitted while the storage was another type', async () => {
    const outside = await outsideDir();
    try {
      await agent.resource('storages').update({
        filterByTk: defaultStorage.id,
        values: { type: 's3', options: { documentRoot: outside, baseUrl: '/storage/uploads' } },
      });
      await agent.resource('storages').update({
        filterByTk: defaultStorage.id,
        values: { type: 'local' },
      });
      const upload = await agent.resource('attachments').create({ file: attachmentInput() });
      expect(await readNames(outside)).toEqual([]);
      await removeUploaded(upload.body);
    } finally {
      await fsp.rm(outside, { recursive: true, force: true });
    }
  });

  it('does not write a probe file outside the managed area', async () => {
    const outside = await outsideDir();
    try {
      await agent.resource('storages').probe({
        filterByTk: defaultStorage.name,
        values: { documentRoot: outside, path: 'probe-out' },
      });
      expect(fs.existsSync(path.join(outside, 'probe-out'))).toBe(false);
    } finally {
      await fsp.rm(outside, { recursive: true, force: true });
    }
  });
});
