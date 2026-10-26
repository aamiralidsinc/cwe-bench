import * as assert from 'assert';
import * as grpc from '../src';
import {
  assertLeakBlocked,
  callUnary,
  identity,
  makeClient,
  startServer,
} from './zzsupport';

const MARKER = 'INTERCEPTOR_EXCEPTION_5d1e8a';

const definition = {
  attack: {
    path: '/TestService/Attack',
    requestStream: false,
    responseStream: false,
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

const implementation = {
  attack(call: any, callback: any) {
    callback(null, Buffer.from('ok'));
  },
  health(call: any, callback: any) {
    callback(null, Buffer.from('ok'));
  },
};

const throwingInterceptor = ((methodDescriptor: any, call: any) => {
  if (methodDescriptor.path === '/TestService/Attack') {
    throw new Error(`${MARKER}: interceptor failure`);
  }
  return call;
}) as unknown as grpc.ServerInterceptor;

describe('exceptions thrown by application-supplied call handling', () => {
  it('does not pass the exception text to the client', async () => {
    const ctx = await startServer(definition, implementation, {
      interceptors: [throwingInterceptor],
    });
    const client = makeClient(definition, ctx.port);
    try {
      const outcome = await callUnary(client, 'attack');
      assertLeakBlocked(outcome, MARKER);
      const health = await callUnary(client, 'health');
      assert.ifError(health.err);
      assert.strictEqual(String(health.value), 'ok');
    } finally {
      client.close();
      ctx.shutdown();
    }
  }).timeout(10000);
});
