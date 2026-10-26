// The project's own suites for the affected area must keep passing.
import test from 'node:test'
import assert from 'node:assert/strict'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { WORKSPACE } from '../support/lab.mjs'

function runProjectSuite(cwd, script) {
  return spawnSync(process.execPath, [script], {
    cwd: path.join(WORKSPACE, cwd),
    encoding: 'utf8',
    timeout: 180000,
    killSignal: 'SIGKILL',
    env: { ...process.env },
  })
}

test('the parser package suite passes', () => {
  const run = runProjectSuite('packages/mjml-parser-xml', 'test/test.js')
  assert.equal(run.status, 0, `parser suite failed:\n${run.stdout}\n${run.stderr}`)
})

test('the core package suite passes', () => {
  const run = runProjectSuite('packages/mjml-core', 'tests/index.js')
  assert.equal(run.status, 0, `core suite failed:\n${run.stdout}\n${run.stderr}`)
})
