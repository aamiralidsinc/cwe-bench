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
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { startBrowserProject, readIfExists, seedTest, type BrowserHandle } from '../support/harness'

const EXPOSED = '0.0.0.0'
const LOCAL = '127.0.0.1'
let browser: BrowserHandle | undefined

afterEach(async () => { if (browser) { await browser.close(); browser = undefined } })

async function command(name: string, ...payload: unknown[]) {
  return browser!.rpc.triggerCommand(browser!.sessionId, name, join(browser!.root, 'sample.test.ts'), payload)
}

async function listDir(path: string): Promise<string[]> {
  try { return (await fs.readdir(path)).sort() } catch { return [] }
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

  it('writing a snapshot file does not change it', async () => {
    browser = await startBrowserProject(EXPOSED)
    const target = join(browser.root, '__snapshots__', 'sample.test.ts.snap')
    await fs.mkdir(join(browser.root, '__snapshots__'), { recursive: true })
    await fs.writeFile(target, 'KEEP', 'utf-8')
    try { await browser.rpc.saveSnapshotFile(target, 'attacker controlled\n') } catch {}
    expect(await fs.readFile(target, 'utf-8')).toBe('KEEP')
  })

  it('removing a snapshot file does not delete it', async () => {
    browser = await startBrowserProject(EXPOSED)
    const target = join(browser.root, '__snapshots__', 'sample.test.ts.snap')
    await fs.mkdir(join(browser.root, '__snapshots__'), { recursive: true })
    await fs.writeFile(target, 'KEEP', 'utf-8')
    try { await browser.rpc.removeSnapshotFile(target) } catch {}
    expect(await readIfExists(target)).toBe('KEEP')
  })
})

describe('network-reachable browser API records no artifact files', () => {
  it('recording an artifact with an attachment does not create a file', async () => {
    browser = await startBrowserProject(EXPOSED)
    await fs.writeFile(join(browser.root, 'attachment.txt'), 'attacker', 'utf-8')
    const testId = seedTest(browser)
    const attachmentsDir = browser.project.config.attachmentsDir
    try {
      await browser.rpc.onTaskArtifactRecord(testId, {
        type: 'verifier:attachment',
        attachments: [{ path: 'attachment.txt', contentType: 'text/plain' }],
      })
    } catch {}
    expect(await listDir(attachmentsDir)).toEqual([])
  })

  it('recording an annotation with an attachment does not create a file', async () => {
    browser = await startBrowserProject(EXPOSED)
    await fs.writeFile(join(browser.root, 'attachment.txt'), 'attacker', 'utf-8')
    const testId = seedTest(browser)
    const attachmentsDir = browser.project.config.attachmentsDir
    try {
      await browser.rpc.onTaskArtifactRecord(testId, {
        type: 'internal:annotation',
        annotation: {
          message: 'note',
          attachment: { path: 'attachment.txt', contentType: 'text/plain' },
        },
      })
    } catch {}
    expect(await listDir(attachmentsDir)).toEqual([])
  })
})

describe('an exposed browser API is refused even when the runner API is local', () => {
  it('writing a file does not take effect', async () => {
    browser = await startBrowserProject(EXPOSED, { rootHost: LOCAL })
    const target = join(browser.root, 'inherited.txt')
    try { await command('writeFile', 'inherited.txt', 'attacker', undefined) } catch {}
    expect(await readIfExists(target)).toBeNull()
  })
})

describe('file writes do not follow links that leave the project root', () => {
  it('writing through a link to an outside file does not change it', async () => {
    browser = await startBrowserProject(LOCAL)
    const outside = await fs.mkdtemp(join(tmpdir(), 'vitest-outside-'))
    const target = join(outside, 'target.txt')
    try {
      await fs.writeFile(target, 'KEEP', 'utf-8')
      await fs.symlink(target, join(browser.root, 'link.txt'))
      try { await command('writeFile', 'link.txt', 'attacker', undefined) } catch {}
      expect(await fs.readFile(target, 'utf-8')).toBe('KEEP')
    }
    finally { await fs.rm(outside, { recursive: true, force: true }) }
  })

  it('appending through a link to an outside file does not change it', async () => {
    browser = await startBrowserProject(LOCAL)
    const outside = await fs.mkdtemp(join(tmpdir(), 'vitest-outside-'))
    const target = join(outside, 'target.txt')
    try {
      await fs.writeFile(target, 'KEEP', 'utf-8')
      await fs.symlink(target, join(browser.root, 'append-link.txt'))
      try { await command('appendFile', 'append-link.txt', 'attacker') } catch {}
      expect(await fs.readFile(target, 'utf-8')).toBe('KEEP')
    }
    finally { await fs.rm(outside, { recursive: true, force: true }) }
  })

  it('writing through a linked directory does not create a file', async () => {
    browser = await startBrowserProject(LOCAL)
    const outside = await fs.mkdtemp(join(tmpdir(), 'vitest-outside-'))
    try {
      await fs.symlink(outside, join(browser.root, 'outdir'))
      try { await command('writeFile', 'outdir/created.txt', 'attacker', undefined) } catch {}
      expect(await readIfExists(join(outside, 'created.txt'))).toBeNull()
    }
    finally { await fs.rm(outside, { recursive: true, force: true }) }
  })

  it('removing through a linked directory does not delete a file', async () => {
    browser = await startBrowserProject(LOCAL)
    const outside = await fs.mkdtemp(join(tmpdir(), 'vitest-outside-'))
    const target = join(outside, 'keep.txt')
    try {
      await fs.writeFile(target, 'KEEP', 'utf-8')
      await fs.symlink(outside, join(browser.root, 'outdir'))
      try { await command('removeFile', 'outdir/keep.txt') } catch {}
      expect(await fs.readFile(target, 'utf-8')).toBe('KEEP')
    }
    finally { await fs.rm(outside, { recursive: true, force: true }) }
  })

  it('writing a snapshot file through a link to an outside file does not change it', async () => {
    browser = await startBrowserProject(LOCAL)
    const outside = await fs.mkdtemp(join(tmpdir(), 'vitest-outside-'))
    const target = join(outside, 'target.snap')
    try {
      await fs.writeFile(target, 'KEEP', 'utf-8')
      const link = join(browser.root, '__snapshots__', 'link.snap')
      await fs.mkdir(dirname(link), { recursive: true })
      await fs.symlink(target, link)
      try { await browser.rpc.saveSnapshotFile(link, 'attacker controlled\n') } catch {}
      expect(await fs.readFile(target, 'utf-8')).toBe('KEEP')
    }
    finally { await fs.rm(outside, { recursive: true, force: true }) }
  })
})

describe('network-reachable browser API refuses benchmark result writes', () => {
  it('writing a benchmark result does not create a file', async () => {
    browser = await startBrowserProject(EXPOSED)
    const target = join(browser.root, 'results', 'bench.json')
    try { await browser.rpc.writeBenchmarkResult('results/bench.json', 'attacker') } catch {}
    expect(await readIfExists(target)).toBeNull()
  })
})

describe('relaxed file serving does not let a client escape the project root', () => {
  it('writing outside the project root does not create a file', async () => {
    browser = await startBrowserProject(LOCAL, { relaxedFileServing: true })
    const target = join(dirname(browser.root), 'escaped-write.txt')
    await fs.rm(target, { force: true })
    try { await command('writeFile', '../escaped-write.txt', 'attacker', undefined) } catch {}
    expect(await readIfExists(target)).toBeNull()
  })

  it('removing outside the project root does not delete the file', async () => {
    browser = await startBrowserProject(LOCAL, { relaxedFileServing: true })
    const target = join(dirname(browser.root), 'escaped-remove.txt')
    await fs.writeFile(target, 'KEEP', 'utf-8')
    try { await command('removeFile', '../escaped-remove.txt') } catch {}
    expect(await fs.readFile(target, 'utf-8')).toBe('KEEP')
  })

  it('writing to an absolute path outside the project root does not create a file', async () => {
    browser = await startBrowserProject(LOCAL, { relaxedFileServing: true })
    const target = join(dirname(browser.root), 'escaped-absolute.txt')
    await fs.rm(target, { force: true })
    try { await command('writeFile', target, 'attacker', undefined) } catch {}
    expect(await readIfExists(target)).toBeNull()
  })
})
