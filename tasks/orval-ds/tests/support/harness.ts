// Shared helpers for the hidden verifier suites.
//
// Every test drives the real generator entry point (`orval -c <config>` from the
// built package in /app) against a spec written in a fresh temporary workspace.
// The generated files are then loaded by a separate bun process, so code that a
// malicious description smuggled into the output runs exactly as it would when
// the generated client is imported or called.
import { execFileSync } from 'node:child_process';
import {
  mkdirSync,
  mkdtempSync,
  existsSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const APP = process.env.APP_DIR ?? '/app';
const BUN = process.env.BUN_BIN ?? 'bun';
const DEPS = process.env.VERIFIER_DEPS ?? '/opt/verifier-deps/node_modules';
const CLI = join(APP, 'packages/orval/dist/bin/orval.mjs');

export interface CaseOptions {
  spec: Record<string, unknown>;
  output: Record<string, unknown>;
  /** Relative target of the generated entry module, e.g. './gen/gen.ts'. */
  entry?: string;
  /** Extra files written into the fresh workspace before generation (e.g. a mutator). */
  files?: Record<string, string>;
}

export function makeWorkspace(): string {
  const dir = mkdtempSync(join(tmpdir(), 'orval-verifier-'));
  if (existsSync(DEPS)) symlinkSync(DEPS, join(dir, 'node_modules'));
  return dir;
}

/** Write the description and run the generator through its CLI entry point. */
export function generateCase(options: CaseOptions): {
  dir: string;
  entry: string;
} {
  const dir = makeWorkspace();
  for (const [name, body] of Object.entries(options.files ?? {})) {
    writeFileSync(join(dir, name), body);
  }
  writeFileSync(join(dir, 'spec.json'), JSON.stringify(options.spec));
  const config = `export default { verifier: { input: './spec.json', output: ${JSON.stringify(
    options.output,
  )} } };\n`;
  writeFileSync(join(dir, 'orval.config.mjs'), config);
  execFileSync(BUN, [CLI, '-c', './orval.config.mjs'], {
    cwd: dir,
    stdio: 'pipe',
    timeout: 180_000,
    env: { ...process.env, NO_COLOR: '1', FORCE_COLOR: '0' },
  });
  return { dir, entry: options.entry ?? './gen/gen.ts' };
}

export interface EvalResult {
  /** True when a description value executed as code in the generated module. */
  injected: boolean;
  /** Value produced by the test's `body` snippet, JSON-serialisable. */
  result?: unknown;
  /** Error raised while loading/calling the generated module. */
  error: string;
}

/**
 * Load the generated module in a fresh bun process, run `body` (which may use
 * the imported module as `m` and assign to `result`), and report whether the
 * attacker-controlled marker global was set.
 */
export function evaluate(
  dir: string,
  entry: string,
  body = '',
  timeout = 120_000,
): EvalResult {
  const runner = `
delete (globalThis as any).__PWNED;
let result: unknown;
let error = '';
try {
  const m: any = await import(${JSON.stringify(entry)});
  ${body}
} catch (e: any) {
  error = String((e && e.message) || e);
}
console.log('__RESULT__' + JSON.stringify({
  injected: (globalThis as any).__PWNED === true,
  result,
  error,
}));
`;
  writeFileSync(join(dir, 'runner.ts'), runner);
  let stdout = '';
  try {
    stdout = execFileSync(BUN, ['runner.ts'], {
      cwd: dir,
      encoding: 'utf8',
      timeout,
      env: { ...process.env, NO_COLOR: '1', FORCE_COLOR: '0' },
    });
  } catch (error: unknown) {
    const e = error as { stdout?: string; stderr?: string; message?: string };
    const line = String(e.stdout ?? '')
      .split('\n')
      .find((l) => l.startsWith('__RESULT__'));
    if (!line) {
      throw new Error(
        `generated module runner failed: ${String(e.message ?? e).slice(0, 300)} ${String(
          e.stderr ?? '',
        ).slice(0, 300)}`,
      );
    }
    stdout = String(e.stdout);
  }
  const line = stdout
    .split('\n')
    .filter((l) => l.startsWith('__RESULT__'))
    .pop();
  if (!line) throw new Error('generated module runner produced no result');
  return JSON.parse(line.slice('__RESULT__'.length)) as EvalResult;
}

/** A minimal OpenAPI description with one operation and one JSON response. */
export function specWithSchema(
  schema: Record<string, unknown>,
  operationId = 'getThing',
): Record<string, unknown> {
  return {
    openapi: '3.0.3',
    info: { title: 'verifier', version: '1.0.0' },
    paths: {
      '/things': {
        get: {
          operationId,
          responses: {
            200: {
              description: 'ok',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Thing' },
                },
              },
            },
          },
        },
      },
    },
    components: { schemas: { Thing: schema } },
  };
}

export function objectSchema(
  properties: Record<string, unknown>,
): Record<string, unknown> {
  return { type: 'object', properties };
}

export function simpleSpec(
  path: string,
  operationId = 'getThing',
  parameters: unknown[] = [],
  components?: Record<string, unknown>,
): Record<string, unknown> {
  return {
    openapi: '3.0.3',
    info: { title: 'verifier', version: '1.0.0' },
    paths: {
      [path]: {
        get: {
          operationId,
          ...(parameters.length ? { parameters } : {}),
          responses: { 200: { description: 'ok' } },
        },
      },
    },
    ...(components ? { components } : {}),
  };
}

export const ATTACK = 'globalThis.__PWNED=true';

export function ensureDir(path: string): void {
  if (!existsSync(path)) mkdirSync(path, { recursive: true });
}
