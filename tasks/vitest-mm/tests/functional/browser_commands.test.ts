// Legitimate local use of the browser-mode file commands must keep working
// when writes are allowed, and reading files must keep working even when
// writes are disabled (only changes to disk are restricted, not reads).
// Exporting an artifact is the same kind of local, project-scoped write.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { join } from 'node:path'
import {
  readFile,
  removeFile,
  writeFile,
} from '@verifier/browser-commands'
import { exportArtifact } from '@verifier/browser-artifacts'
import {
  exists,
  readIfExists,
  startBrowserProject,
} from '../support/harness'

const LOCAL = '127.0.0.1'
const EXPOSED = '0.0.0.0'
let cleanup: (() => Promise<void>) | undefined

afterEach(async () => { if (cleanup) { await cleanup(); cleanup = undefined } })

describe('local browser file commands keep working', () => {
  it('writes a file when writing is allowed', async () => {
    const { project, root, close } = await startBrowserProject(LOCAL)
    cleanup = close
    await writeFile({ project } as any, 'out.txt', 'hello', undefined as any)
    expect(await fs.readFile(join(root, 'out.txt'), 'utf-8')).toBe('hello')
  })

  it('removes a file when writing is allowed', async () => {
    const { project, root, close } = await startBrowserProject(LOCAL)
    cleanup = close
    await fs.writeFile(join(root, 'gone.txt'), 'x', 'utf-8')
    await removeFile({ project } as any, 'gone.txt')
    expect(await exists(join(root, 'gone.txt'))).toBe(false)
  })

  it('writes a file inside the project even when file serving is widened', async () => {
    const { project, root, close } = await startBrowserProject(LOCAL, { fsStrict: false })
    cleanup = close
    await writeFile({ project } as any, 'inside.txt', 'ok', undefined as any)
    expect(await fs.readFile(join(root, 'inside.txt'), 'utf-8')).toBe('ok')
  })

  it('exports an artifact into the project', async () => {
    const { project, root, close } = await startBrowserProject(LOCAL)
    cleanup = close
    await exportArtifact({ project } as any, 'reports/artifact.txt', 'evidence')
    expect(await fs.readFile(join(root, 'reports/artifact.txt'), 'utf-8')).toBe('evidence')
  })

  it('reads a file even when writing is disabled', async () => {
    const { project, root, close } = await startBrowserProject(EXPOSED)
    cleanup = close
    await fs.writeFile(join(root, 'data.txt'), 'readable', 'utf-8')
    const content = await readFile({ project } as any, 'data.txt', { encoding: 'utf-8' } as any)
    expect(content).toBe('readable')
  })

  it('writes a file when the browser api is not configured separately', async () => {
    const { project, root, close } = await startBrowserProject(LOCAL, { unsetBrowserApi: true })
    cleanup = close
    await writeFile({ project } as any, 'inherited.txt', 'ok', undefined as any)
    expect(await readIfExists(join(root, 'inherited.txt'))).toBe('ok')
  })
})
