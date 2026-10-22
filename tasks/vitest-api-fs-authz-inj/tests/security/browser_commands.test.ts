// The browser-mode side of the same product exposes a second set of
// file-touching operations. A client that holds the API token (which the
// product hands to anyone who loads the page) connects to the browser API
// WebSocket as the product's own browser client does, and requests the file
// commands through it. When the server is reachable from the network, none of
// the file-changing commands may take effect; read-only access is unaffected
// and is checked in the functional suite.
//
// Each test asserts the effect on disk, not any particular error, so any clean
// refusal (a thrown client error, an ignored request) passes.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { join } from 'node:path'
import { startBrowserProject, readIfExists, type BrowserHandle } from '../support/harness'

const EXPOSED = '0.0.0.0'
let browser: BrowserHandle | undefined

afterEach(async () => { if (browser) { await browser.close(); browser = undefined } })

async function command(name: string, ...payload: unknown[]) {
  return browser!.rpc.triggerCommand(browser!.sessionId, name, join(browser!.root, 'sample.test.ts'), payload)
}

describe('network-reachable browser file commands refuse writes', () => {
  it('creating a file does not take effect', async () => {
    browser = await startBrowserProject(EXPOSED)
    const target = join(browser.root, 'created.txt')
    try { await command('writeFile', 'created.txt', 'attacker', undefined) } catch {}
    expect(await readIfExists(target)).toBeNull()
  })

  it('appending to a file does not change it', async () => {
    browser = await startBrowserProject(EXPOSED)
    const target = join(browser.root, 'log.txt')
    await fs.writeFile(target, 'KEEP', 'utf-8')
    try { await command('appendFile', 'log.txt', 'attacker') } catch {}
    expect(await fs.readFile(target, 'utf-8')).toBe('KEEP')
  })

  it('removing a file does not delete it', async () => {
    browser = await startBrowserProject(EXPOSED)
    const target = join(browser.root, 'keep.txt')
    await fs.writeFile(target, 'KEEP', 'utf-8')
    try { await command('removeFile', 'keep.txt') } catch {}
    expect(await readIfExists(target)).toBe('KEEP')
  })
})
