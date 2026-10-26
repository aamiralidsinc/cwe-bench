'use strict';
// Contract-source escaping: a supplied string must stay inside the Solidity literal the wizard
// puts it in and must decode back to exactly the supplied text.
const test = require('node:test');
const assert = require('node:assert');
const {
  src,
  assertMarkerContained,
  literalAfter,
  literalAfterBoth,
  zipKeyByRegex,
} = require('../support/literals.cjs');

const { erc20, erc1155 } = src('api.ts');
const { zipFoundry } = src('zip-foundry.ts');
const { buildERC20 } = src('erc20.ts');

const MARK = 'MALICIOUS_7c1a.back';

function constructorLiteral(source, parent) {
  const found = literalAfterBoth(source, 'constructor()', parent + '(', 'sol');
  assert.ok(found.literal, `no readable Solidity literal in the generated constructor (${found.why})`);
  return found.literal.value;
}

test('contract source: a non-ASCII name with a backslash and quote cannot leave its literal', () => {
  const name = 'é\\"); ' + MARK + '(); //';
  let out;
  try {
    out = erc20.print({ name, symbol: 'MTK' });
  } catch (e) {
    return; // a client error is an acceptable refusal
  }
  assertMarkerContained(assert, out, MARK, 'sol', 'generated contract');
});

test('contract source: a symbol with non-ASCII, backslash and quote cannot leave its literal', () => {
  const symbol = 'é\\"); ' + MARK + '(); //';
  let out;
  try {
    out = erc20.print({ name: 'My Token', symbol });
  } catch (e) {
    return;
  }
  assertMarkerContained(assert, out, MARK, 'sol', 'generated contract symbol');
});

test('contract source: an ERC1155 uri with non-ASCII, backslash and quote cannot leave its literal', () => {
  const uri = 'é\\"); ' + MARK + '(); //';
  let out;
  try {
    out = erc1155.print({ name: 'My Token', uri });
  } catch (e) {
    return;
  }
  assertMarkerContained(assert, out, MARK, 'sol', 'generated contract uri');
});

test('contract source: a line break inside non-ASCII text cannot leave its literal', () => {
  const name = 'ć\n' + MARK + '(); //';
  let out;
  try {
    out = erc20.print({ name, symbol: 'MTK' });
  } catch (e) {
    return;
  }
  assertMarkerContained(assert, out, MARK, 'sol', 'generated contract');
});

test('contract source: a backspace in a name is emitted as valid Solidity', () => {
  const name = 'A\x08B';
  let out;
  try {
    out = erc20.print({ name, symbol: 'MTK' });
  } catch (e) {
    return;
  }
  assert.equal(constructorLiteral(out, 'ERC20'), name);
});

test('contract source: DEL in a name is emitted as valid Solidity', () => {
  const name = 'A\x7fB';
  let out;
  try {
    out = erc20.print({ name, symbol: 'MTK' });
  } catch (e) {
    return;
  }
  assert.equal(constructorLiteral(out, 'ERC20'), name);
});

test('generated test project: a non-ASCII name with a backslash and quote decodes exactly', async () => {
  const name = 'Tokeć\\"';
  const opts = { kind: 'ERC20', name, symbol: 'MTK' };
  let zip;
  try {
    zip = await zipFoundry(buildERC20(opts), opts);
  } catch (e) {
    return;
  }
  const sol = await zip.file(zipKeyByRegex(zip, /^test\/.+\.t\.sol$/)).async('string');
  const found = literalAfter(sol, 'instance.name(), ', 'sol');
  assert.ok(found.literal, `the generated test does not contain a valid name literal (${found.why})`);
  assert.equal(found.literal.value, name);
});
