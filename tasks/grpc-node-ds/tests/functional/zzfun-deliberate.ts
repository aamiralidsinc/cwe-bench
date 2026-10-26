import * as assert from 'assert';
import * as grpc from '../src';
import {
  CallOutcome,
  RunningServer,
  callBidi,
  callClientStream,
  callServerStream,
  callUnary,
  identity,
  makeClient,
  startServer,
} from './zzsupport';

const PLAIN = 'DELIBERATE_PLAIN_b81f4a';
const STATUS = 'DELIBERATE_STATUS_c27d93';
const CLIENT_STREAM = 'DELIBERATE_CLIENT_STREAM_e4a6b2';
const SERVER_STREAM = 'DELIBERATE_SERVER_STREAM_d93c17';
const BIDI = 'DELIBERATE_BIDI_6af028';

const definition = {
  unary: {
    path: '/TestService/Unary',
    requestStream: false,
    responseStream: false,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  },
  clientStream: {
    path: '/TestService/ClientStream',
    requestStream: true,
    responseStream: false,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  },
  serverStream: {
    path: '/TestService/ServerStream',
    requestStream: false,
    responseStream: true,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  },
  bidi: {
    path: '/TestService/Bidi',
    requestStream: true,
    responseStream: true,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  },
};

function trailer(): grpc.Metadata {
  const metadata = new grpc.Metadata();
  metadata.add('x-trailer', 'kept');
  return metadata;
}

const implementation = {
  unary(call: any, callback: any) {
    const request = String(call.request);
    if (request === 'plain') {
      callback(new Error(PLAIN));
    } else if (request === 'status') {
      callback({
        code: grpc.status.NOT_FOUND,
        details: STATUS,
        metadata: trailer(),
      });
    } else {
      callback(null, Buffer.from('ok'));
    }
  },
  clientStream(stream: any, callback: any) {
    stream.on('data', () => {
      /* drain */
    });
    stream.on('end', () => {
      callback(new Error(CLIENT_STREAM));
    });
  },
  serverStream(stream: any) {
    stream.emit('error', {
      code: grpc.status.NOT_FOUND,
      details: SERVER_STREAM,
      metadata: trailer(),
    });
  },
  bidi(stream: any) {
    stream.on('data', () => {
      stream.emit('error', new Error(BIDI));
    });
    stream.on('end', () => {
      stream.end();
    });
  },
};

describe('deliberate error reports through the library API', () => {
  let ctx: RunningServer;

  before(async () => {
    ctx = await startServer(definition, implementation);
  });

  after(() => {
    ctx.shutdown();
  });

  function client(): any {
    return makeClient(definition, ctx.port);
  }

  it('delivers a plain error handed to the unary callback', async () => {
    const c = client();
    try {
      const outcome = await callUnary(c, 'unary', Buffer.from('plain'));
      assert(outcome.err);
      assert.strictEqual(outcome.err.code, grpc.status.UNKNOWN);
      assert.strictEqual(outcome.err.details, PLAIN);
    } finally {
      c.close();
    }
  }).timeout(10000);

  it('delivers a status handed to the unary callback with its trailers', async () => {
    const c = client();
    try {
      const outcome: CallOutcome = await callUnary(
        c,
        'unary',
        Buffer.from('status')
      );
      assert(outcome.err);
      assert.strictEqual(outcome.err.code, grpc.status.NOT_FOUND);
      assert.strictEqual(outcome.err.details, STATUS);
      assert.deepStrictEqual(outcome.err.metadata.get('x-trailer'), ['kept']);
    } finally {
      c.close();
    }
  }).timeout(10000);

  it('delivers an error handed to the client-stream callback', async () => {
    const c = client();
    try {
      const outcome = await callClientStream(c, 'clientStream');
      assert(outcome.err);
      assert.strictEqual(outcome.err.code, grpc.status.UNKNOWN);
      assert.strictEqual(outcome.err.details, CLIENT_STREAM);
    } finally {
      c.close();
    }
  }).timeout(10000);

  it('delivers a status emitted by a server-stream implementation', async () => {
    const c = client();
    try {
      const outcome = await callServerStream(c, 'serverStream');
      assert(outcome.err);
      assert.strictEqual(outcome.err.code, grpc.status.NOT_FOUND);
      assert.strictEqual(outcome.err.details, SERVER_STREAM);
      assert.deepStrictEqual(outcome.err.metadata.get('x-trailer'), ['kept']);
    } finally {
      c.close();
    }
  }).timeout(10000);

  it('delivers an error emitted by a bidi implementation', async () => {
    const c = client();
    try {
      const outcome = await callBidi(c, 'bidi');
      assert(outcome.err);
      assert.strictEqual(outcome.err.code, grpc.status.UNKNOWN);
      assert.strictEqual(outcome.err.details, BIDI);
    } finally {
      c.close();
    }
  }).timeout(10000);
});
