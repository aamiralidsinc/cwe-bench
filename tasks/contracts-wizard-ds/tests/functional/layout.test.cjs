'use strict';
// The wizard still produces the same set of files for an ordinary contract.
const test = require('node:test');
const assert = require('node:assert');
const { src } = require('../support/literals.cjs');

const { zipHardhat } = src('zip-hardhat.ts');
const { zipFoundry } = src('zip-foundry.ts');
const { zipHardhatPolkadot } = src('zip-hardhat-polkadot.ts');
const { buildERC20 } = src('erc20.ts');

test('Hardhat project file set is unchanged', async () => {
  const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK' };
  const zip = await zipHardhat(buildERC20(opts), opts);
  assert.deepEqual(Object.keys(zip.files).sort(), [
    '.gitignore',
    'README.md',
    'contracts/',
    'contracts/MyToken.sol',
    'hardhat.config.ts',
    'ignition/',
    'ignition/modules/',
    'ignition/modules/MyToken.ts',
    'package-lock.json',
    'package.json',
    'test/',
    'test/test.ts',
    'tsconfig.json',
  ]);
});

test('Foundry project file set is unchanged', async () => {
  const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK' };
  const zip = await zipFoundry(buildERC20(opts), opts);
  assert.deepEqual(Object.keys(zip.files).sort(), [
    'README.md',
    'script/',
    'script/MyToken.s.sol',
    'setup.sh',
    'src/',
    'src/MyToken.sol',
    'test/',
    'test/MyToken.t.sol',
  ]);
});

test('Polkadot project file set is unchanged', async () => {
  const opts = { kind: 'ERC20', name: 'My Token', symbol: 'MTK' };
  const zip = await zipHardhatPolkadot(buildERC20(opts), opts);
  assert.deepEqual(Object.keys(zip.files).sort(), [
    '.gitignore',
    'README.md',
    'contracts/',
    'contracts/MyToken.sol',
    'hardhat.config.ts',
    'ignition/',
    'ignition/modules/',
    'ignition/modules/MyToken.ts',
    'package-lock.json',
    'package.json',
    'test/',
    'test/test.ts',
    'tsconfig.json',
  ]);
});
