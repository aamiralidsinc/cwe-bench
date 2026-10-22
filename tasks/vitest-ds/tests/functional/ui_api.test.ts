// Legitimate local use of the runner API must keep working exactly as before:
// when the server is only bound locally, the editor can save a test file, run
// tests, and write snapshots. Read-only access keeps working even when the
// server is reachable from the network. A fix that refuses these breaks the product.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { basename, dirname, join } from 'node:path'
import { startUi, type UiHandle } from '../support/harness'

const LOCAL = '127.0.0.1'
const EXPOSED = '0.0.0.0'
let ui: UiHandle | undefined

afterEach(async () => { if (ui) { await ui.close(); ui = undefined } })

describe('local runner API keeps working', () => {
  it('saves an edited test file', async () => {
    ui = await startUi(LOCAL)
    const content = '// edited by the local editor\n'
    await ui.rpc.saveTestFile(ui.file, content)
    expect(await fs.readFile(ui.file, 'utf-8')).toBe(content)
  })

  it('runs test files when asked', async () => {
    ui = await startUi(LOCAL)
    await ui.rpc.rerun([ui.file])
    expect(ui.rerunFilesCalls).toHaveLength(1)
    expect(ui.rerunFilesCalls[0]).toContain(ui.file)
  })

  it('writes the snapshot file of a registered test file', async () => {
    ui = await startUi(LOCAL)
    const snapshotFile = join(dirname(ui.file), '__snapshots__', `${basename(ui.file)}.snap`)
    const content = '// snapshot written by the local editor\n'
    await ui.rpc.saveSnapshotFile(ui.file, content)
    expect(await fs.readFile(snapshotFile, 'utf-8')).toBe(content)
  })

  it('updates snapshots when asked', async () => {
    ui = await startUi(LOCAL)
    await ui.rpc.updateSnapshot()
    expect(ui.updateSnapshotCalls).toHaveLength(1)
  })

  it('still rejects saving a file that was never registered', async () => {
    ui = await startUi(LOCAL)
    const unregistered = ui.file + '.not-registered.ts'
    let threw = false
    try { await ui.rpc.saveTestFile(unregistered, 'x') } catch { threw = true }
    expect(threw).toBe(true)
    let exists = true
    try { await fs.access(unregistered) } catch { exists = false }
    expect(exists).toBe(false)
  })
})

describe('network-reachable runner API keeps read-only access', () => {
  it('reads a registered test file', async () => {
    ui = await startUi(EXPOSED)
    const expected = await fs.readFile(ui.file, 'utf-8')
    expect(await ui.rpc.readTestFile(ui.file)).toBe(expected)
  })
})
