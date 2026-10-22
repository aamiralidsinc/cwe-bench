// Legitimate local use of the browser-mode file commands must keep working
// when writes are allowed, and reading files must keep working even when
// writes are disabled (only changes to disk are restricted, not reads). The
// commands are requested over the browser API WebSocket exactly as the
// product's own browser client requests them.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { join } from 'node:path'
import { startBrowserProject, seedTest, type BrowserHandle } from '../support/harness'

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

  it('writes and removes a snapshot file when writing is allowed', async () => {
    browser = await startBrowserProject(LOCAL)
    const target = join(browser.root, '__snapshots__', 'sample.test.ts.snap')
    await browser.rpc.saveSnapshotFile(target, 'snapshot written by the local editor\n')
    expect(await fs.readFile(target, 'utf-8')).toBe('snapshot written by the local editor\n')
    await browser.rpc.removeSnapshotFile(target)
    await expect(fs.access(target)).rejects.toThrow()
  })

  it('records a test artifact attachment when writing is allowed', async () => {
    browser = await startBrowserProject(LOCAL)
    await fs.writeFile(join(browser.root, 'attachment.txt'), 'attachment', 'utf-8')
    const testId = seedTest(browser)
    await browser.rpc.onTaskArtifactRecord(testId, {
      type: 'verifier:attachment',
      attachments: [{ path: 'attachment.txt', contentType: 'text/plain' }],
    })
    const attachmentsDir = browser.project.config.attachmentsDir
    const entries = await fs.readdir(attachmentsDir)
    expect(entries).toHaveLength(1)
    expect(await fs.readFile(join(attachmentsDir, entries[0]), 'utf-8')).toBe('attachment')
  })

  it('writes a file inside the project when file serving is relaxed', async () => {
    browser = await startBrowserProject(LOCAL, { relaxedFileServing: true })
    await command('writeFile', 'inside.txt', 'hello', undefined)
    expect(await fs.readFile(join(browser.root, 'inside.txt'), 'utf-8')).toBe('hello')
  })

  it('writes through a link that stays inside the project', async () => {
    browser = await startBrowserProject(LOCAL)
    const real = join(browser.root, 'real.txt')
    await fs.writeFile(real, 'KEEP', 'utf-8')
    await fs.symlink(real, join(browser.root, 'alias.txt'))
    await command('writeFile', 'alias.txt', 'hello', undefined)
    expect(await fs.readFile(real, 'utf-8')).toBe('hello')
  })

  it('writes through a linked directory that stays inside the project', async () => {
    browser = await startBrowserProject(LOCAL)
    const dir = join(browser.root, 'inside-dir')
    await fs.mkdir(dir)
    await fs.symlink(dir, join(browser.root, 'alias-dir'))
    await command('writeFile', 'alias-dir/out.txt', 'hello', undefined)
    expect(await fs.readFile(join(dir, 'out.txt'), 'utf-8')).toBe('hello')
  })

  it('writes a benchmark result when writing is allowed', async () => {
    browser = await startBrowserProject(LOCAL)
    await browser.rpc.writeBenchmarkResult('results/bench.json', 'result')
    expect(await fs.readFile(join(browser.root, 'results', 'bench.json'), 'utf-8')).toBe('result')
  })
})

describe('an exposed browser API still serves reads when the runner API is local', () => {
  it('reads a file', async () => {
    browser = await startBrowserProject(EXPOSED, { rootHost: LOCAL })
    await fs.writeFile(join(browser.root, 'data.txt'), 'readable', 'utf-8')
    const content = await command('readFile', 'data.txt', { encoding: 'utf-8' })
    expect(content).toBe('readable')
  })
})
