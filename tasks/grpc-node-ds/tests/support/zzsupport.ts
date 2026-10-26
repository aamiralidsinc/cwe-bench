// Shared helpers for the hidden suites. Everything here drives the library
// through its public API only.
import * as grpc from '../src';

export const REQUEST_BYTES = Buffer.from('ping');

export interface RunningServer {
  server: grpc.Server;
  port: number;
  shutdown(): void;
}

export function identity(value: any): any {
  return value;
}

export function startServer(
  definition: any,
  implementation: any,
  options?: grpc.ServerOptions
): Promise<RunningServer> {
  return new Promise((resolve, reject) => {
    const server = new grpc.Server(options);
    server.addService(definition, implementation);
    server.bindAsync(
      '127.0.0.1:0',
      grpc.ServerCredentials.createInsecure(),
      (err, port) => {
        if (err) {
          reject(err);
          return;
        }
        server.start();
        resolve({
          server,
          port,
          shutdown() {
            server.forceShutdown();
          },
        });
      }
    );
  });
}

export function makeClient(definition: any, port: number): any {
  const Client = grpc.makeGenericClientConstructor(definition, 'TestService');
  return new (Client as any)(
    `127.0.0.1:${port}`,
    grpc.credentials.createInsecure()
  );
}

export interface CallOutcome {
  err: any;
  value?: any;
}

export function callUnary(
  client: any,
  method: string,
  payload: Buffer = REQUEST_BYTES
): Promise<CallOutcome> {
  return new Promise(resolve => {
    client[method](payload, (err: any, value: any) => resolve({ err, value }));
  });
}

export function callClientStream(
  client: any,
  method: string,
  payload: Buffer = REQUEST_BYTES
): Promise<CallOutcome> {
  return new Promise(resolve => {
    const call = client[method]((err: any, value: any) =>
      resolve({ err, value })
    );
    call.on('error', () => {
      /* the callback reports the status */
    });
    call.write(payload);
    call.end();
  });
}

export function callServerStream(
  client: any,
  method: string,
  payload: Buffer = REQUEST_BYTES
): Promise<CallOutcome> {
  return new Promise(resolve => {
    const call = client[method](payload);
    call.on('data', () => {
      /* drain */
    });
    call.on('error', (err: any) => resolve({ err }));
    call.on('end', () => resolve({ err: null }));
  });
}

export function callBidi(
  client: any,
  method: string,
  payload: Buffer = REQUEST_BYTES
): Promise<CallOutcome> {
  return new Promise(resolve => {
    const call = client[method]();
    call.on('data', () => {
      /* drain */
    });
    call.on('error', (err: any) => resolve({ err }));
    call.on('end', () => resolve({ err: null }));
    call.write(payload);
    call.end();
  });
}

/** The call must have failed, and its detail text must not carry the marker. */
export function assertLeakBlocked(outcome: CallOutcome, marker: string): void {
  if (!outcome.err) {
    throw new Error('expected the call to end with an error status');
  }
  const details = String(outcome.err.details || '');
  if (details.includes(marker)) {
    throw new Error(
      `the client received the server-side exception text: ${details}`
    );
  }
}

export const UNARY_METHOD = {
  requestStream: false,
  responseStream: false,
};
