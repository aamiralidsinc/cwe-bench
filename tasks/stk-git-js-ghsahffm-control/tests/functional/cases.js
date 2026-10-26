'use strict';

/*
 * Functional cases: ordinary use of the library before the fix must keep working. Setup,
 * expected values and clean-up are plain Node/child-process code in the case tables.
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
  return fs.mkdtempSync(path.join(os.tmpdir(), `sg-f-${name}-`));
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
      classname: 'legitimate-configuration',
      name: 'clone writes a data-carrying configuration entry from options',
      run: async () => {
        const root = tmpRoot('header');
        try {
          const origin = makeRepo(path.join(root, 'origin'));
          const base = path.join(root, 'base');
          fs.mkdirSync(base);
          const target = path.join(root, 'target');

          await simpleGit(base).clone(origin, target, {
            '--config': 'http.extraheader=AUTHORIZATION bearer abcdef',
          });

          const header = git(['config', '--get', 'http.extraheader'], target).stdout.trim();
          expect(header === 'AUTHORIZATION bearer abcdef', `the entry was not written: ${header}`);
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'legitimate-configuration',
      name: 'the configuration API writes and reads an ordinary identity setting',
      run: async () => {
        const root = tmpRoot('identity');
        try {
          const repo = makeRepo(path.join(root, 'repo'));
          await simpleGit(repo).addConfig('user.name', 'Task Fixture');

          const stored = git(['config', '--get', 'user.name'], repo).stdout.trim();
          expect(stored === 'Task Fixture', `the identity was not written: ${stored}`);
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'legitimate-configuration',
      name: 'an instance-wide ordinary setting is applied and readable',
      run: async () => {
        const root = tmpRoot('instance');
        try {
          const repo = makeRepo(path.join(root, 'repo'));
          const result = await simpleGit({ baseDir: repo, config: ['user.name=Legit User'] }).getConfig('user.name');
          expect(result && result.value === 'Legit User', `the setting was not applied: ${result && result.value}`);
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'ordinary-operations',
      name: 'a remote listing works against an ordinary remote',
      run: async () => {
        const root = tmpRoot('list');
        try {
          const repo = makeRepo(path.join(root, 'repo'));
          const origin = makeRepo(path.join(root, 'origin'));
          const output = await simpleGit(repo).listRemote([origin, 'HEAD']);
          expect(String(output).trim().length > 0, 'the remote listing returned nothing');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'ordinary-operations',
      name: 'a pull fast-forwards a clean checkout',
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

          const result = await simpleGit(checkout).pull('origin', 'main');
          expect(result && result.summary, 'the pull returned no summary');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'ordinary-operations',
      name: 'a push updates an ordinary remote',
      run: async () => {
        const root = tmpRoot('push');
        try {
          const bare = path.join(root, 'origin.git');
          git(['init', '-q', '--bare', bare], root);
          const repo = makeRepo(path.join(root, 'repo'));
          git(['remote', 'add', 'origin', bare], repo);

          await simpleGit(repo).push('origin', 'main');
          const branches = git(['branch', '--list'], bare).stdout;
          expect(branches.includes('main'), 'the push did not update the remote');
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'opt-in',
      name: 'the existing protocol opt-in still permits a configuration override',
      run: async () => {
        const root = tmpRoot('optin-config');
        try {
          const origin = makeRepo(path.join(root, 'origin'));
          const base = path.join(root, 'base');
          fs.mkdirSync(base);
          const target = path.join(root, 'target');

          await simpleGit({ baseDir: base, unsafe: { allowUnsafeProtocolOverride: true } }).clone(
            origin,
            target,
            { '--config': 'protocol.ext.allow=always' }
          );

          const stored = git(['config', '--get', 'protocol.ext.allow'], target).stdout.trim();
          expect(stored === 'always', `the opted-in override was not applied: ${stored}`);
        } finally {
          cleanup(root);
        }
      },
    },
    {
      classname: 'opt-in',
      name: 'the existing protocol opt-in still permits an inline configuration switch',
      run: async () => {
        const root = tmpRoot('optin-switch');
        try {
          const repo = path.join(root, 'repo');
          fs.mkdirSync(repo);

          await simpleGit({ baseDir: repo, unsafe: { allowUnsafeProtocolOverride: true } }).raw(
            '-c',
            'protocol.ext.allow=always',
            'init'
          );

          expect(fs.existsSync(path.join(repo, '.git')), 'the opted-in operation did not run');
        } finally {
          cleanup(root);
        }
      },
    },
  ];
};
