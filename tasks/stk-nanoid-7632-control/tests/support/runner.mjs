#!/usr/bin/env node
/*
 * Hidden-suite runner. Usage:
 *     node runner.mjs <security|functional> <output.xml>
 *
 * Loads the case table for the group, runs every case, and writes a JUnit XML file the scorer
 * reads. A call case runs in its own child process with a hard timeout: a call that never returns
 * is the reported failure, so it is recorded as a failed case and the suite carries on.
 *
 * Expected values are literals in the case tables; no product code is used to compute them.
 */
import { spawnSync } from 'node:child_process'
import { fileURLToPath, pathToFileURL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'

const GROUP = process.argv[2]
const OUT = process.argv[3]
const ROOT = process.env.PRODUCT_ROOT || '/workspace'
const CASE_TIMEOUT = Number(process.env.CASE_TIMEOUT_MS || 4000)
const HERE = path.dirname(fileURLToPath(import.meta.url))
const WORKER = path.join(HERE, 'worker.mjs')

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function writeXml(results) {
  const failures = results.filter(r => !r.ok).length
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<testsuite name="${esc(GROUP)}" tests="${results.length}" failures="${failures}" errors="0" skipped="0">`
  ]
  for (const r of results) {
    if (r.ok) {
      lines.push(`  <testcase classname="${esc(r.classname)}" name="${esc(r.name)}"/>`)
    } else {
      const msg = r.message || 'failed'
      lines.push(`  <testcase classname="${esc(r.classname)}" name="${esc(r.name)}">`)
      lines.push(`    <failure message="${esc(msg).slice(0, 500)}">${esc(msg).slice(0, 4000)}</failure>`)
      lines.push('  </testcase>')
    }
  }
  lines.push('</testsuite>', '')
  fs.mkdirSync(path.dirname(OUT), { recursive: true })
  fs.writeFileSync(OUT, lines.join('\n'))
}

function timedOut(r) {
  return r.error && r.error.code === 'ETIMEDOUT'
}

function runCall(c) {
  const spec = {
    module: c.module,
    expr: c.expr,
    expect: c.expect
  }
  const payload = Buffer.from(JSON.stringify(spec)).toString('base64')
  const r = spawnSync(process.execPath, [WORKER, payload], {
    timeout: CASE_TIMEOUT,
    killSignal: 'SIGKILL',
    encoding: 'utf8',
    env: { ...process.env, PRODUCT_ROOT: ROOT }
  })
  if (timedOut(r) || r.signal) {
    return {
      classname: 'security/' + c.id,
      name: c.name,
      ok: false,
      message: `the call did not return within ${CASE_TIMEOUT} ms (it kept running and was killed)`
    }
  }
  if (r.status !== 0) {
    return {
      classname: 'security/' + c.id,
      name: c.name,
      ok: false,
      message: `worker exited ${r.status}: ${(r.stderr || '').slice(0, 800)}`
    }
  }
  const line = (r.stdout || '').trim().split('\n').filter(Boolean).pop() || ''
  let parsed
  try {
    parsed = JSON.parse(line)
  } catch (e) {
    return {
      classname: 'security/' + c.id,
      name: c.name,
      ok: false,
      message: `worker produced no result: ${(r.stdout || '').slice(0, 400)} ${(r.stderr || '').slice(0, 400)}`
    }
  }
  return { classname: 'security/' + c.id, name: c.name, ok: !!parsed.ok, message: parsed.detail }
}

function runCli(c) {
  const bin = path.join(ROOT, 'bin', 'nanoid.js')
  const r = spawnSync(process.execPath, [bin, ...(c.args || [])], {
    timeout: CASE_TIMEOUT,
    killSignal: 'SIGKILL',
    encoding: 'utf8',
    cwd: ROOT
  })
  const classname = 'security/' + c.id
  if (timedOut(r) || r.signal) {
    return {
      classname,
      name: c.name,
      ok: false,
      message: `the command did not return within ${CASE_TIMEOUT} ms (it kept running and was killed)`
    }
  }
  const out = (r.stdout || '').trim()
  if (c.expect.kind === 'cli-blocked') {
    // Anything that comes back without printing an ID is a refusal: an error exit or an empty
    // result. No exact status is required.
    const ok = r.status !== 0 || out === ''
    return {
      classname,
      name: c.name,
      ok,
      message: ok
        ? `returned (exit ${r.status}, output ${JSON.stringify(out)})`
        : `printed ${JSON.stringify(out)} with exit ${r.status}`
    }
  }
  if (c.expect.kind === 'cli-length') {
    let ok = out.length === c.expect.value
    if (ok && c.expect.charset) {
      ok = [...out].every(ch => c.expect.charset.includes(ch))
    }
    return {
      classname,
      name: c.name,
      ok,
      message: ok
        ? `printed ${JSON.stringify(out)}`
        : `printed ${JSON.stringify(out)} (exit ${r.status}), expected length ${c.expect.value}${
            c.expect.charset ? ` over ${JSON.stringify(c.expect.charset)}` : ''
          }`
    }
  }
  return { classname, name: c.name, ok: false, message: `unknown expectation ${JSON.stringify(c.expect)}` }
}

function runFunctionalCli(c) {
  const r = runCli({ ...c, id: c.id })
  r.classname = 'functional/' + c.id
  return r
}

async function main() {
  const results = []
  let table
  try {
    table = await import(pathToFileURL(path.join(HERE, '..', GROUP, 'cases.mjs')).href)
  } catch (e) {
    results.push({
      classname: 'harness',
      name: `suite loads: ${GROUP}`,
      ok: false,
      message: `suite error: ${e && (e.stack || e.message)}`
    })
    writeXml(results)
    return
  }
  const cases = table.cases || []
  for (const c of cases) {
    try {
      if (c.kind === 'cli') {
        results.push(GROUP === 'functional' ? runFunctionalCli(c) : runCli(c))
      } else {
        const r = runCall(c)
        if (GROUP === 'functional') r.classname = 'functional/' + c.id
        results.push(r)
      }
    } catch (e) {
      results.push({
        classname: `${GROUP}/${c.id}`,
        name: c.name,
        ok: false,
        message: `runner error: ${e && (e.stack || e.message)}`
      })
    }
  }
  writeXml(results)
}

main().catch(e => {
  try {
    writeXml([{ classname: 'harness', name: 'runner', ok: false, message: String(e && (e.stack || e.message)) }])
  } catch (_) {
    process.exitCode = 1
  }
})
