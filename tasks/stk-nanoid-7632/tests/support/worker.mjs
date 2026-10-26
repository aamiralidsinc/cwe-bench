#!/usr/bin/env node
/*
 * One hidden case, in its own process. The runner starts this file with the case as base64 JSON
 * and kills it if it does not finish; the case's call is therefore allowed to block without
 * blocking the suite.
 *
 * The product is loaded through the module the case names, from PRODUCT_ROOT (the restored
 * project). Expected values are literals from the case table; the worker never derives an
 * expectation from the product.
 */
import { pathToFileURL } from 'node:url'
import path from 'node:path'

const spec = JSON.parse(Buffer.from(process.argv[2], 'base64').toString('utf8'))
const root = process.env.PRODUCT_ROOT || '/workspace'

function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n')
}

// A byte source of the requested length, for cases that inject their own random generator.
function zeros(n) {
  const len = Number.isFinite(Number(n)) ? Math.max(0, Math.trunc(Number(n))) : 0
  return new Uint8Array(len)
}

// The bundler build reads the global web crypto object. Replace it with a fixed sequence so the
// case result does not depend on the host's entropy.
if (String(spec.module).includes('browser')) {
  Object.defineProperty(globalThis, 'crypto', {
    configurable: true,
    value: {
      getRandomValues(array) {
        for (let i = 0; i < array.length; i++) array[i] = (i * 37 + 11) & 255
        return array
      }
    }
  })
}

let m
try {
  m = await import(pathToFileURL(path.join(root, spec.module)).href)
} catch (e) {
  emit({ ok: false, detail: `could not load ${spec.module}: ${e && (e.stack || e.message)}` })
  process.exit(0)
}

let value
try {
  // Direct eval so the expression sees the product module (`m`) and the helpers above.
  value = eval(spec.expr)
} catch (e) {
  emit({ ok: false, detail: `call threw ${e && (e.stack || e.message)}` })
  process.exit(0)
}

const want = spec.expect
let ok = false
if (want.kind === 'empty') {
  ok = typeof value === 'string' && value === ''
} else if (want.kind === 'length') {
  ok = typeof value === 'string' && value.length === want.value
} else if (want.kind === 'lengthIn') {
  ok = typeof value === 'string' && want.values.includes(value.length)
} else if (want.kind === 'equals') {
  ok = value === want.value
} else {
  emit({ ok: false, detail: `unknown expectation ${JSON.stringify(want)}` })
  process.exit(0)
}

emit({
  ok,
  detail: ok
    ? `returned ${JSON.stringify(value)}`
    : `returned ${JSON.stringify(value)} (${typeof value}), expected ${
        want.kind === 'empty' ? 'the empty string' : JSON.stringify(want)
      }`
})
