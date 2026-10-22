// Ordinary use of the Azure Blob media handlers: upload into a directory,
// delete a blob by the name it was stored under, and list the root / a
// directory.
import { beforeEach, describe, expect, it } from 'vitest';
import { createMediaHandlers } from '@app/packages/next-tinacms-azure/src/handlers';
import { state as azure } from '../support/stubs/azure-blob';
import { resetStubs } from '../support/harness';

function handlers() {
  return createMediaHandlers({
    connectionString: 'UseDevelopmentStorage=true',
    containerName: 'media',
    authorized: async () => true,
  } as any);
}

function upload(directory: string, filename = 'a.png') {
  const form = new FormData();
  form.set('directory', directory);
  form.set('filename', filename);
  form.set('file', new Blob(['DATA'], { type: 'image/png' }));
  return handlers().POST({ formData: async () => form } as any);
}

function remove(media: any[]) {
  return handlers().DELETE({} as any, { params: { media } } as any);
}

function list(directory?: string) {
  const url = directory
    ? `http://localhost/api/media?directory=${encodeURIComponent(directory)}`
    : 'http://localhost/api/media';
  return handlers().GET({ nextUrl: new URL(url) } as any);
}

beforeEach(resetStubs);

describe('legitimate Azure Blob use', () => {
  it('uploads a file into a directory', async () => {
    const res: any = await upload('photos');
    expect(res.status).toBe(200);
    expect(azure.uploads.map((entry) => entry.name)).toEqual(['photos/a.png']);
    expect(res.body.filename).toBe('a.png');
  });

  it('deletes a blob by name', async () => {
    const res: any = await remove(['media', 'photos/a.png']);
    expect(res.status).toBe(200);
    expect(azure.deletes).toEqual(['photos/a.png']);
  });

  it('lists the root', async () => {
    const res: any = await list();
    expect(res.status).toBe(200);
    expect(azure.prefixes).toEqual(['']);
  });

  it('lists a directory', async () => {
    const res: any = await list('photos');
    expect(res.status).toBe(200);
    expect(azure.prefixes).toEqual(['photos/']);
  });
});
