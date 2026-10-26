import * as assert from 'assert';
import {
  CallOutcome,
  RunningServer,
  assertLeakBlocked,
  callBidi,
  callClientStream,
  callServerStream,
  callUnary,
  identity,
  makeClient,
  startServer,
} from './zzsupport';

const MARKER = 'HANDLER_EXCEPTION_7f3c9e';

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
  health: {
    path: '/TestService/Health',
    requestStream: false,
    responseStream: false,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  },
};

function throwing(message: string): never {
  throw new Error(message);
}

const implementation = {
  unary() {
    throwing(`${MARKER}: unary implementation failure`);
  },
  clientStream() {
    throwing(`${MARKER}: client-stream implementation failure`);
  },
  serverStream() {
    throwing(`${MARKER}: server-stream implementation failure`);
  },
  bidi() {
    throwing(`${MARKER}: bidi implementation failure`);
  },
  health(call: any, callback: any) {
    callback(null, Buffer.from('ok'));
  },
};

describe('unexpected exceptions in method implementations', () => {
  let ctx: RunningServer;

  before(async () => {
    ctx = await startServer(definition, implementation);
  });

  after(() => {
    ctx.shutdown();
  });

  async function verify(
    invoke: (client: any) => Promise<CallOutcome>
  ): Promise<void> {
    const client = makeClient(definition, ctx.port);
    try {
      const outcome = await invoke(client);
      assertLeakBlocked(outcome, MARKER);
      const health = await callUnary(client, 'health');
      assert.ifError(health.err);
      assert.strictEqual(String(health.value), 'ok');
    } finally {
      client.close();
    }
  }

  it('does not pass unary implementation text to the client', async () => {
    await verify(client => callUnary(client, 'unary'));
  }).timeout(10000);

  it('does not pass client-stream implementation text to the client', async () => {
    await verify(client => callClientStream(client, 'clientStream'));
  }).timeout(10000);

  it('does not pass server-stream implementation text to the client', async () => {
    await verify(client => callServerStream(client, 'serverStream'));
  }).timeout(10000);

  it('does not pass bidi implementation text to the client', async () => {
    await verify(client => callBidi(client, 'bidi'));
  }).timeout(10000);
});
