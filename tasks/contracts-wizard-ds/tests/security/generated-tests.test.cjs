'use strict';
// Starter-project files: a supplied name or token URI must stay inside the string literal the
// project generator puts it in, whichever project format is downloaded.
const test = require('node:test');
const assert = require('node:assert');
const { src, literalAfter, literalAfterBoth, zipText, zipKeyByRegex } = require('../support/literals.cjs');

const { zipHardhat } = src('zip-hardhat.ts');
const { zipFoundry } = src('zip-foundry.ts');
const { zipHardhatPolkadot } = src('zip-hardhat-polkadot.ts');
const { buildERC20 } = src('erc20.ts');
const { buildERC1155 } = src('erc1155.ts');

const MARK = 'MALICIOUS_7c1a.back';

test('Hardhat project: a double quote in an ERC20 name cannot leave the test assertion', async () => {
  const name = 'My "Token"; ' + MARK + '(); //';
  const opts = { kind: 'ERC20', name, symbol: 'MTK' };
  let zip;
  try {
    zip = await zipHardhat(buildERC20(opts), opts);
  } catch (e) {
    return;
  }
  const content = await zipText(zip, 'test/test.ts');
  const found = literalAfter(content, '.to.equal(', 'js');
  assert.ok(found.literal, `the generated test has no readable name literal (${found.why})`);
  assert.equal(found.literal.value, name);
});

test('Hardhat project: a double quote in an ERC1155 uri cannot leave the test assertion', async () => {
  const uri = 'https://example.com/"; ' + MARK + '(); //';
  const opts = { kind: 'ERC1155', name: 'My Token', uri };
  let zip;
  try {
    zip = await zipHardhat(buildERC1155(opts), opts);
  } catch (e) {
    return;
  }
  const content = await zipText(zip, 'test/test.ts');
  const found = literalAfter(content, '.to.equal(', 'js');
  assert.ok(found.literal, `the generated test has no readable uri literal (${found.why})`);
  assert.equal(found.literal.value, uri);
});

test('Foundry project: a double quote in an ERC20 name cannot leave the test assertion', async () => {
  const name = 'My "Token"; ' + MARK + '(); //';
  const opts = { kind: 'ERC20', name, symbol: 'MTK' };
  let zip;
  try {
    zip = await zipFoundry(buildERC20(opts), opts);
  } catch (e) {
    return;
  }
  const sol = await zipText(zip, zipKeyByRegex(zip, /^test\/.+\.t\.sol$/));
  const found = literalAfter(sol, 'instance.name(), ', 'sol');
  assert.ok(found.literal, `the generated test has no readable name literal (${found.why})`);
  assert.equal(found.literal.value, name);
});

test('Polkadot project: a double quote in an ERC20 name cannot leave the test assertion', async () => {
  const name = 'My "Token"; ' + MARK + '(); //';
  const opts = { kind: 'ERC20', name, symbol: 'MTK' };
  let zip;
  try {
    zip = await zipHardhatPolkadot(buildERC20(opts), opts);
  } catch (e) {
    return;
  }
  const content = await zipText(zip, 'test/test.ts');
  const found = literalAfter(content, '.to.equal(', 'js');
  assert.ok(found.literal, `the Polkadot test has no readable name literal (${found.why})`);
  assert.equal(found.literal.value, name);
});

test('Foundry project: a double quote in an ERC20 name cannot leave the deploy script', async () => {
  const name = 'My "Token"; ' + MARK + '(); //';
  const opts = { kind: 'ERC20', name, symbol: 'MTK' };
  let zip;
  try {
    zip = await zipFoundry(buildERC20(opts), opts);
  } catch (e) {
    return;
  }
  const sol = await zipText(zip, zipKeyByRegex(zip, /^script\/.+\.s\.sol$/));
  const found = literalAfterBoth(sol, 'vm.startBroadcast();', 'console.log(', 'sol');
  assert.ok(found.literal, `the deploy script has no readable message literal (${found.why})`);
  assert.equal(found.literal.value, 'Deploying ' + name);
});
