// The Azure Blob media handlers (app-router style). This adapter has no
// media-root option, but a caller-supplied key must still be relative and must
// never climb above the container area it serves.
import { beforeEach, describe, it } from 'vitest';
import { createMediaHandlers } from '@app/packages/next-tinacms-azure/src/handlers';
import { state as azure } from '../support/stubs/azure-blob';
import { resetStubs, expectRefused } from '../support/harness';

function handlers() {
  return createMediaHandlers({
    connectionString: 'UseDevelopmentStorage=true',
    containerName: 'media',
    authorized: async () => true,
  } as any);
}

function formRequest(fields: Record<string, any>) {
  const form = new FormData();
  for (const [name, value] of Object.entries(fields)) {
    form.set(name, value as any);
  }
  return { formData: async () => form } as any;
}

async function upload(directory: string, filename = 'a.png') {
  return handlers().POST(
    formRequest({
      directory,
      filename,
      file: new Blob(['DATA'], { type: 'image/png' }),
    })
  );
}

async function remove(media: any[]) {
  return handlers().DELETE({} as any, { params: { media } } as any);
}

async function list(directory: string) {
  return handlers().GET({
    nextUrl: new URL(`http://localhost/api/media?directory=${encodeURIComponent(directory)}`),
  } as any);
}

beforeEach(resetStubs);

describe('azure blob upload is confined to the served area', () => {
  it('refuses a directory that walks upward', async () => {
    const res = await upload('../outside');
    expectRefused(res, azure.uploads);
  });

  it('refuses an inner climb that leaves the area', async () => {
    const res = await upload('a/../../../outside');
    expectRefused(res, azure.uploads);
  });

  it('refuses an absolute directory', async () => {
    const res = await upload('/etc');
    expectRefused(res, azure.uploads);
  });

  it('refuses a windows-style separator', async () => {
    const res = await upload('..\\outside');
    expectRefused(res, azure.uploads);
  });

  it('refuses a bare parent directory', async () => {
    const res = await upload('..');
    expectRefused(res, azure.uploads);
  });
});

describe('azure blob delete is confined to the served area', () => {
  it('refuses a blob name that walks upward', async () => {
    const res = await remove(['media', '../secret.png']);
    expectRefused(res, azure.deletes);
  });

  it('refuses an absolute blob name', async () => {
    const res = await remove(['media', '/etc/passwd']);
    expectRefused(res, azure.deletes);
  });

  it('refuses an empty blob name', async () => {
    const res = await remove(['media', '']);
    expectRefused(res, azure.deletes);
  });
});

describe('azure blob listing is confined to the served area', () => {
  it('refuses a directory that walks upward', async () => {
    const res = await list('../');
    expectRefused(res, azure.prefixes);
  });

  it('refuses a leading-slash traversal directory', async () => {
    const res = await list('/../x');
    expectRefused(res, azure.prefixes);
  });

  it('refuses a windows-style separator', async () => {
    const res = await list('..\\outside');
    expectRefused(res, azure.prefixes);
  });
});
