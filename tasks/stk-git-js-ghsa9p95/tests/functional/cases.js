'use strict';

/*
 * Functional cases: legitimate operations and the values that must keep working next to each
 * hidden route. Every expectation is what the pinned library already does today; the opt-in cases
 * exercise the documented escape hatch that a fix must honour.
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

  function ok(id, name, run) {
    cases.push({ classname: 'functional/' + id, name, run });
  }

  function assert(condition, message) {
    if (!condition) {
      throw new Error(message);
    }
  }

  ok('F-clone-basic', 'an ordinary clone succeeds', async () => {
    const dest = unique('F-clone-basic');
    await gitAt(base).clone(sourceUrl, dest);
    assert(fs.existsSync(path.join(dest, 'file.txt')), 'the cloned file is missing');
  });

  ok('F-clone-options', 'a clone with an ordinary option object succeeds', async () => {
    const dest = unique('F-clone-options');
    await gitAt(base).clone(sourceUrl, dest, { '--branch': 'main' });
    assert(fs.existsSync(path.join(dest, 'file.txt')), 'the cloned file is missing');
  });

  ok('F-clone-legit-config', 'a clone with ordinary configuration succeeds', async () => {
    const dest = unique('F-clone-config');
    await gitAt(base).clone(sourceUrl, dest, { '--config': 'http.extraheader=Authorization: Bearer test' });
    assert(fs.existsSync(path.join(dest, 'file.txt')), 'the cloned file is missing');
  });

  ok('F-fetch-basic', 'an ordinary fetch succeeds and keeps the remote', async () => {
    const repo = initRepo(unique('F-fetch'));
    sh('git', ['remote', 'add', 'origin', source], repo);
    const git = gitAt(repo);
    await git.fetch('origin', 'main');
    const remotes = await git.getRemotes();
    assert(remotes.some((remote) => remote.name === 'origin'), 'origin is missing from the remotes');
  });

  ok('F-pull-basic', 'an ordinary pull succeeds', async () => {
    const repo = unique('F-pull');
    sh('git', ['clone', '-q', source, repo], root);
    await gitAt(repo).pull('origin', 'main');
  });

  ok('F-push-basic', 'an ordinary push succeeds', async () => {
    const repo = initRepo(unique('F-push'));
    sh('git', ['remote', 'add', 'origin', bare], repo);
    await gitAt(repo).push('origin', 'main');
    sh('git', ['rev-parse', '--verify', 'refs/heads/main'], bare);
  });

  ok('F-remote-basic', 'adding and reading an ordinary remote succeeds', async () => {
    const repo = initRepo(unique('F-remote'));
    const git = gitAt(repo);
    await git.addRemote('origin', source);
    const remotes = await git.getRemotes(true);
    assert(remotes.some((remote) => remote.name === 'origin'), 'origin is missing from the remotes');
    await git.fetch('origin', 'main');
  });

  ok('F-commit-ext-text', 'a commit message containing helper-like text succeeds', async () => {
    const repo = initRepo(unique('F-commit'));
    const git = gitAt(repo);
    fs.writeFileSync(path.join(repo, 'notes.txt'), 'notes\n');
    await git.add('notes.txt');
    await git.commit('document ext:: handling and fd:: handling');
    const message = await git.raw('log', '-1', '--format=%s');
    assert(String(message).includes('document ext:: handling'), 'the commit message was not stored');
  });

  ok('F-grep-ext-text', 'a search term containing helper-like text succeeds', async () => {
    const repo = initRepo(unique('F-grep'));
    const result = await gitAt(repo).grep('ext::');
    assert(result && typeof result === 'object', 'grep did not return a result');
  });

  ok('F-fetch-existing-guard', 'the existing fetch argument refusal keeps its message', async () => {
    const repo = initRepo(unique('F-fetch-guard'));
    sh('git', ['remote', 'add', 'origin', source], repo);
    let error;
    try {
      await gitAt(repo).fetch('origin', '--upload-pack=test-value');
    } catch (e) {
      error = e;
    }
    assert(error, 'the unsafe fetch argument was accepted');
    assert(/potential exploit argument blocked/.test(String(error.message)), 'the refusal message changed');
  });

  ok('F-instance-config', 'ordinary instance configuration still reaches git', async () => {
    const repo = initRepo(unique('F-config'));
    const git = gitAt(repo, { config: ['user.name=Config User', 'user.email=config@example.invalid'] });
    fs.writeFileSync(path.join(repo, 'config.txt'), 'config\n');
    await git.add('config.txt');
    await git.commit('configured commit');
    const author = await git.raw('log', '-1', '--format=%an');
    assert(String(author).trim() === 'Config User', `the configured author is ${JSON.stringify(String(author).trim())}`);
  });

  ok('F-raw-basic', 'an ordinary raw command succeeds', async () => {
    const repo = initRepo(unique('F-raw'));
    const out = await gitAt(repo).raw('rev-parse', '--show-toplevel');
    assert(String(out).includes(path.basename(repo)) || String(out).trim().length > 0, 'raw returned nothing');
  });

  ok('F-optin-protocol', 'the opt-in keeps a deliberate helper transport working', async () => {
    const marker = markerFor('F-optin-protocol');
    marker.reset();
    const dest = unique('F-optin-protocol');
    try {
      await gitAt(base, { unsafe: { allowUnsafeProtocolOverride: true } })
        .clone('ext::' + marker.script, dest, ['-c', 'protocol.ext.allow=always']);
    } catch (_) {
      /* the helper exits non-zero; the marker is the evidence it ran */
    }
    assert(marker.exists(), 'the opted-in helper transport did not run');
  });

  ok('F-optin-stored', 'the opt-in keeps a deliberate stored helper remote working', async () => {
    const marker = markerFor('F-optin-stored');
    marker.reset();
    const repo = initRepo(unique('F-optin-stored'));
    sh('git', ['config', 'protocol.ext.allow', 'always'], repo);
    const git = gitAt(repo, { unsafe: { allowUnsafeProtocolOverride: true } });
    await git.addRemote('origin', 'ext::' + marker.script);
    try {
      await git.fetch('origin', 'main');
    } catch (_) {
      /* the helper exits non-zero; the marker is the evidence it ran */
    }
    assert(marker.exists(), 'the opted-in stored helper remote did not run');
  });

  return cases;
};
