'use strict';

/*
 * Security cases. Each case drives a public entry point of the submitted library with a value a
 * caller could supply, and asserts the operation is refused and leaves nothing behind. Git
 * setup and side-effect observation use the git binary directly, so a hardened product helper
 * cannot change an outcome.
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
      classname: 'config-api',
      name: 'writing the protocol setting through the configuration API is refused',
      run: async () => {
        const root = tmpRoot('config-api');
        try {
          const repo = makeRepo(path.join(root, 'repo'));

          const result = await refused(simpleGit(repo).addConfig('protocol.ext.allow', 'always'));
          const applied = git(['config', '--get', 'protocol.ext.allow'], repo).stdout.trim();

          expect(result.refused, 'the configuration write was accepted');
          expect(applied !== 'always', 'the protocol restriction was relaxed');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'config-api',
      name: 'writing the protocol setting through a raw configuration command is refused',
      run: async () => {
        const root = tmpRoot('config-raw');
        try {
          const repo = makeRepo(path.join(root, 'repo'));

          const result = await refused(
            simpleGit(repo).raw(['config', '--local', 'protocol.ext.allow', 'always'])
          );
          const applied = git(['config', '--get', 'protocol.ext.allow'], repo).stdout.trim();

          expect(result.refused, 'the configuration write was accepted');
          expect(applied !== 'always', 'the protocol restriction was relaxed');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'config-source',
      name: 'a configuration override carried in a referenced configuration source is refused',
      run: async () => {
        const root = tmpRoot('config-source');
        try {
          const repo = makeRepo(path.join(root, 'repo'));
          const included = path.join(root, 'included.cfg');
          fs.writeFileSync(included, '[protocol "ext"]\n\tallow = always\n');

          let applied = '';
          let refusedOperation = false;

          try {
            const value = await simpleGit({
              baseDir: repo,
              config: [`include.path=${included}`],
            }).getConfig('protocol.ext.allow');
            applied = value && value.value ? value.value : '';
          } catch (e) {
            refusedOperation = true;
          }

          expect(refusedOperation || applied !== 'always', 'the protocol restriction was relaxed');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'remote-operation',
      name: 'a caller-supplied pack command on a remote listing is refused',
      run: async () => {
        const root = tmpRoot('list-remote');
        try {
          const repo = makeRepo(path.join(root, 'repo'));
          const origin = makeRepo(path.join(root, 'origin'));
          const marker = path.join(root, 'marker');
          const command = path.join(root, 'upload-pack.sh');
          fs.writeFileSync(command, `#!/bin/sh\ntouch '${marker}'\nexec git-upload-pack "$@"\n`, { mode: 0o755 });

          const result = await refused(
            simpleGit(repo).listRemote([`--upload-pack=${command}`, origin, 'HEAD'])
          );

          expect(result.refused, 'the pack command was accepted');
          expect(!fs.existsSync(marker), 'the caller-supplied command ran');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'remote-operation',
      name: 'a caller-supplied pack command on a pull is refused',
      run: async () => {
        const root = tmpRoot('pull');
        try {
          const source = makeRepo(path.join(root, 'source'));
          const checkout = path.join(root, 'checkout');
          git(['clone', '-q', source, checkout]);
          git(['config', 'user.email', 'task@example.invalid'], checkout);
          git(['config', 'user.name', 'Task Fixture'], checkout);
          fs.writeFileSync(path.join(source, 'next.txt'), 'two\n');
          git(['add', '.'], source);
          git(['commit', '-qm', 'two'], source);

          const marker = path.join(root, 'marker');
          const command = path.join(root, 'upload-pack.sh');
          fs.writeFileSync(command, `#!/bin/sh\ntouch '${marker}'\nexec git-upload-pack "$@"\n`, { mode: 0o755 });

          const result = await refused(
            simpleGit(checkout).pull('origin', 'main', [`--upload-pack=${command}`])
          );

          expect(result.refused, 'the pack command was accepted');
          expect(!fs.existsSync(marker), 'the caller-supplied command ran');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'remote-operation',
      name: 'a caller-supplied pack command on a push is refused',
      run: async () => {
        const root = tmpRoot('push');
        try {
          const bare = path.join(root, 'origin.git');
          git(['init', '-q', '--bare', bare], root);
          const repo = makeRepo(path.join(root, 'repo'));
          git(['remote', 'add', 'origin', bare], repo);

          const marker = path.join(root, 'marker');
          const command = path.join(root, 'receive-pack.sh');
          fs.writeFileSync(command, `#!/bin/sh\ntouch '${marker}'\nexec git-receive-pack "$@"\n`, { mode: 0o755 });

          const result = await refused(
            simpleGit(repo).push('origin', 'main', [`--receive-pack=${command}`])
          );

          expect(result.refused, 'the pack command was accepted');
          expect(!fs.existsSync(marker), 'the caller-supplied command ran');
        } finally {
          cleanup(root);
        }
      },
    },
  ];
};
