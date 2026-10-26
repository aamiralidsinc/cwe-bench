'use strict';
// Generated source carries comment headers too. A supplied value must not be able to end the
// comment it is placed in and start new source lines.
const test = require('node:test');
const assert = require('node:assert');
const { src, assertMarkerContained, zipText } = require('../support/literals.cjs');

const { erc20 } = src('api.ts');
const { zipFoundry } = src('zip-foundry.ts');
const { buildERC20 } = src('erc20.ts');

const MARK = 'MALICIOUS_7c1a.back';
const LICENSE = 'MIT\n' + MARK + '();';

test('contract source: a line break in a supplied header value cannot start new code', () => {
  let out;
  try {
    out = erc20.print({ name: 'My Token', symbol: 'MTK', info: { license: LICENSE } });
  } catch (e) {
    return; // refusing the value is an acceptable outcome
  }
  assertMarkerContained(assert, out, MARK, 'sol', 'generated contract');
});

test('Foundry project: a line break in a supplied header value cannot start new code', async () => {
  const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK', info: { license: LICENSE } };
  let zip;
  try {
    zip = await zipFoundry(buildERC20(opts), opts);
  } catch (e) {
    return;
  }
  for (const key of ['test/MyToken.t.sol', 'script/MyToken.s.sol']) {
    const sol = await zipText(zip, key);
    assertMarkerContained(assert, sol, MARK, 'sol', `Foundry ${key}`);
  }
});
