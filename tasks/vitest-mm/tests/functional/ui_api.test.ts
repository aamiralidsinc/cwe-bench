// Legitimate local use of the runner API must keep working exactly as before:
// when the server is only bound locally, the editor can save a test file, run
// tests, and write snapshots. Read-only access keeps working even when the
// server is reachable from the network. A fix that refuses these breaks the
// product.
//
// The producer shape is covered too: a bare port number, an unset host, and
// localhost all mean "local", so writes keep working under each of them.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { dirname, join } from 'node:path'
import {
  fetchUiAttachment,
  readIfExists,
  startUi,
  type UiHandle,
} from '../support/harness'

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

  it('runs a single task when asked', async () => {
    ui = await startUi(LOCAL)
    await ui.rpc.rerunTask('local-task-id')
    expect(ui.rerunTaskCalls).toEqual(['local-task-id'])
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
    expect(await readIfExists(unregistered)).toBeNull()
  })

  it('saves a file over HTTP when the server is local', async () => {
    ui = await startUi(LOCAL, { ui: true })
    const target = join(ui.root, 'saved.bin')
    await fs.writeFile(target, 'OLD', 'utf-8')
    await fetchUiAttachment(ui, target, { method: 'POST', body: 'NEW' })
    expect(await fs.readFile(target, 'utf-8')).toBe('NEW')
  })

  it('saves a test file when the host is unset', async () => {
    ui = await startUi(undefined)
    const content = '// edited with an unset host\n'
    await ui.rpc.saveTestFile(ui.file, content)
    expect(await fs.readFile(ui.file, 'utf-8')).toBe(content)
  })

  it('saves a test file when the host is localhost', async () => {
    ui = await startUi('localhost')
    const content = '// edited on localhost\n'
    await ui.rpc.saveTestFile(ui.file, content)
    expect(await fs.readFile(ui.file, 'utf-8')).toBe(content)
  })

  it('saves a test file when the api is given as a bare port number', async () => {
    ui = await startUi(undefined, { api: 0 })
    const content = '// edited with a numeric api\n'
    await ui.rpc.saveTestFile(ui.file, content)
    expect(await fs.readFile(ui.file, 'utf-8')).toBe(content)
  })
})

describe('network-reachable runner API keeps read-only access', () => {
  it('reads a registered test file', async () => {
    ui = await startUi(EXPOSED)
    const expected = await fs.readFile(ui.file, 'utf-8')
    expect(await ui.rpc.readTestFile(ui.file)).toBe(expected)
  })
})
