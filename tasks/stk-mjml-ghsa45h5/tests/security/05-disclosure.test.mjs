// A failed or refused include must not put the resolved filesystem location of
// the target into the generated email, the validation report or the
// command-line diagnostics. The target may only be named as the template wrote
// it.
import test, { after } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import {
  makeLab,
  mjml2html,
  outputOf,
  messagesOf,
  runCli,
  template,
  writeTemplate,
} from '../support/lab.mjs'

const lab = makeLab()
after(() => lab.cleanup())

test('a missing target inside the root is not located in the output', () => {
  const result = mjml2html(template('./missing.mjml'), {
    filePath: lab.project,
    actualPath: path.join(lab.project, 'page.mjml'),
  })
  const resolved = path.join(lab.project, 'missing.mjml')
  const combined = `${outputOf(result)}\n${messagesOf(result)}`
  assert.ok(!combined.includes(resolved), 'the output disclosed the resolved target')
  assert.ok(combined.includes('./missing.mjml'), 'the failure no longer names the written target')
})

test('a missing target outside the root is not located in the output', () => {
  const result = mjml2html(template('../secret/nothing-here.mjml'), {
    filePath: lab.project,
    actualPath: path.join(lab.project, 'page.mjml'),
  })
  const resolved = path.join(lab.secret, 'nothing-here.mjml')
  const combined = `${outputOf(result)}\n${messagesOf(result)}`
  assert.ok(!combined.includes(resolved), 'the output disclosed the resolved target')
})

test('the validation report does not locate a missing target', () => {
  writeTemplate(lab.project, 'broken.mjml', './missing.mjml')
  const run = runCli(['-v', 'broken.mjml'], { cwd: lab.project })
  const resolved = path.join(lab.project, 'missing.mjml')
  const combined = `${run.stdout}\n${run.stderr}`
  assert.ok(!combined.includes(resolved), 'the validation report disclosed the resolved target')
  assert.ok(combined.includes('./missing.mjml'), 'the validation report no longer names the written target')
})

test('the command-line render does not locate a missing target outside the root', () => {
  writeTemplate(lab.project, 'outside-broken.mjml', '../secret/nothing-here.mjml')
  const run = runCli(['outside-broken.mjml', '-s'], { cwd: lab.project })
  const resolved = path.join(lab.secret, 'nothing-here.mjml')
  const combined = `${run.stdout}\n${run.stderr}`
  assert.ok(!combined.includes(resolved), 'the render output disclosed the resolved target')
})
