// Watch mode must keep tracking a partial inside the root: changing the
// partial recompiles the templates that include it.
import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { makeLab, startWatch, waitFor, writeTemplate } from '../support/lab.mjs'

const lab = makeLab()
after(() => lab.cleanup())

test('changing an in-root partial recompiles the template that includes it', async () => {
  const partial = path.join(lab.project, 'sub', 'watched-partial.mjml')
  fs.writeFileSync(partial, '<mj-text>FIRST-VALUE</mj-text>')
  const input = writeTemplate(lab.project, 'watched-page.mjml', './sub/watched-partial.mjml')
  const output = path.join(lab.base, 'watched-page.html')
  const probeLog = path.join(lab.base, 'watch-functional.reads')
  const logFile = path.join(lab.base, 'watch-functional.log')

  const watch = startWatch({ input, output, cwd: lab.base, probeLog, logFile })
  try {
    assert.ok(
      await waitFor(() => fs.existsSync(output) && fs.readFileSync(output, 'utf8').includes('FIRST-VALUE'), {
        timeout: 20000,
      }),
      'the initial compile did not include the partial',
    )

    fs.writeFileSync(partial, '<mj-text>SECOND-VALUE</mj-text>')
    assert.ok(
      await waitFor(() => fs.readFileSync(output, 'utf8').includes('SECOND-VALUE'), { timeout: 20000 }),
      'a change to an in-root partial did not trigger a recompile',
    )
  } finally {
    watch.stop()
  }
})
