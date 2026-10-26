import * as assert from 'assert';
import {
  assertLeakBlocked,
  callUnary,
  identity,
  makeClient,
  startServer,
} from './zzsupport';

const SERIALIZER_MARKER = 'SERIALIZER_EXCEPTION_2b8d1f';
const DESERIALIZER_MARKER = 'DESERIALIZER_EXCEPTION_9a4e7c';

function healthMethod(): any {
  return {
    path: '/TestService/Health',
    requestStream: false,
    responseStream: false,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  };
}

describe('exceptions thrown by application-supplied message converters', () => {
  it('does not pass a response converter exception to the client', async () => {
    const definition = {
      convert: {
        path: '/TestService/Convert',
        requestStream: false,
        responseStream: false,
        requestDeserialize: identity,
        responseSerialize() {
          throw new Error(`${SERIALIZER_MARKER}: could not encode response`);
        },
        requestSerialize: identity,
        responseDeserialize: identity,
      },
      health: healthMethod(),
    };
    const implementation = {
      convert(call: any, callback: any) {
        callback(null, Buffer.from('response'));
      },
      health(call: any, callback: any) {
        callback(null, Buffer.from('ok'));
      },
    };
    const ctx = await startServer(definition, implementation);
    const client = makeClient(definition, ctx.port);
    try {
      const outcome = await callUnary(client, 'convert');
      assertLeakBlocked(outcome, SERIALIZER_MARKER);
      const health = await callUnary(client, 'health');
      assert.ifError(health.err);
      assert.strictEqual(String(health.value), 'ok');
    } finally {
      client.close();
      ctx.shutdown();
    }
  }).timeout(10000);

  it('does not pass a request converter exception to the client', async () => {
    const definition = {
      convert: {
        path: '/TestService/Convert',
        requestStream: false,
        responseStream: false,
        requestDeserialize() {
          throw new Error(`${DESERIALIZER_MARKER}: could not decode request`);
        },
        responseSerialize: identity,
        requestSerialize: identity,
        responseDeserialize: identity,
      },
      health: healthMethod(),
    };
    const implementation = {
      convert(call: any, callback: any) {
        callback(null, Buffer.from('response'));
      },
      health(call: any, callback: any) {
        callback(null, Buffer.from('ok'));
      },
    };
    const ctx = await startServer(definition, implementation);
    const client = makeClient(definition, ctx.port);
    try {
      const outcome = await callUnary(client, 'convert');
      assertLeakBlocked(outcome, DESERIALIZER_MARKER);
      const health = await callUnary(client, 'health');
      assert.ifError(health.err);
      assert.strictEqual(String(health.value), 'ok');
    } finally {
      client.close();
      ctx.shutdown();
    }
  }).timeout(10000);
});
