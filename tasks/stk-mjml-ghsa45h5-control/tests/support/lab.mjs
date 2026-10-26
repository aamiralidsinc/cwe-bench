// Shared helpers for the hidden suites. Everything here uses only the Node
// standard library: the tests must not depend on product code to build their
// inputs, expected values or clean-ups.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawn, spawnSync } from 'node:child_process'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'

export const WORKSPACE = process.env.HARNESS_WORKSPACE || '/workspace'
export const CLI = path.join(WORKSPACE, 'packages', 'mjml', 'bin', 'mjml')
export const PROBE = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fsprobe.cjs')

const requireFromWorkspace = createRequire(path.join(WORKSPACE, 'entry.js'))
export const mjml2html = requireFromWorkspace('mjml')
export const MJMLParser = requireFromWorkspace('mjml-parser-xml')

export const OUTSIDE_MARKER = 'OUTSIDE-SECRET-MARKER'
export const SIBLING_MARKER = 'SIBLING-SECRET-MARKER'
export const INSIDE_MARKER = 'INSIDE-LEGIT-MARKER'

export const template = include =>
  `<mjml><mj-body><mj-section><mj-column><mj-include path="${include}" /></mj-column></mj-section></mj-body></mjml>`

export function makeLab() {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'mjml-include-lab-'))
  const project = path.join(base, 'project')
  const secret = path.join(base, 'secret')
  const sibling = `${project}-sibling`
  const created = [base]

  fs.mkdirSync(project)
  fs.mkdirSync(secret)
  fs.mkdirSync(sibling)
  fs.mkdirSync(path.join(project, 'sub'))
  fs.mkdirSync(path.join(project, 'sub', 'deep'))

  fs.writeFileSync(path.join(secret, 'outside.mjml'), `<mj-text>${OUTSIDE_MARKER}</mj-text>`)
  fs.writeFileSync(path.join(sibling, 'secret.mjml'), `<mj-text>${SIBLING_MARKER}</mj-text>`)
  fs.writeFileSync(path.join(project, 'ok.mjml'), `<mj-text>${INSIDE_MARKER}</mj-text>`)
  fs.writeFileSync(path.join(project, 'plain.txt'), `<mj-text>${INSIDE_MARKER}</mj-text>`)
  fs.writeFileSync(path.join(project, 'inner-target.mjml'), `<mj-text>${INSIDE_MARKER}</mj-text>`)
  fs.symlinkSync(path.join(secret, 'outside.mjml'), path.join(project, 'link.mjml'))
  fs.symlinkSync(path.join(project, 'inner-target.mjml'), path.join(project, 'inner-link.mjml'))

  return {
    base,
    project,
    secret,
    sibling,
    outsideFile: path.join(secret, 'outside.mjml'),
    siblingFile: path.join(sibling, 'secret.mjml'),
    cleanup() {
      for (const entry of created) {
        try {
          fs.rmSync(entry, { recursive: true, force: true })
        } catch (e) {
          /* best effort */
        }
      }
    },
  }
}

// Record every filesystem read the current process makes while the recorder is
// active. The product is required in the same process, so patching node:fs is
// enough to observe what the parser reads.
export function recordReads() {
  const reads = []
  const original = {
    readFileSync: fs.readFileSync,
    readFile: fs.readFile,
    openSync: fs.openSync,
    open: fs.open,
    createReadStream: fs.createReadStream,
  }

  const record = value => {
    if (typeof value === 'string' || value instanceof URL) reads.push(String(value))
    else if (ArrayBuffer.isView(value)) reads.push(Buffer.from(value).toString())
  }

  fs.readFileSync = function (target, ...rest) {
    record(target)
    return original.readFileSync.call(this, target, ...rest)
  }
  fs.readFile = function (target, ...rest) {
    record(target)
    return original.readFile.call(this, target, ...rest)
  }
  fs.openSync = function (target, ...rest) {
    record(target)
    return original.openSync.call(this, target, ...rest)
  }
  fs.open = function (target, ...rest) {
    record(target)
    return original.open.call(this, target, ...rest)
  }
  fs.createReadStream = function (target, ...rest) {
    record(target)
    return original.createReadStream.call(this, target, ...rest)
  }

  const canonical = target => {
    const absolute = path.resolve(target)
    try {
      return fs.realpathSync(absolute)
    } catch (e) {
      return absolute
    }
  }

  const originalRealpath = fs.realpathSync
  return {
    reads,
    // Did the process touch this physical file, directly or through a link?
    touched(file) {
      const wanted = canonical(file)
      return reads.some(read => canonical(read) === wanted)
    },
    restore() {
      fs.readFileSync = original.readFileSync
      fs.readFile = original.readFile
      fs.openSync = original.openSync
      fs.open = original.open
      fs.createReadStream = original.createReadStream
      fs.realpathSync = originalRealpath
    },
  }
}

export function outputOf(result) {
  if (typeof result === 'string') return result
  return (result && result.html) || ''
}

export function messagesOf(result) {
  const errors = (result && result.errors) || []
  return errors.map(e => [e.formattedMessage, e.message].filter(Boolean).join('\n')).join('\n')
}

export function runCli(args, { cwd, env = {}, timeout = 60000 } = {}) {
  return spawnSync(process.execPath, [CLI, ...args], {
    cwd,
    env: { ...process.env, ...env },
    encoding: 'utf8',
    timeout,
    killSignal: 'SIGKILL',
  })
}

export function runNodeScript(source, { cwd, env = {}, timeout = 60000 } = {}) {
  return spawnSync(process.execPath, ['-e', source], {
    cwd,
    env: { ...process.env, ...env },
    encoding: 'utf8',
    timeout,
    killSignal: 'SIGKILL',
  })
}

export function probeEnv(logPath) {
  return { NODE_OPTIONS: `--require ${PROBE}`, FS_PROBE_LOG: logPath }
}

export function readProbeLog(logPath) {
  try {
    return fs
      .readFileSync(logPath, 'utf8')
      .split('\n')
      .map(line => line.replace(/^open:/, ''))
      .filter(Boolean)
  } catch (e) {
    return []
  }
}

export const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))

export async function waitFor(predicate, { timeout = 20000, interval = 100 } = {}) {
  const started = Date.now()
  for (;;) {
    if (predicate()) return true
    if (Date.now() - started > timeout) return false
    await sleep(interval)
  }
}

// Start the CLI in watch mode as its own process group so the whole tree can be
// killed. The probe records every file the watcher reads.
export function startWatch({ input, output, cwd, probeLog, logFile }) {
  const log = fs.openSync(logFile, 'a')
  const child = spawn(process.execPath, [CLI, '-w', input, '-o', output], {
    cwd,
    env: { ...process.env, ...probeEnv(probeLog) },
    stdio: ['ignore', log, log],
    detached: true,
  })
  const stop = () => {
    try {
      process.kill(-child.pid, 'SIGKILL')
    } catch (e) {
      /* already gone */
    }
    try {
      child.kill('SIGKILL')
    } catch (e) {
      /* already gone */
    }
    try {
      fs.closeSync(log)
    } catch (e) {
      /* already closed */
    }
  }
  return { child, stop }
}

export function writeTemplate(dir, name, include) {
  const file = path.join(dir, name)
  fs.writeFileSync(file, template(include))
  return file
}
