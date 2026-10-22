// In-memory stand-in for @azure/storage-blob. Blob writes, deletes and list
// prefixes are recorded so the tests can assert which blob names reached the
// service.

export const state = {
  uploads: [] as Array<{ name: string; size: number }>,
  deletes: [] as string[],
  prefixes: [] as string[],
  blobs: [] as any[],
  reset() {
    this.uploads = [];
    this.deletes = [];
    this.prefixes = [];
    this.blobs = [];
  },
};

class StubBlockBlobClient {
  constructor(public name: string) {}
  async uploadData(buffer: any) {
    state.uploads.push({ name: this.name, size: buffer?.length ?? 0 });
  }
  async deleteIfExists(_options?: any) {
    state.deletes.push(this.name);
    return { succeeded: true };
  }
}

class StubContainerClient {
  getBlockBlobClient(name: string) {
    return new StubBlockBlobClient(name);
  }
  listBlobsByHierarchy(_delimiter: string, options?: { prefix?: string }) {
    state.prefixes.push(options?.prefix ?? '');
    const blobs = state.blobs;
    return {
      [Symbol.asyncIterator]: async function* () {
        for (const blob of blobs) {
          yield blob;
        }
      },
    };
  }
}

export class BlobServiceClient {
  constructor(public connectionString: string) {}
  static fromConnectionString(connectionString: string) {
    return new BlobServiceClient(connectionString);
  }
  getContainerClient(_name: string) {
    return new StubContainerClient();
  }
}
