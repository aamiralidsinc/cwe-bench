// Security: request metadata taken from the description is emitted as source too.
import { describe, expect, it } from 'vitest';

import {
  ATTACK,
  evaluate,
  generateCase,
  objectSchema,
} from '../support/harness';

const MEDIA_TYPE = "application/json', __m: (" + ATTACK + "), __x: '";
const FIELD = 'x`+(' + ATTACK + ')+`';

describe('generated request metadata', () => {
  it('a media type may not break out of the Content-Type literal', () => {
    const spec = {
      openapi: '3.0.3',
      info: { title: 'verifier', version: '1.0.0' },
      paths: {
        '/things': {
          post: {
            operationId: 'createThing',
            requestBody: {
              content: {
                [MEDIA_TYPE]: {
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
globalThis.fetch = ((_url: any, init: any) => {
  headers = init?.headers;
  throw new Error('stop');
}) as any;
try { await m.createThing({ a: 'x' }); } finally { result = headers; }
`;
    const out = evaluate(dir, entry, body);
    expect(out.injected).toBe(false);
    // The media type is carried as data: the header holds exactly the described text.
    expect((out.result as Record<string, unknown> | null)?.['Content-Type']).toBe(
      MEDIA_TYPE,
    );
  });

  it('a form field name may not break out of its literal', () => {
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
                  schema: objectSchema({ [FIELD]: { type: 'string' } }),
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
globalThis.fetch = ((_url: any, init: any) => {
  const form = init?.body;
  fields = form ? Array.from(form.keys()) : null;
  throw new Error('stop');
}) as any;
try { await m.upload({ ${JSON.stringify(FIELD)}: 'v' }); } finally { result = fields; }
`;
    const out = evaluate(dir, entry, body);
    expect(out.injected).toBe(false);
    // The field name is carried as data: the form holds exactly the described name.
    expect(out.result).toEqual([FIELD]);
  });
});
