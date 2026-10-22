// In-memory stand-in for @aws-sdk/client-s3. Every command sent by the
// handlers under test is recorded so a test can assert which object keys
// actually reached the storage client.

export interface SentCommand {
  kind: string;
  input: any;
}

export const s3 = {
  sent: [] as SentCommand[],
  presigns: [] as Array<{ bucket: string; key: string; expiresIn: number }>,
  headStatus: 404,
  listResult: null as any,
  reset() {
    this.sent = [];
    this.presigns = [];
    this.headStatus = 404;
    this.listResult = null;
  },
};

export class ListObjectsCommand {
  readonly kind = 'ListObjects';
  constructor(public input: any) {}
}
export class PutObjectCommand {
  readonly kind = 'PutObject';
  constructor(public input: any) {}
}
export class DeleteObjectCommand {
  readonly kind = 'DeleteObject';
  constructor(public input: any) {}
}
export class DeleteObjectsCommand {
  readonly kind = 'DeleteObjects';
  constructor(public input: any) {}
}
export class CopyObjectCommand {
  readonly kind = 'CopyObject';
  constructor(public input: any) {}
}
export class HeadObjectCommand {
  readonly kind = 'HeadObject';
  constructor(public input: any) {}
}

export class S3Client {
  constructor(public config: any) {}

  async send(command: any) {
    s3.sent.push({ kind: command.kind, input: command.input });
    if (command instanceof HeadObjectCommand) {
      const error: any = new Error('not found');
      error.$metadata = { httpStatusCode: s3.headStatus };
      throw error;
    }
    if (command instanceof ListObjectsCommand) {
      return (
        s3.listResult ?? {
          Contents: [],
          CommonPrefixes: [],
          NextMarker: undefined,
        }
      );
    }
    return {};
  }
}
