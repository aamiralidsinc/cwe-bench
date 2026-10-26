// A template that names a partial outside the configured project root must not
// cause that file to be read, and none of its content may reach the output.
import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import path from 'node:path'
import {
  makeLab,
  mjml2html,
  recordReads,
  outputOf,
  messagesOf,
  template,
  OUTSIDE_MARKER,
  SIBLING_MARKER,
} from '../support/lab.mjs'

const lab = makeLab()
after(() => lab.cleanup())

const compile = include =>
  mjml2html(template(include), {
    filePath: lab.project,
    actualPath: path.join(lab.project, 'page.mjml'),
  })

// `written` is the target as the template wrote it. The instruction lets diagnostics name the
// target exactly as written, so the resolved-location check applies only when the two differ
// (2026-10-24 audit fix: the absolute-path case wrote the resolved path itself).
function assertBlocked(result, probe, target, marker, written) {
  const html = outputOf(result)
  const diagnostics = messagesOf(result)
  assert.ok(!html.includes(marker), `content of ${target} reached the generated email`)
  assert.ok(!diagnostics.includes(marker), `content of ${target} reached the diagnostics`)
  if (written !== target) assert.ok(!html.includes(target), 'the generated email disclosed the resolved target')
  assert.ok(!probe.touched(target), `the target ${target} was read`)
}

test('a relative path that climbs out of the root is refused', () => {
  const probe = recordReads()
  try {
    const result = compile('../secret/outside.mjml')
    assertBlocked(result, probe, lab.outsideFile, OUTSIDE_MARKER)
  } finally {
    probe.restore()
  }
})

test('an absolute path outside the root is refused', () => {
  const probe = recordReads()
  try {
    const result = compile(lab.outsideFile)
    assertBlocked(result, probe, lab.outsideFile, OUTSIDE_MARKER, lab.outsideFile)
  } finally {
    probe.restore()
  }
})

test('a sibling directory sharing the root prefix is refused', () => {
  const probe = recordReads()
  try {
    const result = compile('../project-sibling/secret.mjml')
    assertBlocked(result, probe, lab.siblingFile, SIBLING_MARKER)
  } finally {
    probe.restore()
  }
})

test('a link inside the root that points outside is refused', () => {
  const probe = recordReads()
  try {
    const result = compile('./link.mjml')
    assertBlocked(result, probe, lab.outsideFile, OUTSIDE_MARKER)
  } finally {
    probe.restore()
  }
})
