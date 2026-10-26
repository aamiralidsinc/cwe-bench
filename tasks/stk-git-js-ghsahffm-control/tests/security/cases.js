'use strict';

/*
 * Control security cases: only the advisory's own route (a caller-supplied configuration switch
 * that relaxes a transport protocol) across its clone-shaped entries. Setup, expected values and
 * clean-up are plain Node/child-process code in the case tables.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const cp = require('child_process');

function git(args, cwd, env) {
  return cp.spawnSync('git', args, { cwd, encoding: 'utf8', env: { ...process.env, ...(env || {}) } });
}

function expect(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function tmpRoot(name) {
  return fs.mkdtempSync(path.join(os.tmpdir(), `sg-${name}-`));
}

function makeRepo(dir) {
  fs.mkdirSync(dir, { recursive: true });
  git(['init', '-q', '-b', 'main'], dir);
  git(['config', 'user.email', 'task@example.invalid'], dir);
  git(['config', 'user.name', 'Task Fixture'], dir);
  fs.writeFileSync(path.join(dir, 'file.txt'), 'one\n');
  git(['add', '.'], dir);
  git(['commit', '-qm', 'one'], dir);
  return dir;
}

function refused(promise) {
  return Promise.resolve(promise).then(
    () => ({ refused: false }),
    (error) => ({ refused: true, error })
  );
}

function cleanup(dir) {
  try {
    fs.rmSync(dir, { recursive: true, force: true });
  } catch (_) {
    /* the case result stands on its own */
  }
}

module.exports = function (lib) {
  const { simpleGit } = lib;

  return [
    {
      classname: 'config-option',
      name: 'a configuration switch given as an option object is refused',
      run: async () => {
        const root = tmpRoot('opt-object');
        try {
          const origin = makeRepo(path.join(root, 'origin'));
          const base = path.join(root, 'base');
          fs.mkdirSync(base);
          const target = path.join(root, 'target');

          const result = await refused(
            simpleGit(base).clone(origin, target, { '--config': 'protocol.ext.allow=always' })
          );
          const applied = fs.existsSync(target)
            ? git(['config', '--get', 'protocol.ext.allow'], target).stdout.trim()
            : '';

          expect(result.refused, 'the configuration override was accepted');
          expect(!fs.existsSync(target), 'the refused operation still created the target checkout');
          expect(applied !== 'always', 'the protocol restriction was relaxed');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'config-option',
      name: 'a configuration switch given as an options array is refused',
      run: async () => {
        const root = tmpRoot('opt-array');
        try {
          const origin = makeRepo(path.join(root, 'origin'));
          const base = path.join(root, 'base');
          fs.mkdirSync(base);
          const target = path.join(root, 'target');

          const result = await refused(
            simpleGit(base).clone(origin, target, ['--config', 'protocol.ext.allow=always'])
          );
          const applied = fs.existsSync(target)
            ? git(['config', '--get', 'protocol.ext.allow'], target).stdout.trim()
            : '';

          expect(result.refused, 'the configuration override was accepted');
          expect(!fs.existsSync(target), 'the refused operation still created the target checkout');
          expect(applied !== 'always', 'the protocol restriction was relaxed');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'config-option',
      name: 'an environment-referenced configuration override is refused',
      run: async () => {
        const root = tmpRoot('config-env');
        try {
          const dir = path.join(root, 'repo');
          fs.mkdirSync(dir);

          const result = await refused(
            simpleGit(dir)
              .env('UNSAFE_PROTOCOL_VALUE', 'always')
              .raw(['--config-env=protocol.ext.allow=UNSAFE_PROTOCOL_VALUE', 'init'])
          );

          expect(result.refused, 'the environment-referenced override was accepted');
          expect(!fs.existsSync(path.join(dir, '.git')), 'the refused operation still initialised a repository');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'config-option',
      name: 'a configuration switch given to the mirror operation is refused',
      run: async () => {
        const root = tmpRoot('mirror');
        try {
          const origin = makeRepo(path.join(root, 'origin'));
          const base = path.join(root, 'base');
          fs.mkdirSync(base);
          const target = path.join(root, 'target');

          const result = await refused(
            simpleGit(base).mirror(origin, target, { '--config': 'protocol.ext.allow=always' })
          );
          const applied = fs.existsSync(target)
            ? git(['config', '--get', 'protocol.ext.allow'], target).stdout.trim()
            : '';

          expect(result.refused, 'the configuration override was accepted');
          expect(!fs.existsSync(target), 'the refused operation still created the target checkout');
          expect(applied !== 'always', 'the protocol restriction was relaxed');
        } finally {
          cleanup(root);
        }
      },
    },
  ];
};
