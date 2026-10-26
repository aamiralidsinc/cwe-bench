// Minimal JUnit runner for the hidden suites. Each group module exports
// `cases`; a case throws (or rejects) when it fails. The runner always writes
// a JUnit XML file so the orchestrator can score a group even when every case
// fails, and never lets one case abort the rest.
import * as fs from 'node:fs';
import * as path from 'node:path';

export interface Case {
  id: string;
  name: string;
  run: () => void | Promise<void>;
}

const group = process.argv[2];
const outPath = process.argv[3];
if (!group || !outPath) {
  console.error('usage: runner.ts <security|functional> <output.xml>');
  process.exit(2);
}

function esc(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function withTimeout<T>(p: T | Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    Promise.resolve(p),
    new Promise<T>((_, reject) => {
      const timer = setTimeout(
        () => reject(new Error(`case timed out after ${ms} ms`)),
        ms,
      );
      (timer as any).unref?.();
    }),
  ]);
}

const mod = (await import(`../${group}/index.ts`)) as { cases: Case[] };
const cases = mod.cases;

const rows: { id: string; name: string; error: string }[] = [];
for (const testCase of cases) {
  let error = '';
  try {
    await withTimeout(testCase.run(), 30000);
  } catch (err) {
    error = err instanceof Error ? `${err.name}: ${err.message}` : String(err);
  }
  rows.push({ id: testCase.id, name: testCase.name, error });
}

const failures = rows.filter((row) => row.error !== '').length;
const body = rows
  .map((row) => {
    const inner =
      row.error === ''
        ? ''
        : `<failure message="${esc(row.error.split('\n')[0] ?? '')}">${esc(row.error)}</failure>`;
    return `  <testcase classname="${esc(group)}" name="${esc(row.id)}">${inner}</testcase>`;
  })
  .join('\n');
const xml = `<?xml version="1.0" encoding="utf-8"?>
<testsuites name="nogginlessdom">
<testsuite name="${esc(group)}" tests="${rows.length}" failures="${failures}" errors="0" skipped="0">
${body}
</testsuite>
</testsuites>
`;

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, xml, 'utf-8');
console.log(
  `${group}: ${rows.length - failures}/${rows.length} passed${
    failures > 0 ? `, ${failures} failed` : ''
  }`,
);
for (const row of rows) {
  if (row.error !== '') console.log(`  FAIL ${row.id}: ${row.error}`);
}
process.exit(failures === 0 ? 0 : 1);
