// Everything a legitimate template does with includes today must keep working.
import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import {
  makeLab,
  mjml2html,
  MJMLParser,
  WORKSPACE,
  recordReads,
  runNodeScript,
  outputOf,
  messagesOf,
  template,
  writeTemplate,
  INSIDE_MARKER,
  OUTSIDE_MARKER,
} from '../support/lab.mjs'

const lab = makeLab()
after(() => lab.cleanup())

const compile = (include, options = {}) =>
  mjml2html(template(include), {
    filePath: lab.project,
    actualPath: path.join(lab.project, 'page.mjml'),
    ...options,
  })

test('an include inside the root is rendered', () => {
  assert.ok(outputOf(compile('./ok.mjml')).includes(INSIDE_MARKER))
})

test('a configured partials directory is the root', () => {
  const partials = path.join(lab.base, 'partials')
  fs.mkdirSync(partials)
  fs.writeFileSync(path.join(partials, 'header.mjml'), `<mj-text>${INSIDE_MARKER}</mj-text>`)
  const result = mjml2html(template('./header.mjml'), {
    filePath: partials,
    actualPath: path.join(lab.base, 'templates', 'page.mjml'),
  })
  assert.ok(outputOf(result).includes(INSIDE_MARKER))
})

test('a configured root given as a file uses its directory', () => {
  const page = path.join(lab.project, 'page.mjml')
  fs.writeFileSync(page, '')
  const result = mjml2html(template('./ok.mjml'), { filePath: page, actualPath: page })
  assert.ok(outputOf(result).includes(INSIDE_MARKER))
})

test('with no configured root the working directory is the root', () => {
  writeTemplate(lab.project, 'cwd-page.mjml', './ok.mjml')
  const source = `
    const mjml = require(${JSON.stringify(path.join(WORKSPACE, 'packages', 'mjml', 'lib', 'index.js'))})
    const out = mjml(${JSON.stringify(template('./ok.mjml'))}, {})
    process.stdout.write(out.html || '')
  `
  const run = runNodeScript(source, { cwd: lab.project })
  assert.equal(run.status, 0, `child failed: ${run.stderr}`)
  assert.ok(run.stdout.includes(INSIDE_MARKER), 'the default root stopped resolving includes')
})

test('a partial with another extension keeps working', () => {
  assert.ok(outputOf(compile('./plain.txt')).includes(INSIDE_MARKER))
})

test('a link inside the root that stays inside keeps working', () => {
  assert.ok(outputOf(compile('./inner-link.mjml')).includes(INSIDE_MARKER))
})

test('a nested partial resolves a relative include from its own location', () => {
  fs.writeFileSync(
    path.join(lab.project, 'sub', 'child.mjml'),
    `<mj-text>child</mj-text><mj-include path="../ok.mjml" />`,
  )
  const result = compile('sub/child.mjml')
  assert.ok(outputOf(result).includes(INSIDE_MARKER), 'a partial could not reach a sibling in the root')
})

test('a missing include inside the root still reports an error naming the target as written', () => {
  const result = compile('./missing.mjml')
  const combined = `${outputOf(result)}\n${messagesOf(result)}`
  assert.ok(combined.includes('./missing.mjml'), 'the failure no longer names the written target')
})

test('includes can still be ignored without touching the filesystem', () => {
  const probe = recordReads()
  try {
    const tree = MJMLParser(template('../secret/outside.mjml'), {
      filePath: lab.project,
      ignoreIncludes: true,
    })
    assert.ok(!JSON.stringify(tree).includes(OUTSIDE_MARKER))
    assert.ok(!probe.touched(lab.outsideFile), 'an ignored include was read')
  } finally {
    probe.restore()
  }
})
