'use strict';

/*
 * Control task security cases: only the route the report leads to (a pack-program option on a
 * clone, and its mirror alias). Every case drives the public entry point with a harmless program
 * that touches a marker and exits; it passes only when the library refuses and the program never
 * ran. On the pinned library every case leaves the marker.
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

  const root = ctx.root;
  const base = path.join(root, 'work');
  fs.mkdirSync(base, { recursive: true });
  const source = initRepo(path.join(root, 'source'));
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

  blocked('T1-clone-options-object', 'clone with a pack-program option object',
    (cmd) => gitAt(base).clone(sourceUrl, unique('T1-opt'), { '--upload-pack': cmd }));
  blocked('T1-clone-arguments', 'clone with a pack-program option in the argument list',
    (cmd) => gitAt(base).clone(sourceUrl, unique('T1-args'), ['--upload-pack', cmd]));
  blocked('T1-mirror-arguments', 'mirror with a pack-program option in the argument list',
    (cmd) => gitAt(base).mirror(sourceUrl, unique('T1-mirror'), ['--upload-pack', cmd]));
  blocked('T1-mirror-options-object', 'mirror with a pack-program option object',
    (cmd) => gitAt(base).mirror(sourceUrl, unique('T1-mirror-opt'), { '--upload-pack': cmd }));

  return cases;
};
