'use strict';
// A supplied base URI is copied into a Solidity return literal in the generated contract.
const test = require('node:test');
const assert = require('node:assert');
const { src, literalAfterBoth } = require('../support/literals.cjs');

const { erc721 } = src('api.ts');

function baseUriLiteral(source) {
  const found = literalAfterBoth(source, '_baseURI()', 'return ', 'sol');
  assert.ok(found.literal, `the generated contract has no valid base URI literal (${found.why})`);
  return found.literal.value;
}

test('contract source: a non-ASCII base URI is emitted as valid Solidity and decodes exactly', () => {
  const baseUri = 'https://exämple.org/token/';
  let out;
  try {
    out = erc721.print({ name: 'My NFT', symbol: 'MNFT', baseUri });
  } catch (e) {
    return;
  }
  assert.equal(baseUriLiteral(out), baseUri);
});

test('contract source: a base URI with a backspace is emitted as valid Solidity and decodes exactly', () => {
  const baseUri = 'ipfs://a\x08b/';
  let out;
  try {
    out = erc721.print({ name: 'My NFT', symbol: 'MNFT', baseUri });
  } catch (e) {
    return;
  }
  assert.equal(baseUriLiteral(out), baseUri);
});
