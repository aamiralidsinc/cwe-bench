// Functional: request metadata from the description still reaches the request.
import { describe, expect, it } from 'vitest';

import { evaluate, generateCase, objectSchema } from '../support/harness';

describe('request metadata', () => {
  it('a json request body still sets its Content-Type header', () => {
    const spec = {
      openapi: '3.0.3',
      info: { title: 'verifier', version: '1.0.0' },
      paths: {
        '/things': {
          post: {
            operationId: 'createThing',
            requestBody: {
              content: {
                'application/json': {
                  schema: objectSchema({ a: { type: 'string' } }),
                },
              },
            },
            responses: { 200: { description: 'ok' } },
          },
        },
      },
    };
    const { dir, entry } = generateCase({
      spec,
      output: { target: './gen/gen.ts', client: 'fetch' },
    });
    const body = `
let headers: any = null;
globalThis.fetch = (async (_url: any, init: any) => {
  headers = init?.headers;
  throw new Error('stop');
}) as any;
try { await m.createThing({ a: 'x' }); } catch {}
result = headers;
`;
    const out = evaluate(dir, entry, body);
    expect((out.result as Record<string, unknown>)['Content-Type']).toBe(
      'application/json',
    );
  });

  it('a multipart body still appends its field name', () => {
    const spec = {
      openapi: '3.0.3',
      info: { title: 'verifier', version: '1.0.0' },
      paths: {
        '/upload': {
          post: {
            operationId: 'upload',
            requestBody: {
              required: true,
              content: {
                'multipart/form-data': {
                  schema: objectSchema({ note: { type: 'string' } }),
                },
              },
            },
            responses: { 200: { description: 'ok' } },
          },
        },
      },
    };
    const { dir, entry } = generateCase({
      spec,
      output: { target: './gen/gen.ts', client: 'fetch' },
    });
    const body = `
let fields: string[] | null = null;
globalThis.fetch = (async (_url: any, init: any) => {
  const form = init?.body;
  fields = form ? Array.from(form.keys()) : null;
  throw new Error('stop');
}) as any;
try { await m.upload({ note: 'v' }); } catch {}
result = fields;
`;
    const out = evaluate(dir, entry, body);
    expect(out.result).toEqual(['note']);
  });

  it('a media type with a quoted parameter reaches the Content-Type header unchanged', () => {
    const mediaType = 'application/json; profile="urn:example:say-hi"';
    const spec = {
      openapi: '3.0.3',
      info: { title: 'verifier', version: '1.0.0' },
      paths: {
        '/things': {
          post: {
            operationId: 'createThing',
            requestBody: {
              content: {
                [mediaType]: {
                  schema: objectSchema({ a: { type: 'string' } }),
                },
              },
            },
            responses: { 200: { description: 'ok' } },
          },
        },
      },
    };
    const { dir, entry } = generateCase({
      spec,
      output: { target: './gen/gen.ts', client: 'fetch' },
    });
    const body = `
let headers: any = null;
globalThis.fetch = (async (_url: any, init: any) => {
  headers = init?.headers;
  throw new Error('stop');
}) as any;
try { await m.createThing({ a: 'x' }); } catch {}
result = headers;
`;
    const out = evaluate(dir, entry, body);
    expect((out.result as Record<string, unknown>)['Content-Type']).toBe(mediaType);
  });

  it('a multipart field name with quotes is appended unchanged', () => {
    const field = 'say "hi"';
    const spec = {
      openapi: '3.0.3',
      info: { title: 'verifier', version: '1.0.0' },
      paths: {
        '/upload': {
          post: {
            operationId: 'upload',
            requestBody: {
              required: true,
              content: {
                'multipart/form-data': {
                  schema: objectSchema({
                    [field]: { type: 'string' },
                    note: { type: 'string' },
                  }),
                },
              },
            },
            responses: { 200: { description: 'ok' } },
          },
        },
      },
    };
    const { dir, entry } = generateCase({
      spec,
      output: { target: './gen/gen.ts', client: 'fetch' },
    });
    const body = `
let fields: unknown = null;
globalThis.fetch = (async (_url: any, init: any) => {
  const form = init?.body;
  fields = form ? Array.from(form.entries()) : null;
  throw new Error('stop');
}) as any;
try { await m.upload({ ${JSON.stringify(field)}: 'v', note: 'n' }); } catch {}
result = fields;
`;
    const out = evaluate(dir, entry, body);
    expect(out.result).toEqual([
      [field, 'v'],
      ['note', 'n'],
    ]);
  });
});
