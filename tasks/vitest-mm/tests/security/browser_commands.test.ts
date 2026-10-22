// The browser-mode file commands are reached by test code running in the
// browser, through the same network-reachable server. While that server is
// reachable from the network, none of them may create, modify or delete a file.
//
// Every test asserts the effect on disk only. A clean refusal in any form passes.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { join } from 'node:path'
import {
  removeFile,
  writeFile,
} from '@verifier/browser-commands'
import { exportArtifact } from '@verifier/browser-artifacts'
import { exists, startBrowserProject } from '../support/harness'

const EXPOSED = '0.0.0.0'
let cleanup: (() => Promise<void>) | undefined

afterEach(async () => { if (cleanup) { await cleanup(); cleanup = undefined } })

describe('network-reachable browser commands refuse write/delete', () => {
  it('creating a file does not take effect', async () => {
    const { project, root, close } = await startBrowserProject(EXPOSED)
    cleanup = close
    try { await writeFile({ project } as any, 'created.txt', 'attacker', undefined as any) } catch {}
    expect(await exists(join(root, 'created.txt'))).toBe(false)
  })

  it('removing a file does not delete it', async () => {
    const { project, root, close } = await startBrowserProject(EXPOSED)
    cleanup = close
    const target = join(root, 'keep.txt')
    await fs.writeFile(target, 'KEEP', 'utf-8')
    try { await removeFile({ project } as any, 'keep.txt') } catch {}
    expect(await fs.readFile(target, 'utf-8')).toBe('KEEP')
  })

  it('exporting an artifact does not create it', async () => {
    const { project, root, close } = await startBrowserProject(EXPOSED)
    cleanup = close
    try { await exportArtifact({ project } as any, 'artifact.txt', 'attacker') } catch {}
    expect(await exists(join(root, 'artifact.txt'))).toBe(false)
  })
})
