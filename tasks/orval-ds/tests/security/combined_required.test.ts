// Security: a name listed as required is emitted into a composed model type.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import ts from 'typescript';
import { describe, expect, it } from 'vitest';

import {
  evaluate,
  generateCase,
  objectSchema,
  specWithSchema,
} from '../support/harness';

const REQUIRED = "x'>>;globalThis.__PWNED=true;//";

describe('generated composed model types', () => {
  it('a required name may not become a statement', () => {
    const { dir, entry } = generateCase({
      spec: specWithSchema({
        allOf: [
          objectSchema({ [REQUIRED]: { type: 'string' } }),
          objectSchema({ b: { type: 'string' } }),
        ],
        required: [REQUIRED],
      }),
      output: { target: './gen/gen.ts', client: 'fetch' },
    });

    // Loading the generated module must not run anything the name describes.
    expect(evaluate(dir, entry).injected).toBe(false);

    // The name is carried as data: the model still spells it as one literal.
    const source = readFileSync(join(dir, 'gen/gen.ts'), 'utf8');
    const file = ts.createSourceFile(
      'gen.ts',
      source,
      ts.ScriptTarget.Latest,
      true,
    );
    const literals: string[] = [];
    const visit = (node: ts.Node): void => {
      if (ts.isStringLiteral(node)) literals.push(node.text);
      ts.forEachChild(node, visit);
    };
    visit(file);
    expect(literals).toContain(REQUIRED);
  });
});
