// Watch mode tracks the partials a template depends on with its own resolver.
// That resolver must apply the same confinement before it opens a file, even
// though its result is only a watch list.
import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import {
  makeLab,
  startWatch,
  waitFor,
  readProbeLog,
  writeTemplate,
  OUTSIDE_MARKER,
} from '../support/lab.mjs'

const lab = makeLab()
after(() => lab.cleanup())

// The watcher appends a missing .mjml suffix to its own target, while the
// compiler resolves the attribute as written. A file that exists only under the
// suffixed name isolates what the watcher's resolver opened.
const watchOnlyTarget = path.join(lab.secret, 'watch-only.mjml')
fs.writeFileSync(watchOnlyTarget, `<mj-text>${OUTSIDE_MARKER}</mj-text>`)

test('watch mode does not open a file outside the root', async () => {
  const input = writeTemplate(lab.project, 'watched.mjml', '../secret/watch-only')
  const output = path.join(lab.base, 'watched.html')
  const probeLog = path.join(lab.base, 'watch.reads')
  const logFile = path.join(lab.base, 'watch.log')

  const watch = startWatch({ input, output, cwd: lab.base, probeLog, logFile })
  try {
    const compiled = await waitFor(() => fs.existsSync(output), { timeout: 20000 })
    assert.ok(compiled, 'the watcher never produced its first output')
    // The dependency scan runs in the watcher's first event-loop turn; give it
    // a moment after the first compile to be sure every read is recorded.
    await new Promise(resolve => setTimeout(resolve, 500))
  } finally {
    watch.stop()
  }

  const reads = readProbeLog(probeLog)
  assert.ok(
    !reads.some(read => path.resolve(read) === watchOnlyTarget),
    'the watcher opened a file outside the root',
  )
})
