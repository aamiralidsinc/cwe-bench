// Legitimate local use of the browser-mode file commands must keep working
// when writes are allowed, and reading files must keep working even when
// writes are disabled (only changes to disk are restricted, not reads). The
// commands are requested over the browser API WebSocket exactly as the
// product's own browser client requests them.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { join } from 'node:path'
import { startBrowserProject, type BrowserHandle } from '../support/harness'

const LOCAL = '127.0.0.1'
const EXPOSED = '0.0.0.0'
let browser: BrowserHandle | undefined

afterEach(async () => { if (browser) { await browser.close(); browser = undefined } })

async function command(name: string, ...payload: unknown[]) {
  return browser!.rpc.triggerCommand(browser!.sessionId, name, join(browser!.root, 'sample.test.ts'), payload)
}

describe('local browser file commands keep working', () => {
  it('writes a file when writing is allowed', async () => {
    browser = await startBrowserProject(LOCAL)
    await command('writeFile', 'out.txt', 'hello', undefined)
    expect(await fs.readFile(join(browser.root, 'out.txt'), 'utf-8')).toBe('hello')
  })

  it('appends to a file when writing is allowed', async () => {
    browser = await startBrowserProject(LOCAL)
    await fs.writeFile(join(browser.root, 'log.txt'), 'A', 'utf-8')
    await command('appendFile', 'log.txt', 'B')
    expect(await fs.readFile(join(browser.root, 'log.txt'), 'utf-8')).toBe('AB')
  })

  it('reads a file even when writing is disabled', async () => {
    browser = await startBrowserProject(EXPOSED)
    await fs.writeFile(join(browser.root, 'data.txt'), 'readable', 'utf-8')
    const content = await command('readFile', 'data.txt', { encoding: 'utf-8' })
    expect(content).toBe('readable')
  })
})
