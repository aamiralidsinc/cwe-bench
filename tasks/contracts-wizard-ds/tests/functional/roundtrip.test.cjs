'use strict';
// Legitimate values keep working: the wizard must still copy them into the generated files
// exactly, and a generated literal must decode back to the supplied text.
const test = require('node:test');
const assert = require('node:assert');
const {
  src,
  literalAfter,
  literalAfterBoth,
  zipText,
  zipKeyByRegex,
} = require('../support/literals.cjs');

const { erc20, erc1155, erc721 } = src('api.ts');
const { zipHardhat } = src('zip-hardhat.ts');
const { zipFoundry } = src('zip-foundry.ts');
const { zipHardhatPolkadot } = src('zip-hardhat-polkadot.ts');
const { buildERC20 } = src('erc20.ts');
const { buildERC1155 } = src('erc1155.ts');

function constructorLiteral(source, parent) {
  const found = literalAfterBoth(source, 'constructor()', parent + '(', 'sol');
  assert.ok(found.literal, `no readable Solidity literal in the generated constructor (${found.why})`);
  return found.literal.value;
}

test('Hardhat project: a plain ERC20 name is preserved in the generated test', async () => {
  const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK' };
  const zip = await zipHardhat(buildERC20(opts), opts);
  const content = await zipText(zip, 'test/test.ts');
  const found = literalAfter(content, '.to.equal(', 'js');
  assert.ok(found.literal, `plain name missing from the generated test (${found.why})`);
  assert.equal(found.literal.value, 'My Token');
});

test('Foundry project: a plain ERC20 name is preserved in the generated test', async () => {
  const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK' };
  const zip = await zipFoundry(buildERC20(opts), opts);
  const sol = await zipText(zip, zipKeyByRegex(zip, /^test\/.+\.t\.sol$/));
  const found = literalAfter(sol, 'instance.name(), ', 'sol');
  assert.ok(found.literal, `plain name missing from the generated test (${found.why})`);
  assert.equal(found.literal.value, 'My Token');
});

test('contract source: an ASCII name with a quote and a backslash decodes exactly', () => {
  const name = 'A "B" \\ C';
  const out = erc20.print({ name, symbol: 'S' });
  assert.equal(constructorLiteral(out, 'ERC20'), name);
});

test('contract source: non-ASCII, emoji and NUL in a name decode exactly', () => {
  for (const name of ['Tokeć', 'Token😀', 'A\x00B']) {
    const out = erc20.print({ name, symbol: 'S' });
    assert.equal(constructorLiteral(out, 'ERC20'), name, `name did not round-trip: ${JSON.stringify(name)}`);
  }
});

test('contract source and Foundry test: an ERC1155 uri keeps its {id} placeholder', async () => {
  const uri = 'https://myuri/{id}';
  const opts = { kind: 'ERC1155', name: 'My Token', uri };
  const out = erc1155.print({ name: opts.name, uri });
  const contractLiteral = literalAfter(out, 'ERC1155(', 'sol').literal;
  assert.ok(contractLiteral, 'the generated contract has no readable uri literal');
  assert.equal(contractLiteral.value, uri);
  const zip = await zipFoundry(buildERC1155(opts), opts);
  const sol = await zipText(zip, zipKeyByRegex(zip, /^test\/.+\.t\.sol$/));
  const found = literalAfter(sol, 'instance.uri(0), ', 'sol');
  assert.ok(found.literal, `plain uri missing from the generated test (${found.why})`);
  assert.equal(found.literal.value, uri);
});

test('ordinary header values are preserved unchanged', async () => {
  for (const license of ['MIT', 'Apache-2.0']) {
    const out = erc20.print({ name: 'My Token', symbol: 'MTK', info: { license } });
    assert.ok(
      out.includes(`// SPDX-License-Identifier: ${license}\n`),
      `plain license not preserved in contract source: ${license}`,
    );
    const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK', info: { license } };
    const zip = await zipFoundry(buildERC20(opts), opts);
    for (const key of [zipKeyByRegex(zip, /^test\/.+\.t\.sol$/), zipKeyByRegex(zip, /^script\/.+\.s\.sol$/), 'src/MyToken.sol']) {
      const text = await zipText(zip, key);
      assert.ok(text.includes(`// SPDX-License-Identifier: ${license}\n`), `license not preserved in ${key}`);
    }
  }
});

test('contract source: a plain ASCII base URI with quotes and a backslash decodes exactly', () => {
  const baseUri = 'https://x/"a"/b\\c';
  const out = erc721.print({ name: 'My NFT', symbol: 'MNFT', baseUri });
  const found = literalAfterBoth(out, '_baseURI()', 'return ', 'sol');
  assert.ok(found.literal, `plain base URI missing (${found.why})`);
  assert.equal(found.literal.value, baseUri);
});

test('Polkadot project: a plain ERC20 name is preserved in the generated test', async () => {
  const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK' };
  const zip = await zipHardhatPolkadot(buildERC20(opts), opts);
  const content = await zipText(zip, 'test/test.ts');
  const found = literalAfter(content, '.to.equal(', 'js');
  assert.ok(found.literal, `plain name missing from the Polkadot test (${found.why})`);
  assert.equal(found.literal.value, 'My Token');
  const config = await zipText(zip, 'hardhat.config.ts');
  assert.ok(config.includes('polkavm'), 'the Polkadot environment configuration changed');
});

test('Foundry project: the deploy script still reports a plain name', async () => {
  const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK' };
  const zip = await zipFoundry(buildERC20(opts), opts);
  const sol = await zipText(zip, zipKeyByRegex(zip, /^script\/.+\.s\.sol$/));
  const found = literalAfterBoth(sol, 'vm.startBroadcast();', 'console.log(', 'sol');
  assert.ok(found.literal, `deploy script message missing (${found.why})`);
  assert.equal(found.literal.value, 'Deploying My Token');
});

test('contract source: an address-less generation still reports the same ordinary name', () => {
  // A second, independent ordinary value checks the plain path was not replaced by escaping.
  const out = erc20.print({ name: 'Standard Token', symbol: 'STD' });
  assert.equal(constructorLiteral(out, 'ERC20'), 'Standard Token');
});
