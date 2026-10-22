// A client that only holds the API token (which the product hands to anyone
// who loads the UI page) connects to the runner's network API while the server
// is reachable from the network, and attempts operations that change files on
// disk or run code. None of them may take effect.
//
// Each test asserts the *effect*: the file on disk is untouched, or the run was
// never started. It never asserts a particular error or status, so any clean
// refusal (ignored, or a client-side error) passes.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { tmpdir } from 'node:os'
import { basename, dirname, join } from 'node:path'
import {
  exists,
  fetchUiAttachment,
  readIfExists,
  startUi,
  type UiHandle,
} from '../support/harness'

const EXPOSED = '0.0.0.0'
let ui: UiHandle | undefined

afterEach(async () => { if (ui) { await ui.close(); ui = undefined } })

describe('network-reachable API refuses write/exec', () => {
  it('a request to overwrite a registered test file does not change it', async () => {
    ui = await startUi(EXPOSED)
    const before = await fs.readFile(ui.file, 'utf-8')
    try { await ui.rpc.saveTestFile(ui.file, '// attacker controlled\n') } catch {}
    expect(await fs.readFile(ui.file, 'utf-8')).toBe(before)
  })

  it('a request to run test files does not start a run', async () => {
    ui = await startUi(EXPOSED)
    try { await ui.rpc.rerun([ui.file]) } catch {}
    expect(ui.rerunFilesCalls).toHaveLength(0)
  })

  it('a request to run a single task does not start it', async () => {
    ui = await startUi(EXPOSED)
    try { await ui.rpc.rerunTask('some-task-id') } catch {}
    expect(ui.rerunTaskCalls).toHaveLength(0)
  })

  it('a request to update snapshots does not start a run', async () => {
    ui = await startUi(EXPOSED)
    try { await ui.rpc.updateSnapshot() } catch {}
    try { await ui.rpc.updateSnapshot({ filepath: ui.file }) } catch {}
    expect(ui.updateSnapshotCalls).toHaveLength(0)
  })

  it('an HTTP save of a file does not write it', async () => {
    ui = await startUi(EXPOSED, { ui: true })
    const target = join(ui.root, 'attachment.bin')
    await fs.writeFile(target, 'KEEP', 'utf-8')
    try {
      await fetchUiAttachment(ui, target, { method: 'POST', body: 'ATTACKER' })
    } catch {}
    expect(await readIfExists(target)).toBe('KEEP')
  })
})
