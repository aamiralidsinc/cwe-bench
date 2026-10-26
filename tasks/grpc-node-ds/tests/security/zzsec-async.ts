import * as assert from 'assert';
import {
  assertLeakBlocked,
  callUnary,
  identity,
  makeClient,
  startServer,
} from './zzsupport';

const MARKER = 'ASYNC_EXCEPTION_3e6b0d';

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
  async attack(call: any, callback: any) {
    throw new Error(`${MARKER}: asynchronous implementation failure`);
  },
  health(call: any, callback: any) {
    callback(null, Buffer.from('ok'));
  },
};

describe('exceptions raised asynchronously by a method implementation', () => {
  it('does not pass the exception text to the client', async () => {
    const ctx = await startServer(definition, implementation);
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
