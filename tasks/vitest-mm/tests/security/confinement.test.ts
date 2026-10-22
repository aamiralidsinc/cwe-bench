// Confinement (CWE-22). A client must not be able to read or write a file that
// is not part of the project — whichever operation, whichever interface, and
// whatever file-serving settings the project has.
//
// These tests run with the server bound locally (so the network-write rule is
// not what stops them) and with the project's file-serving settings widened,
// and they target a path outside every project directory. A response that
// carries the outside file's contents, or a write that lands outside, is the
// failure. Refusal in any clean form passes.
import { afterEach, describe, expect, it } from 'vitest'
import { promises as fs } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import {
  writeFile,
} from '@verifier/browser-commands'
import { exportArtifact } from '@verifier/browser-artifacts'
import {
  exists,
  fetchBrowserAttachment,
  fetchUiAttachment,
  readIfExists,
  startBrowserProject,
  startUi,
  type BrowserHandle,
  type UiHandle,
} from '../support/harness'

const LOCAL = '127.0.0.1'
let browser: BrowserHandle | undefined
let ui: UiHandle | undefined

afterEach(async () => {
  if (browser) { await browser.close(); browser = undefined }
  if (ui) { await ui.close(); ui = undefined }
})

async function outsideFile(contents: string): Promise<string> {
  const dir = await fs.mkdtemp(join(tmpdir(), 'vitest-outside-'))
  const path = join(dir, 'secret.txt')
  await fs.writeFile(path, contents, 'utf-8')
  return path
}

describe('paths outside the project stay unreachable', () => {
  it('an attachment read does not return a file outside the project', async () => {
    const secret = await outsideFile('SECRET-CONTENT')
    browser = await startBrowserProject(LOCAL, { fsStrict: false })
    const { status, body } = await fetchBrowserAttachment(browser, secret)
    expect(body.includes('SECRET-CONTENT')).toBe(false)
  })

  it('a write command does not create a file outside the project', async () => {
    browser = await startBrowserProject(LOCAL, { fsStrict: false })
    const escaped = join(dirname(browser.root), `escape-${Date.now()}.txt`)
    try {
      await writeFile({ project: browser.project } as any, `../${escaped.split('/').pop()}`, 'X', undefined as any)
    } catch {}
    expect(await exists(escaped)).toBe(false)
  })

  it('an artifact export does not create a file outside the project', async () => {
    browser = await startBrowserProject(LOCAL, { fsStrict: false })
    const escaped = join(dirname(browser.root), `artifact-${Date.now()}.txt`)
    try {
      await exportArtifact({ project: browser.project } as any, `../${escaped.split('/').pop()}`, 'A')
    } catch {}
    expect(await exists(escaped)).toBe(false)
  })

  it('an HTTP save does not write a file outside the project', async () => {
    const secret = await outsideFile('KEEP')
    ui = await startUi(LOCAL, { ui: true, fsStrict: false })
    try {
      await fetchUiAttachment(ui, secret, { method: 'POST', body: 'ATTACKER' })
    } catch {}
    expect(await readIfExists(secret)).toBe('KEEP')
  })
})
