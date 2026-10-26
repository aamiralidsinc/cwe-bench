import * as assert from 'assert';
import * as grpc from '../src';
import {
  CallOutcome,
  callUnary,
  identity,
  makeClient,
  startServer,
} from './zzsupport';

const AUTH_DETAILS = 'DELIBERATE_AUTH_d18c4e';

const definition = {
  echo: {
    path: '/TestService/Echo',
    requestStream: false,
    responseStream: false,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  },
  list: {
    path: '/TestService/List',
    requestStream: false,
    responseStream: true,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  },
  guarded: {
    path: '/TestService/Guarded',
    requestStream: false,
    responseStream: false,
    requestDeserialize: identity,
    responseSerialize: identity,
    requestSerialize: identity,
    responseDeserialize: identity,
  },
};

const implementation = {
  echo(call: any, callback: any) {
    callback(null, call.request);
  },
  list(stream: any) {
    stream.write(Buffer.from('one'));
    stream.write(Buffer.from('two'));
    stream.end();
  },
  guarded(call: any, callback: any) {
    callback(null, Buffer.from('ok'));
  },
};

const authInterceptor = ((methodDescriptor: any, call: any) => {
  const listener = new grpc.ServerListenerBuilder()
    .withOnReceiveMetadata((metadata, next) => {
      if (metadata.get('authorization')?.[0] !== 'good') {
        call.sendStatus({
          code: grpc.status.UNAUTHENTICATED,
          details: AUTH_DETAILS,
        });
      } else {
        next(metadata);
      }
    })
    .build();
  const responder = new grpc.ResponderBuilder()
    .withStart(next => next(listener))
    .build();
  return new grpc.ServerInterceptingCall(call, responder);
}) as unknown as grpc.ServerInterceptor;

describe('normal operation is preserved', () => {
  it('serves a successful unary call', async () => {
    const ctx = await startServer(definition, implementation);
    const client = makeClient(definition, ctx.port);
    try {
      const outcome = await callUnary(client, 'echo', Buffer.from('payload'));
      assert.ifError(outcome.err);
      assert.strictEqual(String(outcome.value), 'payload');
    } finally {
      client.close();
      ctx.shutdown();
    }
  }).timeout(10000);

  it('serves a successful server-streaming call', async () => {
    const ctx = await startServer(definition, implementation);
    const client = makeClient(definition, ctx.port);
    try {
      const values: string[] = [];
      const err: any = await new Promise(resolve => {
        const call = client.list(Buffer.from('x'));
        call.on('data', (value: any) => values.push(String(value)));
        call.on('error', (e: any) => resolve(e));
        call.on('end', () => resolve(null));
      });
      assert.ifError(err);
      assert.deepStrictEqual(values, ['one', 'two']);
    } finally {
      client.close();
      ctx.shutdown();
    }
  }).timeout(10000);

  it('delivers the status an interceptor sends deliberately', async () => {
    const ctx = await startServer(definition, implementation, {
      interceptors: [authInterceptor],
    });
    const client = makeClient(definition, ctx.port);
    try {
      const denied = await callUnary(client, 'guarded', Buffer.from('x'));
      assert(denied.err);
      assert.strictEqual(denied.err.code, grpc.status.UNAUTHENTICATED);
      assert.strictEqual(denied.err.details, AUTH_DETAILS);

      const metadata = new grpc.Metadata();
      metadata.add('authorization', 'good');
      const allowed: CallOutcome = await new Promise(resolve => {
        client.guarded(
          Buffer.from('x'),
          metadata,
          (err: any, value: any) => resolve({ err, value })
        );
      });
      assert.ifError(allowed.err);
      assert.strictEqual(String(allowed.value), 'ok');
    } finally {
      client.close();
      ctx.shutdown();
    }
  }).timeout(10000);
});
