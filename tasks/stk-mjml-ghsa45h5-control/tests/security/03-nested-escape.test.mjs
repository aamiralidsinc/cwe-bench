// A partial that lives inside the root can itself contain an include. That
// nested include must be held to the same root, and a partial one level deeper
// must not gain a wider root.
import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import {
  makeLab,
  mjml2html,
  recordReads,
  outputOf,
  messagesOf,
  template,
  OUTSIDE_MARKER,
} from '../support/lab.mjs'

const lab = makeLab()
after(() => lab.cleanup())

const compile = include =>
  mjml2html(template(include), {
    filePath: lab.project,
    actualPath: path.join(lab.project, 'page.mjml'),
  })

function assertBlocked(result, probe) {
  const html = outputOf(result)
  const diagnostics = messagesOf(result)
  assert.ok(!html.includes(OUTSIDE_MARKER), 'nested include inlined outside content')
  assert.ok(!diagnostics.includes(OUTSIDE_MARKER), 'nested include leaked outside content')
  assert.ok(!html.includes(lab.outsideFile), 'nested include disclosed the resolved target')
  assert.ok(!probe.touched(lab.outsideFile), 'nested include read the outside file')
}

test('a partial can not climb out of the root with a relative include', () => {
  fs.writeFileSync(
    path.join(lab.project, 'sub', 'child.mjml'),
    `<mj-text>child</mj-text><mj-include path="../../secret/outside.mjml" />`,
  )
  const probe = recordReads()
  try {
    assertBlocked(compile('sub/child.mjml'), probe)
  } finally {
    probe.restore()
  }
})

test('a deeper partial does not gain a wider root', () => {
  fs.writeFileSync(
    path.join(lab.project, 'sub', 'deep', 'child.mjml'),
    `<mj-text>child</mj-text><mj-include path="../../../secret/outside.mjml" />`,
  )
  const probe = recordReads()
  try {
    assertBlocked(compile('sub/deep/child.mjml'), probe)
  } finally {
    probe.restore()
  }
})
