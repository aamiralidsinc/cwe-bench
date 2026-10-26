#!/usr/bin/env node
// Hidden-suite runner. Usage:
//     node runner.mjs <security|functional> <fetch|xhr> <output.xml>
//
// Loads the product through its public entry point, runs every case for the
// group and transport, and writes the JUnit XML the scorer reads. A case that
// throws is a failure; a case that returns is a pass. Expected values are
// literals in the cases; no product helper computes them.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { createRequire } from 'node:module'

const [, , GROUP, MODE, OUT] = process.argv
const HERE = path.dirname(fileURLToPath(import.meta.url))
const PRODUCT = process.env.PRODUCT_ENTRY || '/workspace/index.js'
const require = createRequire(import.meta.url)

function esc (value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function writeXml (results) {
  const failures = results.filter((r) => !r.ok).length
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<testsuite name="${esc(GROUP + '-' + MODE)}" tests="${results.length}" failures="${failures}" errors="0" skipped="0">`
  ]
  for (const r of results) {
    if (r.ok) {
      lines.push(`  <testcase classname="${esc(r.classname)}" name="${esc(r.name)}"/>`)
    } else {
      const message = (r.message || 'failed').slice(0, 4000)
      lines.push(`  <testcase classname="${esc(r.classname)}" name="${esc(r.name)}">`)
      lines.push(`    <failure message="${esc(message).slice(0, 500)}">${esc(message)}</failure>`)
      lines.push('  </testcase>')
    }
  }
  lines.push('</testsuite>', '')
  fs.mkdirSync(path.dirname(OUT), { recursive: true })
  fs.writeFileSync(OUT, lines.join('\n'))
}

function withTimeout (promise, ms) {
  return Promise.race([
    promise,
    new Promise((resolve, reject) => setTimeout(() => reject(new Error('case timed out after ' + ms + 'ms')), ms))
  ])
}

async function main () {
  const results = []
  let Backend
  try {
    if (MODE === 'xhr') {
      const { XMLHttpRequest } = require('xmlhttprequest')
      globalThis.XMLHttpRequest = XMLHttpRequest
      globalThis.fetch = undefined
    }
    const product = await import(pathToFileURL(PRODUCT).href)
    Backend = product.default
    if (typeof Backend !== 'function') throw new Error('the product did not export the backend class')
  } catch (e) {
    results.push({
      classname: 'Harness',
      name: 'product entry point loads',
      ok: false,
      message: String(e && (e.stack || e.message))
    })
    writeXml(results)
    process.exit(0)
  }

  const casesFile = path.join(HERE, '..', GROUP, MODE === 'xhr' ? 'xhr_cases.mjs' : 'fetch_cases.mjs')
  let cases
  try {
    const factory = (await import(pathToFileURL(casesFile).href)).default
    cases = await factory({ Backend, MODE })
  } catch (e) {
    results.push({
      classname: 'Harness',
      name: 'suite loads: ' + path.basename(casesFile),
      ok: false,
      message: String(e && (e.stack || e.message))
    })
    writeXml(results)
    process.exit(0)
  }

  for (const entry of cases) {
    try {
      await withTimeout(entry.run({ Backend, MODE }), 20000)
      results.push({ classname: entry.classname, name: entry.name, ok: true })
    } catch (e) {
      results.push({
        classname: entry.classname,
        name: entry.name,
        ok: false,
        message: String(e && (e.stack || e.message))
      })
    }
  }

  writeXml(results)
  process.exit(0)
}

main().catch((e) => {
  try {
    writeXml([{ classname: 'Harness', name: 'runner', ok: false, message: String(e && (e.stack || e.message)) }])
  } catch (_) {}
  process.exit(0)
})
