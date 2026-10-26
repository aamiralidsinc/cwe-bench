'use strict';

/*
 * Security cases. Every case drives the library's public entry point with a harmless program
 * (a shell script that touches a marker and exits) whose name comes from the caller's value.
 * A case passes only when the library refuses with a client error AND the program never ran.
 * On the pinned library every case leaves the marker, so the suite fails there.
 */

module.exports = function (ctx) {
  const { fs, path, sh, markerFor, unique, simpleGit } = ctx;
  const cases = [];

  function initRepo(dir) {
    fs.mkdirSync(dir, { recursive: true });
    sh('git', ['init', '-q', '-b', 'main', '.'], dir);
    sh('git', ['config', 'user.email', 'test@example.invalid'], dir);
    sh('git', ['config', 'user.name', 'Test'], dir);
    fs.writeFileSync(path.join(dir, 'file.txt'), 'content\n');
    sh('git', ['add', 'file.txt'], dir);
    sh('git', ['commit', '-qm', 'initial'], dir);
    return dir;
  }

  function bareRepo(dir) {
    fs.mkdirSync(dir, { recursive: true });
    sh('git', ['init', '-q', '--bare', '.'], dir);
    return dir;
  }

  const root = ctx.root;
  const base = path.join(root, 'work');
  fs.mkdirSync(base, { recursive: true });
  const source = initRepo(path.join(root, 'source'));
  const bare = bareRepo(path.join(root, 'bare.git'));
  const sourceUrl = 'file://' + source;

  const gitAt = (dir, options) => simpleGit(dir, Object.assign({ maxConcurrentProcesses: 1 }, options || {}));

  function blocked(id, name, attack) {
    cases.push({
      classname: 'security/' + id,
      name,
      async run() {
        const marker = markerFor(id);
        marker.reset();
        let rejected = false;
        try {
          await attack(marker.script);
        } catch (_) {
          rejected = true;
        }
        if (marker.exists()) {
          throw new Error('a program named by the caller was started on this machine');
        }
        if (!rejected) {
          throw new Error('the unsafe request was accepted instead of being refused');
        }
      },
    });
  }

  function storedAddress(id, name, add) {
    cases.push({
      classname: 'security/' + id,
      name,
      async run() {
        const marker = markerFor(id);
        marker.reset();
        const repo = initRepo(unique('stored-' + id));
        sh('git', ['config', 'protocol.ext.allow', 'always'], repo);

        let rejected = false;
        try {
          await add(gitAt(repo), 'ext::' + marker.script);
        } catch (_) {
          rejected = true;
        }
        try {
          await gitAt(repo).fetch('origin', 'main');
        } catch (_) {
          rejected = true;
        }
        if (marker.exists()) {
          throw new Error('an address stored earlier started a program on this machine');
        }
        if (!rejected) {
          throw new Error('the stored address was accepted instead of being refused');
        }
      },
    });
  }

  // The reported route: a pack-program option on a clone (and its mirror alias).
  blocked('T1-clone-options-object', 'clone with a pack-program option object',
    (cmd) => gitAt(base).clone(sourceUrl, unique('T1-opt'), { '--upload-pack': cmd }));
  blocked('T1-clone-arguments', 'clone with a pack-program option in the argument list',
    (cmd) => gitAt(base).clone(sourceUrl, unique('T1-args'), ['--upload-pack', cmd]));
  blocked('T1-mirror-arguments', 'mirror with a pack-program option in the argument list',
    (cmd) => gitAt(base).mirror(sourceUrl, unique('T1-mirror'), ['--upload-pack', cmd]));

  // The same program-selection class on the other operations that carry caller arguments.
  blocked('T2-pull', 'pull with a pack-program option', (cmd) => {
    const repo = unique('T2-pull');
    sh('git', ['clone', '-q', source, repo], root);
    return gitAt(repo).pull('origin', 'main', ['--upload-pack', cmd]);
  });
  blocked('T2-push', 'push with a receive-program option', (cmd) => {
    const repo = initRepo(unique('T2-push'));
    sh('git', ['remote', 'add', 'origin', bare], repo);
    return gitAt(repo).push('origin', 'main', { '--receive-pack': cmd });
  });
  blocked('T2-clone-short-form', 'clone with the short pack-program option',
    (cmd) => gitAt(base).clone(sourceUrl, unique('T2-short'), ['-u', cmd]));
  blocked('T2-raw-command', 'raw clone command with a pack-program option',
    (cmd) => gitAt(base).raw('clone', sourceUrl, unique('T2-raw'), '--upload-pack=' + cmd));

  // The reported protocol-permission route: a permission override beside a helper address.
  blocked('T3-clone-config-switch', 'clone with a protocol permission switch and a helper address',
    (cmd) => gitAt(base).clone('ext::' + cmd, unique('T3-clone'), ['-c', 'protocol.ext.allow=always']));
  blocked('T3-raw-config-switch', 'raw command with a protocol permission switch and a helper address',
    (cmd) => gitAt(base).raw('-c', 'protocol.ext.allow=always', 'clone', 'ext::' + cmd, unique('T3-raw')));

  // The same permission change in its other accepted spellings and sources.
  blocked('T4-config-alias-equals', 'clone with the config alias in one token',
    (cmd) => gitAt(base).clone('ext::' + cmd, unique('T4-eq'), { '--config': 'protocol.ext.allow=always' }));
  blocked('T4-config-alias-two-token', 'clone with the config alias in two tokens',
    (cmd) => gitAt(base).clone('ext::' + cmd, unique('T4-two'), ['--config', 'protocol.ext.allow=always']));
  blocked('T4-instance-config', 'instance configuration that permits the helper transport',
    (cmd) => gitAt(base, { config: ['protocol.ext.allow=always'] }).clone('ext::' + cmd, unique('T4-inst')));
  blocked('T4-general-permission', 'clone with the general protocol permission switch',
    (cmd) => gitAt(base).clone('ext::' + cmd, unique('T4-gen'), ['-c', 'protocol.allow=always']));

  // An address stored earlier, which the command that runs it never carries.
  storedAddress('T5-stored-remote', 'a stored helper remote address', (git, url) => git.addRemote('origin', url));
  storedAddress('T5-raw-stored-remote', 'a stored helper remote address through a raw command',
    (git, url) => git.raw('remote', 'add', 'origin', url));

  return cases;
};
