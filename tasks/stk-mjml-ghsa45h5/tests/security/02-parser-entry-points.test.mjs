// The protection must hold at the parsing layer every entry point uses, not
// only in one caller: the standalone parser package, the same parser at its
// default root, and the command-line validation path.
import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import {
  makeLab,
  MJMLParser,
  WORKSPACE,
  recordReads,
  runCli,
  runNodeScript,
  probeEnv,
  readProbeLog,
  template,
  writeTemplate,
  OUTSIDE_MARKER,
} from '../support/lab.mjs'

const lab = makeLab()
after(() => lab.cleanup())

test('the parser package refuses an out-of-root target', () => {
  const probe = recordReads()
  try {
    const tree = MJMLParser(template('../secret/outside.mjml'), {
      filePath: lab.project,
      actualPath: path.join(lab.project, 'page.mjml'),
    })
    const serialized = JSON.stringify(tree)
    assert.ok(!serialized.includes(OUTSIDE_MARKER), 'the parser inlined outside content')
    assert.ok(!probe.touched(lab.outsideFile), 'the parser read the outside file')
  } finally {
    probe.restore()
  }
})

test('the parser defaults its root to the working directory', () => {
  const probeLog = path.join(lab.base, 'parser-default.reads')
  writeTemplate(lab.project, 'page.mjml', '../secret/outside.mjml')
  const source = `
    const parser = require(${JSON.stringify(path.join(WORKSPACE, 'packages', 'mjml-parser-xml', 'lib', 'index.js'))})
    const tree = parser(${JSON.stringify(template('../secret/outside.mjml'))}, {})
    process.stdout.write(JSON.stringify(tree))
  `
  const run = runNodeScript(source, {
    cwd: lab.project,
    env: probeEnv(probeLog),
  })
  assert.equal(run.status, 0, `parser child failed: ${run.stderr}`)
  assert.ok(!run.stdout.includes(OUTSIDE_MARKER), 'the parser inlined outside content')
  const reads = readProbeLog(probeLog)
  assert.ok(
    !reads.some(read => path.resolve(read) === lab.outsideFile),
    'the parser read the outside file',
  )
})

test('the command-line validation path refuses an out-of-root target', () => {
  const probeLog = path.join(lab.base, 'validate.reads')
  writeTemplate(lab.project, 'page.mjml', '../secret/outside.mjml')
  const run = runCli(['-v', 'page.mjml'], { cwd: lab.project, env: probeEnv(probeLog) })
  assert.notEqual(
    run.status,
    0,
    'validation accepted a document whose include lies outside the include base',
  )
  const combined = `${run.stdout}\n${run.stderr}`
  assert.ok(!combined.includes(OUTSIDE_MARKER), 'the validation path inlined outside content')
  const reads = readProbeLog(probeLog)
  assert.ok(
    !reads.some(read => path.resolve(read) === lab.outsideFile),
    'the validation path read the outside file',
  )
})

test('the command-line render path refuses an out-of-root target', () => {
  writeTemplate(lab.project, 'page.mjml', '../secret/outside.mjml')
  const run = runCli(['page.mjml', '-s'], { cwd: lab.project })
  assert.ok(!run.stdout.includes(OUTSIDE_MARKER), 'the CLI render inlined outside content')
})
