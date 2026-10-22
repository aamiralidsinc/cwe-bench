// Functional: the composed model still enforces the properties its parent lists.
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import ts from 'typescript';
import { describe, expect, it } from 'vitest';

import { generateCase, objectSchema, specWithSchema } from '../support/harness';

function typeErrors(dir: string, consumer: string): string[] {
  const path = join(dir, 'consumer.ts');
  writeFileSync(path, consumer);
  const program = ts.createProgram([path], {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.ESNext,
    moduleResolution: ts.ModuleResolutionKind.Bundler,
    lib: ['lib.es2020.d.ts', 'lib.dom.d.ts'],
    strict: true,
    noEmit: true,
    skipLibCheck: true,
    types: [],
  });
  return ts
    .getPreEmitDiagnostics(program)
    .filter(
      (diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error,
    )
    .map((diagnostic) =>
      ts.flattenDiagnosticMessageText(diagnostic.messageText, ' '),
    );
}

describe('composed model requirements', () => {
  it('a property listed as required by the composition stays required', () => {
    const { dir } = generateCase({
      spec: specWithSchema({
        allOf: [
          objectSchema({ 'a-b': { type: 'string' } }),
          objectSchema({ b: { type: 'string' } }),
        ],
        required: ['a-b'],
      }),
      output: { target: './gen/gen.ts', client: 'fetch' },
    });

    const errors = typeErrors(
      dir,
      `import type { Thing } from './gen/gen';
const ok: Thing = { 'a-b': 'x', b: 'y' };
// @ts-expect-error the composition still requires the listed property
const missing: Thing = { b: 'y' };
export { ok, missing };
`,
    );
    expect(errors).toEqual([]);
  });

  it('a sibling property that is not listed stays optional', () => {
    const { dir } = generateCase({
      spec: specWithSchema({
        allOf: [
          objectSchema({ 'a-b': { type: 'string' } }),
          objectSchema({ b: { type: 'string' } }),
        ],
        required: ['a-b'],
      }),
      output: { target: './gen/gen.ts', client: 'fetch' },
    });

    const errors = typeErrors(
      dir,
      `import type { Thing } from './gen/gen';
const ok: Thing = { 'a-b': 'x' };
export { ok };
`,
    );
    expect(errors).toEqual([]);
  });
});
