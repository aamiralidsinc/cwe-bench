// Emit the three generated client applications used by the hidden suites.
// Runs inside the verifier as the unprivileged agent after the project has been rebuilt, using the
// project's own CLI and a JDL description from the read-only verifier tree.
//
// The CLI derives its generator namespace from the package folder name, so the built package is
// staged under a folder called `generator-jhipster` (the workspace itself is /workspace).
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, rmSync, symlinkSync } from 'node:fs';
import { join } from 'node:path';

const dest = process.env.JHI_FIXTURES ?? '/home/agent/fixtures';
const workspace = process.env.JHI_WORKSPACE ?? '/workspace';
const support = process.env.JHI_SUPPORT ?? '/opt/jh-htests/support';

const pkgRoot = join(dest, '.pkg', 'generator-jhipster');
rmSync(dest, { recursive: true, force: true });
mkdirSync(pkgRoot, { recursive: true });
cpSync(join(workspace, 'dist'), join(pkgRoot, 'dist'), { recursive: true });
cpSync(join(workspace, 'package.json'), join(pkgRoot, 'package.json'));
symlinkSync(join(workspace, 'node_modules'), join(pkgRoot, 'node_modules'), 'dir');

for (const client of ['angular', 'react', 'vue']) {
  const dir = join(dest, client);
  mkdirSync(dir, { recursive: true });
  execFileSync(
    process.execPath,
    [
      join(pkgRoot, 'dist', 'cli', 'jhipster.cjs'),
      'jdl',
      join(support, `app.${client}.jdl`),
      '--skip-install',
      '--skip-git',
      '--force',
      '--no-insight',
    ],
    {
      cwd: dir,
      stdio: 'inherit',
      timeout: 600_000,
      env: { ...process.env, NO_COLOR: '1', FORCE_COLOR: '0' },
    },
  );
}
