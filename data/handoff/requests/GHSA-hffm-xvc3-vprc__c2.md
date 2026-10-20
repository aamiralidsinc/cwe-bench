<!-- label=GHSA-hffm-xvc3-vprc call=2 hash=548cae8e1c -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-hffm-xvc3-vprc
- CVE: CVE-2026-6951
- CWE: CWE-94
- Ecosystem / Package: npm / simple-git
- Repository: https://github.com/steveukx/git-js
- Official Summary: simple-git is vulnerable to Remote Code Execution

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/.changeset/config.json b/.changeset/config.json
index 8ef84729233dfea4d1bb2efbc168d81d0a876eff..e89b0ddbfb193343417068c04928d3108001318a 100644
--- a/.changeset/config.json
+++ b/.changeset/config.json
@@ -1,10 +1,10 @@
 {
-  "$schema": "https://unpkg.com/@changesets/config@1.6.4/schema.json",
+  "$schema": "https://unpkg.com/@changesets/config@3.1.3/schema.json",
   "changelog": "@changesets/cli/changelog",
   "commit": false,
   "linked": [],
   "access": "public",
-  "baseBranch": "main",
+  "baseBranch": "origin/main",
   "updateInternalDependencies": "patch",
   "ignore": [
     "@simple-git/test-utils"
diff --git a/.changeset/deep-ducks-care.md b/.changeset/deep-ducks-care.md
new file mode 100644
index 0000000000000000000000000000000000000000..69e2a4e7a274065ec666eb52be60a852646c448e
--- /dev/null
+++ b/.changeset/deep-ducks-care.md
@@ -0,0 +1,11 @@
+---
+"@simple-git/argv-parser": minor
+simple-git: minor
+---
+
+Extend known exploitable configuration keys and per-task environment variables.
+
+Note - `ParsedVulnerabilities` from `argv-parser` is removed in favour of a readonly array of `Vulnerability` to match usage in `simple-git`, rolled into the new `vulnerabilityCheck` for simpler access to the identified issues. 
+
+Thanks to @zebbern for identifying the need to block `core.fsmonitor`.
+Thanks to @kodareef5 for identifying the need to block `GIT_CONFIG_COUNT` environment variables and  `--template` / `merge` related config. 
diff --git a/docs/PLUGIN-UNSAFE-ACTIONS.md b/docs/PLUGIN-UNSAFE-ACTIONS.md
index 0121ba27d17f2a0f2edb9fb22acdd7878d1758f2..7f0da3951e3e1ed68134de64533fc17401812dd1 100644
--- a/docs/PLUGIN-UNSAFE-ACTIONS.md
+++ b/docs/PLUGIN-UNSAFE-ACTIONS.md
@@ -1,37 +1,44 @@
 ## Unsafe Actions
 
-As `simple-git` passes generated arguments through to a child process of the calling node.js process, it is recommended
-that any parameter sourced from user input is validated before being passed to the `simple-git` API.
+As `simple-git` passes generated arguments directly to a `git` child process, **all parameters sourced from
+user input must be validated and sanitised** before being passed to any `simple-git` API, regardless of which
+command is being called. There is no command that is inherently safe to call with unsanitised user data.
 
-In some cases where there is an elevated potential for harm `simple-git` will throw an exception unless you have
-explicitly opted in to the potentially unsafe action.
+In cases where there is a heightened potential for harm — where a single unsanitised argument could allow
+arbitrary command execution or the disclosure of sensitive credentials — `simple-git` will additionally throw
+a `GitPluginError` unless you have explicitly opted in to the potentially unsafe behaviour.
 
-### Enabling custom upload and receive packs
+These blocks are a safety net, not a substitute for input validation. They cover known high-risk patterns,
+but they do not protect against every possible injection or misuse of the `git` command line.
 
-Instead of using the default `git-receive-pack` and `git-upload-pack` binaries to parse incoming and outgoing
-data, `git` can be configured to use _any_ arbitrary binary or evaluable script.
+### Custom upload and receive packs
 
-To avoid accidentally triggering the evaluation of a malicious script when merging user provided parameters
-into command executed by `simple-git`, custom pack options (usually with the `--receive-pack` and `--upload-pack`)
-are blocked without explicitly opting into their use  
+Instead of using the default `git-receive-pack` and `git-upload-pack` binaries to parse incoming and outgoing
+data, `git` can be configured to use _any_ arbitrary binary or evaluable script. This applies whether the
+binary is set via the `--upload-pack` / `--receive-pack` flags or through per-remote configuration
+(`remote.<name>.uploadpack` / `remote.<name>.receivepack`).
 
 ```typescript
 import { simpleGit } from 'simple-git';
 
-// throws
+// throws — via flag
 await simpleGit()
    .raw('push', '--receive-pack=git-receive-pack-custom');
 
-// allows calling clone with a helper transport
+// throws — via per-remote configuration
+await simpleGit()
+   .raw('-c', 'remote.origin.uploadpack=/custom/upload-pack', 'fetch');
+
+// opt in to using custom pack binaries
 await simpleGit({ unsafe: { allowUnsafePack: true } })
    .raw('push', '--receive-pack=git-receive-pack-custom');
 ```
 
 ### Overriding allowed protocols
 
-A standard installation of `git` permits `file`, `http` and `ssh` protocols for a remote. A range of 
+A standard installation of `git` permits `file`, `http` and `ssh` protocols for a remote. A range of
 [git remote helpers](https://git-scm.com/docs/gitremote-helpers) other than these default few can be
-used by referring to te helper name in the remote protocol - for example the git file descriptor transport
+used by referring to the helper name in the remote protocol - for example the git file descriptor transport
 [git-remote-fd](https://git-scm.com/docs/git-remote-fd) would be used in a remote protocol such as:
 
 ```
@@ -57,3 +64,389 @@ await simpleGit({ unsafe: { allowUnsafeProtocolOverride: true } })
 > *Be advised* helper transports can be used to call arbitrary binaries on the host machine.
 > Do not allow them in applications where you are not in control of the input parameters.
 
+### Command aliases
+
+Git allows defining shorthand aliases for any command or external shell script via `alias.*` configuration.
+Passing an unsanitised value as an alias target could cause `git` to execute an arbitrary command.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws
+await simpleGit()
+   .raw('-c', 'alias.ls=!ls -la', 'ls');
+
+// opt in to defining aliases
+await simpleGit({ unsafe: { allowUnsafeAlias: true } })
+   .raw('-c', 'alias.ls=!ls -la', 'ls');
+```
+
+### Credential helpers
+
+Git credential helpers are external binaries or scripts that store and retrieve authentication credentials.
+An attacker-controlled `credential.helper` value could direct `git` to run an arbitrary binary with access
+to any credentials passed through.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws
+await simpleGit()
+   .raw('-c', 'credential.helper=/path/to/malicious-script', 'clone', '--', 'https://example.com/repo');
+
+// opt in to using a custom credential helper
+await simpleGit({ unsafe: { allowUnsafeCredentialHelper: true } })
+   .raw('-c', 'credential.helper=/path/to/custom-helper', 'clone', '--', 'https://example.com/repo');
+```
+
+### Ask-pass programs
+
+The `core.askPass` configuration and the `GIT_ASKPASS` / `SSH_ASKPASS` environment variables define an
+external binary that `git` will call to prompt for passwords. Controlling this value allows an attacker to
+intercept credentials by substituting their own binary.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — via config flag
+await simpleGit()
+   .raw('-c', 'core.askPass=/path/to/capture-credentials', 'clone', '--', 'https://example.com/repo');
+
+// throws — via environment variable
+await simpleGit()
+   .env('GIT_ASKPASS', '/path/to/capture-credentials')
+   .clone('https://example.com/repo');
+
+// opt in to setting a custom ask-pass program
+await simpleGit({ unsafe: { allowUnsafeAskPass: true } })
+   .raw('-c', 'core.askPass=/usr/lib/git-core/git-gui--askpass', 'clone', '--', 'https://example.com/repo');
+```
+
+### SSH command
+
+The `core.sshCommand` configuration and the `GIT_SSH` / `GIT_SSH_COMMAND` environment variables define the
+binary used by `git` when making SSH connections. An attacker-controlled value could substitute an arbitrary
+binary for the SSH transport.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — via config flag
+await simpleGit()
+   .raw('-c', 'core.sshCommand=malicious-binary', 'clone', 'git@example.com:repo.git');
+
+// throws — via environment variable
+await simpleGit()
+   .env('GIT_SSH_COMMAND', 'malicious-binary')
+   .clone('git@example.com:repo.git');
+
+// opt in to using a custom SSH binary
+await simpleGit({ unsafe: { allowUnsafeSshCommand: true } })
+   .env('GIT_SSH_COMMAND', 'ssh -i ~/.ssh/deploy_key')
+   .clone('git@example.com:repo.git');
+```
+
+### Git proxy command
+
+The `core.gitProxy` configuration and `GIT_PROXY_COMMAND` environment variable define a command to be
+executed as a proxy for the `git://` transport. Passing an attacker-controlled value here can result in
+arbitrary command execution on each remote operation.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — via config flag
+await simpleGit()
+   .raw('-c', 'core.gitProxy=malicious-binary', 'fetch');
+
+// throws — via environment variable
+await simpleGit()
+   .env('GIT_PROXY_COMMAND', 'malicious-binary')
+   .fetch();
+
+// opt in to using a custom git proxy
+await simpleGit({ unsafe: { allowUnsafeGitProxy: true } })
+   .env('GIT_PROXY_COMMAND', 'socks5proxywrapper')
+   .fetch();
+```
+
+### Text editor
+
+The `core.editor` and `sequence.editor` configurations and the `EDITOR` / `GIT_EDITOR` / `GIT_SEQUENCE_EDITOR`
+environment variables define the text editor binary that `git` will open for interactive operations.
+`core.editor` is used for commit messages and similar prompts; `sequence.editor` and `GIT_SEQUENCE_EDITOR`
+are used specifically for the interactive rebase todo list. A malicious value in any of these can substitute
+an arbitrary binary.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — general editor via config
+await simpleGit()
+   .raw('-c', 'core.editor=malicious-binary', 'commit', '--amend');
+
+// throws — rebase sequence editor via config
+await simpleGit()
+   .raw('-c', 'sequence.editor=malicious-binary', 'rebase', '-i', 'HEAD~3');
+
+// throws — via environment variable
+await simpleGit()
+   .env('GIT_SEQUENCE_EDITOR', 'malicious-binary')
+   .raw('rebase', '-i', 'HEAD~3');
+
+// opt in to using a custom editor
+await simpleGit({ unsafe: { allowUnsafeEditor: true } })
+   .env('GIT_EDITOR', '/usr/bin/nano')
+   .raw('commit', '--amend');
+```
+
+### Pager
+
+The `core.pager` configuration and the `GIT_PAGER` / `PAGER` environment variables control the binary used
+to page output from `git` commands. Substituting a malicious binary here provides an execution path that
+runs for any paged output.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — via config flag
+await simpleGit()
+   .raw('-c', 'core.pager=malicious-binary', 'log');
+
+// throws — via environment variable
+await simpleGit()
+   .env('GIT_PAGER', 'malicious-binary')
+   .log();
+
+// opt in to using a custom pager
+await simpleGit({ unsafe: { allowUnsafePager: true } })
+   .env('GIT_PAGER', 'less -R')
+   .log();
+```
+
+### Hooks path
+
+The `core.hooksPath` configuration redirects `git` to load its event hooks from a location other than the
+default `.git/hooks` directory. Controlling this path allows an attacker to cause arbitrary scripts to be
+run automatically on standard git operations such as `commit` and `merge`.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws
+await simpleGit()
+   .raw('-c', 'core.hooksPath=/attacker/controlled/hooks', 'commit', '-m', 'message');
+
+// opt in to using a custom hooks path
+await simpleGit({ unsafe: { allowUnsafeHooksPath: true } })
+   .raw('-c', 'core.hooksPath=/custom/shared/hooks', 'commit', '-m', 'message');
+```
+
+### Template directory
+
+The `init.templateDir` configuration, `--template` flag, and `GIT_TEMPLATE_DIR` environment variable
+define a directory whose contents are copied into a newly initialised `.git` directory. An attacker-controlled
+template directory can plant hooks or configuration into every repository initialised by the process.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — via config flag
+await simpleGit()
+   .raw('-c', 'init.templateDir=/attacker/controlled/template', 'init', 'new-repo');
+
+// throws — via flag
+await simpleGit()
+   .raw('init', '--template=/attacker/controlled/template', 'new-repo');
+
+// throws — via environment variable
+await simpleGit()
+   .env('GIT_TEMPLATE_DIR', '/attacker/controlled/template')
+   .init('new-repo');
+
+// opt in to using a custom template directory
+await simpleGit({ unsafe: { allowUnsafeTemplateDir: true } })
+   .raw('init', '--template=/custom/template', 'new-repo');
+```
+
+### External diff tool
+
+The `diff.external` configuration, per-driver `diff.<driver>.command`, and `GIT_EXTERNAL_DIFF` environment
+variable define an external binary that `git` calls to generate diffs. Substituting an attacker-controlled
+binary gives it read access to every file involved in a diff operation.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — global external diff via config
+await simpleGit()
+   .raw('-c', 'diff.external=malicious-diff-tool', 'diff');
+
+// throws — per-driver diff command via config
+await simpleGit()
+   .raw('-c', 'diff.pdf.command=malicious-diff-tool', 'diff', 'document.pdf');
+
+// throws — via environment variable
+await simpleGit()
+   .env('GIT_EXTERNAL_DIFF', 'malicious-diff-tool')
+   .diff();
+
+// opt in to using a custom diff tool
+await simpleGit({ unsafe: { allowUnsafeDiffExternal: true } })
+   .env('GIT_EXTERNAL_DIFF', '/usr/local/bin/my-diff-tool')
+   .diff();
+```
+
+### Diff text conversion
+
+The `diff.textconv` configuration (set per driver via `diff.<driver>.textconv`) defines a binary that converts
+file content to text before generating a diff. This binary is called automatically whenever git diffs a file
+with a matching driver and has read access to the file's content.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws
+await simpleGit()
+   .raw('-c', 'diff.pdf.textconv=malicious-converter', 'diff', 'document.pdf');
+
+// opt in to using a custom text converter
+await simpleGit({ unsafe: { allowUnsafeDiffTextConv: true } })
+   .raw('-c', 'diff.pdf.textconv=pdftotext', 'diff', 'document.pdf');
+```
+
+### Filter operations
+
+The `filter.<driver>.clean` and `filter.<driver>.smudge` configuration values define binaries that transform
+file content when checking out (`smudge`) and staging (`clean`). Controlling either value allows an attacker
+to read or modify every file that passes through the filter.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — clean filter
+await simpleGit()
+   .raw('-c', 'filter.lfs.clean=malicious-binary', 'add', '.');
+
+// throws — smudge filter
+await simpleGit()
+   .raw('-c', 'filter.lfs.smudge=malicious-binary', 'checkout', 'main');
+
+// opt in to using custom filter binaries
+await simpleGit({ unsafe: { allowUnsafeFilter: true } })
+   .raw('-c', 'filter.lfs.clean=git-lfs clean -- %f', '-c', 'filter.lfs.smudge=git-lfs smudge -- %f', 'checkout', 'main');
+```
+
+### File system monitor
+
+The `core.fsmonitor` configuration specifies an external binary that `git` uses to track file system changes.
+This binary is invoked automatically in the background during many common operations, making it a persistent
+execution path if an attacker can control the value.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws
+await simpleGit()
+   .raw('-c', 'core.fsmonitor=malicious-monitor', 'status');
+
+// opt in to using a custom file system monitor
+await simpleGit({ unsafe: { allowUnsafeFsMonitor: true } })
+   .raw('-c', 'core.fsmonitor=true', 'status');
+```
+
+### GPG signing program
+
+The `gpg.program` configuration defines the binary used to sign commits and tags. Per-format variants
+`gpg.ssh.program` and `gpg.x509.program` select the signing binary for SSH and X.509 signatures
+respectively. All three are matched by a single block on `gpg.*.program`. Controlling any of these values
+allows an attacker to run an arbitrary binary whenever a signed commit or tag is created.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — default GPG program
+await simpleGit()
+   .raw('-c', 'gpg.program=malicious-binary', 'commit', '-S', '-m', 'signed commit');
+
+// throws — SSH signing program
+await simpleGit()
+   .raw('-c', 'gpg.ssh.program=malicious-binary', 'commit', '-S', '-m', 'signed commit');
+
+// opt in to using a custom GPG binary
+await simpleGit({ unsafe: { allowUnsafeGpgProgram: true } })
+   .raw('-c', 'gpg.program=/usr/local/bin/gpg2', 'commit', '-S', '-m', 'signed commit');
+```
+
+### Merge drivers
+
+The `merge.driver`, `mergetool.cmd`, and `mergetool.path` configurations define external binaries used to
+resolve merge conflicts. Controlling any of these values allows an attacker to run arbitrary code whenever
+a merge conflict occurs.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — custom merge driver
+await simpleGit()
+   .raw('-c', 'merge.union.driver=malicious-merger %O %A %B', 'merge', 'feature-branch');
+
+// throws — merge tool command
+await simpleGit()
+   .raw('-c', 'mergetool.custom.cmd=malicious-binary $MERGED', 'mergetool');
+
+// opt in to using custom merge drivers
+await simpleGit({ unsafe: { allowUnsafeMergeDriver: true } })
+   .raw('-c', 'mergetool.vimdiff.path=/usr/bin/vim', 'mergetool');
+```
+
+### Configuration paths via environment variables
+
+The `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_CONFIG`, `GIT_EXEC_PATH`, and `PREFIX` environment
+variables override the paths `git` uses to locate its configuration files and built-in commands. Controlling
+these paths allows an attacker to supply an entirely malicious git configuration or replace git's built-in
+commands with arbitrary binaries.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws
+await simpleGit()
+   .env('GIT_CONFIG_GLOBAL', '/attacker/controlled/gitconfig')
+   .clone('https://example.com/repo');
+
+// opt in to overriding git configuration paths
+await simpleGit({ unsafe: { allowUnsafeConfigPaths: true } })
+   .env('GIT_CONFIG_GLOBAL', '/custom/global/gitconfig')
+   .clone('https://example.com/repo');
+```
+
+### Environment-based configuration
+
+Git supports injecting configuration values at runtime through a set of numbered environment variables:
+`GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_n`, and `GIT_CONFIG_VALUE_n`. When `GIT_CONFIG_COUNT` is set to `N`,
+git reads `N` key/value pairs from the corresponding environment variables and treats them as the highest
+priority configuration. Because this mechanism can set any configuration value, the injected keys are
+subject to the same block-listing checks as values passed via `-c` flags.
+
+```typescript
+import { simpleGit } from 'simple-git';
+
+// throws — GIT_CONFIG_COUNT triggers the check; the injected key is also evaluated
+await simpleGit()
+   .env({
+      GIT_CONFIG_COUNT: '1',
+      GIT_CONFIG_KEY_0: 'core.hooksPath',
+      GIT_CONFIG_VALUE_0: '/attacker/hooks',
+   })
+   .commit('message');
+
+// opt in to using environment-based configuration injection
+await simpleGit({ unsafe: { allowUnsafeConfigEnvCount: true } })
+   .env({
+      GIT_CONFIG_COUNT: '1',
+      GIT_CONFIG_KEY_0: 'user.email',
+      GIT_CONFIG_VALUE_0: 'ci-bot@example.com',
+   })
+   .commit('CI build commit');
+```
diff --git a/packages/argv-parser/index.ts b/packages/argv-parser/index.ts
index fa984a8f74f98fa861951b9e7fc9a50c6825bfb0..531663de71092d1dec78267522aeeb2792a7e4a7 100644
--- a/packages/argv-parser/index.ts
+++ b/packages/argv-parser/index.ts
@@ -1,13 +1,15 @@
-export { parseArgv } from './src/parse-argv';
+export { parseArgv } from './src/args/parse-argv';
 export type {
    ConfigRead,
    ConfigScope,
    ConfigWrite,
    ParsedArgv,
    ParsedFlag,
-} from './src/parse-argv.types';
+} from './src/args/parse-argv.types';
+export { parseEnv } from './src/env/parse-env';
 export type {
    Vulnerability,
    VulnerabilityCategory,
+   VulnerabilityCategoryFlags,
 } from './src/vulnerabilities/vulnerability.types';
-export { vulnerabilityAnalysis } from './src/vulnerabilities/vulnerability-analysis';
+export { vulnerabilityCheck } from './src/vulnerabilities/vulnerability-check';
diff --git a/packages/argv-parser/src/parse-argv.ts b/packages/argv-parser/src/args/parse-argv.ts
similarity index 74%
rename from packages/argv-parser/src/parse-argv.ts
rename to packages/argv-parser/src/args/parse-argv.ts
index 01e88363cbfe2be5989a4d6a6c912a2183ec450a..4c2e4c09e339c2db7848feec479545261f01791e 100644
--- a/packages/argv-parser/src/parse-argv.ts
+++ b/packages/argv-parser/src/args/parse-argv.ts
@@ -1,9 +1,9 @@
-import { collectConfigAccess } from './config/analyse-config';
-import type { Flag } from './flags/flags.helpers';
-import { parseGlobalFlags } from './flags/parse-global-flags';
-import { parseTaskFlags } from './flags/parse-task-flags';
+import { collectConfigAccess } from '../config/analyse-config';
+import type { Flag } from '../flags/flags.helpers';
+import { parseGlobalFlags } from '../flags/parse-global-flags';
+import { parseTaskFlags } from '../flags/parse-task-flags';
+import { vulnerabilityAnalysis } from '../vulnerabilities/vulnerability-analysis';
 import type { ParsedArgv, ParsedFlag } from './parse-argv.types';
-import { vulnerabilityAnalysis } from './vulnerabilities/vulnerability-analysis';
 
 /**
  * Parse the tokens that would be forwarded to a `git` child-process and
diff --git a/packages/argv-parser/src/parse-argv.types.ts b/packages/argv-parser/src/args/parse-argv.types.ts
similarity index 94%
rename from packages/argv-parser/src/parse-argv.types.ts
rename to packages/argv-parser/src/args/parse-argv.types.ts
index c421591046a299912f4e3486dfffcb33f00c88f8..ecdfe6fafa7a4273ac81d7cbe55855ebb9843967 100644
--- a/packages/argv-parser/src/parse-argv.types.ts
+++ b/packages/argv-parser/src/args/parse-argv.types.ts
@@ -1,4 +1,4 @@
-import type { ParsedVulnerabilities } from './vulnerabilities/vulnerability.types';
+import type { Vulnerability } from '../vulnerabilities/vulnerability.types';
 
 /** Where a config value originates / which scope it targets. */
 export type ConfigScope =
@@ -72,5 +72,5 @@ export interface ParsedArgv {
    /**
     * Attack vectors discovered in the arguments
     */
-   vulnerabilities: ParsedVulnerabilities;
+   readonly vulnerabilities: Vulnerability[];
 }
diff --git a/packages/argv-parser/src/config/analyse-config.ts b/packages/argv-parser/src/config/analyse-config.ts
index 70a48b884b3b4ea8def2bc24bbb4c03972073dc9..8a06e4636e6fbb5bd9f82f86353f058cc9617562 100644
--- a/packages/argv-parser/src/config/analyse-config.ts
+++ b/packages/argv-parser/src/config/analyse-config.ts
@@ -1,5 +1,5 @@
+import type { ConfigScope, ConfigWrite, ParsedConfigActivity } from '../args/parse-argv.types';
 import { type Flag, scopedFlags } from '../flags/flags.helpers';
-import type { ConfigScope, ConfigWrite, ParsedConfigActivity } from '../parse-argv.types';
 import type { ConfigOperation } from './config.types';
 import { detectConfigAction, toOperation } from './detect-config-action';
 
diff --git a/packages/argv-parser/src/config/detect-config-action.ts b/packages/argv-parser/src/config/detect-config-action.ts
index 1e4f272e80f1507a782b338522eb34472757328e..3277520e17b9f7db95751b139d87b1185b1c4b16 100644
--- a/packages/argv-parser/src/config/detect-config-action.ts
+++ b/packages/argv-parser/src/config/detect-config-action.ts
@@ -1,5 +1,5 @@
+import type { ConfigScope } from '../args/parse-argv.types';
 import { type Flag, scopedFlags } from '../flags/flags.helpers';
-import type { ConfigScope } from '../parse-argv.types';
 import type { ConfigOperation } from './config.types';
 import {
    CONFIG_READ_FLAGS,
diff --git a/packages/argv-parser/src/env/parse-env.ts b/packages/argv-parser/src/env/parse-env.ts
new file mode 100644
index 0000000000000000000000000000000000000000..5128bdc1bcf32f018443f15904c8e8ed3b6ed13d
--- /dev/null
+++ b/packages/argv-parser/src/env/parse-env.ts
@@ -0,0 +1,84 @@
+import type { ConfigWrite, ParsedConfigActivity } from '../args/parse-argv.types';
+import type { Vulnerability, VulnerabilityCategory } from '../vulnerabilities/vulnerability.types';
+import { vulnerabilityAnalysis } from '../vulnerabilities/vulnerability-analysis';
+
+const GitEnvKeys = {
+   'editor': 'allowUnsafeEditor',
+   'git_askpass': 'allowUnsafeAskPass',
+   'git_config_global': 'allowUnsafeConfigPaths',
+   'git_config_system': 'allowUnsafeConfigPaths',
+   'git_config_count': 'allowUnsafeConfigEnvCount',
+   'git_config': 'allowUnsafeConfigPaths',
+   'git_editor': 'allowUnsafeEditor',
+   'git_exec_path': 'allowUnsafeConfigPaths',
+   'git_external_diff': 'allowUnsafeDiffExternal',
+   'git_pager': 'allowUnsafePager',
+   'git_proxy_command': 'allowUnsafeGitProxy',
+   'git_template_dir': 'allowUnsafeTemplateDir',
+   'git_sequence_editor': 'allowUnsafeEditor',
+   'git_ssh': 'allowUnsafeSshCommand',
+   'git_ssh_command': 'allowUnsafeSshCommand',
+   'pager': 'allowUnsafePager',
+   'prefix': 'allowUnsafeConfigPaths',
+   'ssh_askpass': 'allowUnsafeAskPass',
+} as const satisfies Record<string, VulnerabilityCategory>;
+
+type GitEnv = Record<string, string> & {
+   git_config_count?: string;
+};
+
+function* collectConfigByCount(env: GitEnv): Generator<ConfigWrite> {
+   const count = parseInt(env.git_config_count ?? '0', 10);
+   for (let index = 0; index < count; index++) {
+      const key = env[`git_config_key_${index}`];
+      const value = env[`git_config_value_${index}`];
+
+      if (key !== undefined) {
+         yield { key: key.toLowerCase().trim(), value, scope: 'env' };
+      }
+   }
+}
+
+function* collectConfigVulnerabilities(env: GitEnv): Generator<Vulnerability> {
+   for (const key of Object.keys(env)) {
+      if (isGitEnvKey(key)) {
+         const category = GitEnvKeys[key];
+         yield {
+            category,
+            message: `Use of "${key.toUpperCase()}" is not permitted without enabling ${category}`,
+         };
+      }
+   }
+}
+
+function isGitEnvKey(key: string): key is keyof typeof GitEnvKeys {
+   return Object.hasOwn(GitEnvKeys, key);
+}
+
+function prepareEnv(env: Record<string, unknown>): GitEnv {
+   const gitEnv: GitEnv = {};
+   for (const [key, value] of Object.entries(env)) {
+      const envKey = key.toLowerCase().trim();
+      if (isGitEnvKey(envKey) || envKey.startsWith('git')) {
+         gitEnv[envKey] = String(value);
+      }
+   }
+   return gitEnv;
+}
+
+export function parseEnv(raw: Record<string, unknown>) {
+   const env = prepareEnv(raw);
+   const config: ParsedConfigActivity = {
+      read: [],
+      write: [...collectConfigByCount(env)],
+   };
+   const vulnerabilities = [
+      ...collectConfigVulnerabilities(env),
+      ...vulnerabilityAnalysis(null, [], config),
+   ];
+
+   return {
+      config,
+      vulnerabilities,
+   };
+}
diff --git a/packages/argv-parser/src/tokens/flag-specs.ts b/packages/argv-parser/src/tokens/flag-specs.ts
index 2acd4f422a641be5892d6ff5963dc6407c28d91c..5c53edde6dc5cd521f5a1dbe96927b94ec764baf 100644
--- a/packages/argv-parser/src/tokens/flag-specs.ts
+++ b/packages/argv-parser/src/tokens/flag-specs.ts
@@ -52,7 +52,7 @@ const COMMANDS: Record<string, FlagSpec> = {
          ['s', false], // -s shared
          ['u', true], // -u <upload-pack>
       ]),
-      long: new Set(['branch', 'config', 'jobs', 'origin', 'upload-pack', 'u']),
+      long: new Set(['branch', 'config', 'jobs', 'origin', 'upload-pack', 'u', 'template']),
    },
    commit: {
       short: new Map([
@@ -76,6 +76,10 @@ const COMMANDS: Record<string, FlagSpec> = {
       short: new Map(),
       long: new Set(['upload-pack']),
    },
+   init: {
+      short: new Map(),
+      long: new Set(['template']),
+   },
    pull: {
       short: new Map(),
       long: new Set(['upload-pack']),
diff --git a/packages/argv-parser/src/vulnerabilities/detect-config-writes.ts b/packages/argv-parser/src/vulnerabilities/detect-config-writes.ts
deleted file mode 100644
index 016935edffecb5ab5949916198a7674ee82faa48..0000000000000000000000000000000000000000
--- a/packages/argv-parser/src/vulnerabilities/detect-config-writes.ts
+++ /dev/null
@@ -1,43 +0,0 @@
-import type { ParsedConfigActivity } from '../parse-argv.types';
-import type { Vulnerability, VulnerabilityCategory } from './vulnerability.types';
-
-export function* detectConfigWrites({ write }: ParsedConfigActivity): Generator<Vulnerability> {
-   for (const config of write) {
-      for (const helper of preventUnsafeConfig) {
-         const vulnerability = helper(config.key);
-         if (vulnerability) {
-            yield vulnerability;
-         }
-      }
-   }
-}
-
-function preventConfigBuilder(
-   config: string | RegExp,
-   category: VulnerabilityCategory,
-   message = String(config)
-) {
-   const regex = typeof config === 'string' ? new RegExp(`\\s*${config}`, 'i') : config;
-
-   return function preventCommand(key: string): Vulnerability | void {
-      if (regex.test(key)) {
-         return {
-            category,
-            message: `Configuring ${message} is not permitted without enabling ${category}`,
-         };
-      }
-   };
-}
-
-const preventUnsafeConfig = [
-   preventConfigBuilder(
-      /^\s*protocol(.[a-z]+)?.allow/i,
-      'allowUnsafeProtocolOverride',
-      'protocol.allow'
-   ),
-   preventConfigBuilder('core.sshCommand', 'allowUnsafeSshCommand'),
-   preventConfigBuilder('core.fsmonitor', 'allowUnsafeFsMonitor'),
-   preventConfigBuilder('core.gitProxy', 'allowUnsafeGitProxy'),
-   preventConfigBuilder('core.hooksPath', 'allowUnsafeHooksPath'),
-   preventConfigBuilder('diff.external', 'allowUnsafeDiffExternal'),
-];
diff --git a/packages/argv-parser/src/vulnerabilities/detect-upload-pack.ts b/packages/argv-parser/src/vulnerabilities/detect-upload-pack.ts
deleted file mode 100644
index ecf45baef965c9a2637c8dfa8e542e32762382b9..0000000000000000000000000000000000000000
--- a/packages/argv-parser/src/vulnerabilities/detect-upload-pack.ts
+++ /dev/null
@@ -1,28 +0,0 @@
-import type { Flag } from '../flags/flags.helpers';
-import type { Vulnerability } from './vulnerability.types';
-
-export function* detectUploadPack(task: null | string, flags: Flag[]): Generator<Vulnerability> {
-   for (const flag of flags) {
-      if (/^--(upload|receive)-pack/.test(flag.name)) {
-         yield {
-            category: 'allowUnsafePack',
-            message:
-               'Use of --upload-pack or --receive-pack is not permitted without enabling allowUnsafePack',
-         };
-      }
-      if (task === 'clone' && (/^-\w*u/.test(flag.name) || flag.name === '--u')) {
-         yield {
-            category: 'allowUnsafePack',
-            message:
-               'Use of clone with option -u is not permitted without enabling allowUnsafePack',
-         };
-      }
-      if (task === 'push' && /^--exec/.test(flag.name)) {
-         yield {
-            category: 'allowUnsafePack',
-            message:
-               'Use of push with option --exec is not permitted without enabling allowUnsafePack',
-         };
-      }
-   }
-}
diff --git a/packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts b/packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts
new file mode 100644
index 0000000000000000000000000000000000000000..06ad20b452588fc9bd94092869021fb2aae44948
--- /dev/null
+++ b/packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts
@@ -0,0 +1,63 @@
+import type { ParsedConfigActivity } from '../args/parse-argv.types';
+import type { Vulnerability, VulnerabilityCategory } from './vulnerability.types';
+
+export function* detectVulnerableConfigWrites({
+   write,
+}: ParsedConfigActivity): Generator<Vulnerability> {
+   for (const config of write) {
+      for (const helper of preventUnsafeConfig) {
+         const vulnerability = helper(config.key);
+         if (vulnerability) {
+            yield vulnerability;
+         }
+      }
+   }
+}
+
+function preventConfigBuilder(
+   config: string | RegExp,
+   category: VulnerabilityCategory,
+   message = String(config)
+) {
+   const regex = typeof config === 'string' ? new RegExp(`\\s*${config.toLowerCase()}`) : config;
+
+   return function preventCommand(key: string): Vulnerability | void {
+      if (regex.test(key)) {
+         return {
+            category,
+            message: `Configuring ${message} is not permitted without enabling ${category}`,
+         };
+      }
+   };
+}
+
+function preventExpandedConfigBuilder(config: string, category: VulnerabilityCategory) {
+   const regex = new RegExp(`\\s*${config.toLowerCase().replace(/\./g, '(\..+)?.')}`);
+   return preventConfigBuilder(regex, category, config);
+}
+
+const preventUnsafeConfig = [
+   preventConfigBuilder('alias', 'allowUnsafeAlias'),
+   preventConfigBuilder('core.askPass', 'allowUnsafeAskPass'),
+   preventConfigBuilder('core.editor', 'allowUnsafeEditor'),
+   preventConfigBuilder('core.fsmonitor', 'allowUnsafeFsMonitor'),
+   preventConfigBuilder('core.gitProxy', 'allowUnsafeGitProxy'),
+   preventConfigBuilder('core.hooksPath', 'allowUnsafeHooksPath'),
+   preventConfigBuilder('core.pager', 'allowUnsafePager'),
+   preventConfigBuilder('core.sshCommand', 'allowUnsafeSshCommand'),
+   preventExpandedConfigBuilder('credential.helper', 'allowUnsafeCredentialHelper'),
+   preventExpandedConfigBuilder('diff.command', 'allowUnsafeDiffExternal'),
+   preventConfigBuilder('diff.external', 'allowUnsafeDiffExternal'),
+   preventExpandedConfigBuilder('diff.textconv', 'allowUnsafeDiffTextConv'),
+   preventExpandedConfigBuilder('filter.clean', 'allowUnsafeFilter'),
+   preventExpandedConfigBuilder('filter.smudge', 'allowUnsafeFilter'),
+   preventExpandedConfigBuilder('gpg.program', 'allowUnsafeGpgProgram'),
+   preventConfigBuilder('init.templateDir', 'allowUnsafeTemplateDir'),
+   preventExpandedConfigBuilder('merge.driver', 'allowUnsafeMergeDriver'),
+   preventExpandedConfigBuilder('mergetool.path', 'allowUnsafeMergeDriver'),
+   preventExpandedConfigBuilder('mergetool.cmd', 'allowUnsafeMergeDriver'),
+   preventExpandedConfigBuilder('protocol.allow', 'allowUnsafeProtocolOverride'),
+   preventExpandedConfigBuilder('remote.receivepack', 'allowUnsafePack'),
+   preventExpandedConfigBuilder('remote.uploadpack', 'allowUnsafePack'),
+   preventConfigBuilder('sequence.editor', 'allowUnsafeEditor'),
+];
diff --git a/packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts b/packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts
new file mode 100644
index 0000000000000000000000000000000000000000..968323e3369972245ffb73fffb49cd3499b4a4cc
--- /dev/null
+++ b/packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts
@@ -0,0 +1,48 @@
+import type { Flag } from '../flags/flags.helpers';
+import type { Vulnerability, VulnerabilityCategory } from './vulnerability.types';
+
+export function* detectVulnerableFlags(
+   task: null | string,
+   flags: Flag[]
+): Generator<Vulnerability> {
+   for (const flag of flags) {
+      for (const helper of preventUnsafeFlags) {
+         const vulnerability = helper(task, flag.name);
+         if (vulnerability) {
+            yield vulnerability;
+         }
+      }
+   }
+}
+
+function preventFlagBuilder(
+   task: string | null,
+   flag: string | RegExp,
+   category: VulnerabilityCategory,
+   name = String(flag)
+) {
+   const regex = typeof flag === 'string' ? new RegExp(`\\s*${flag.toLowerCase()}`) : flag;
+   const message = `Use of ${task ? `${task} with option ` : ''}${name} is not permitted without enabling ${category}`;
+
+   return function preventFlag(currentTask: string | null, flagName: string): Vulnerability | void {
+      if ((!task || currentTask === task) && regex.test(flagName)) {
+         return {
+            category,
+            message,
+         };
+      }
+   };
+}
+
+const preventUnsafeFlags = [
+   preventFlagBuilder(
+      null,
+      /--(upload|receive)-pack/,
+      'allowUnsafePack',
+      '--upload-pack or --receive-pack'
+   ),
+   preventFlagBuilder('clone', /^-\w*u/, 'allowUnsafePack'),
+   preventFlagBuilder('clone', '--u', 'allowUnsafePack'),
+   preventFlagBuilder('push', '--exec', 'allowUnsafePack'),
+   preventFlagBuilder(null, '--template', 'allowUnsafeTemplateDir'),
+];
diff --git a/packages/argv-parser/src/vulnerabilities/vulnerability-analysis.ts b/packages/argv-parser/src/vulnerabilities/vulnerability-analysis.ts
index dbc2ee62a8e37de46b66e6da6a67d54406fc3aa5..caf41591036ea0b089735575a91b87fd95739904 100644
--- a/packages/argv-parser/src/vulnerabilities/vulnerability-analysis.ts
+++ b/packages/argv-parser/src/vulnerabilities/vulnerability-analysis.ts
@@ -1,28 +1,13 @@
+import type { ParsedConfigActivity } from '../args/parse-argv.types';
 import type { Flag } from '../flags/flags.helpers';
-import type { ParsedConfigActivity } from '../parse-argv.types';
-import { detectConfigWrites } from './detect-config-writes';
-import { detectUploadPack } from './detect-upload-pack';
-import type {
-   ParsedVulnerabilities,
-   Vulnerability,
-   VulnerabilityCategory,
-} from './vulnerability.types';
+import { detectVulnerableConfigWrites } from './detect-vulnerable-config-writes';
+import { detectVulnerableFlags } from './detect-vulnerable-flags';
+import type { Vulnerability } from './vulnerability.types';
 
 export function vulnerabilityAnalysis(
    task: null | string,
    flags: Flag[],
    config: ParsedConfigActivity
-): ParsedVulnerabilities {
-   const vulnerabilities: Vulnerability[] = [
-      ...detectUploadPack(task, flags),
-      ...detectConfigWrites(config),
-   ];
-   const categories = vulnerabilities.reduce((all, vulnerability) => {
-      return all.add(vulnerability.category);
-   }, new Set<VulnerabilityCategory>());
-
-   return {
-      categories,
-      vulnerabilities,
-   };
+): Vulnerability[] {
+   return [...detectVulnerableFlags(task, flags), ...detectVulnerableConfigWrites(config)];
 }
diff --git a/packages/argv-parser/src/vulnerabilities/vulnerability-check.ts b/packages/argv-parser/src/vulnerabilities/vulnerability-check.ts
new file mode 100644
index 0000000000000000000000000000000000000000..5cb09adc82e03e05e06ba2027804000923316bd3
--- /dev/null
+++ b/packages/argv-parser/src/vulnerabilities/vulnerability-check.ts
@@ -0,0 +1,10 @@
+import { parseArgv } from '../args/parse-argv';
+import { parseEnv } from '../env/parse-env';
+
+/**
+ * Retrieves just the vulnerabilities identified in the supplied varargs tokens
+ * and environment variables.
+ */
+export function vulnerabilityCheck(tokens: readonly string[], env: Record<string, unknown>) {
+   return [...parseArgv(...tokens).vulnerabilities, ...parseEnv(env).vulnerabilities];
+}
diff --git a/packages/argv-parser/src/vulnerabilities/vulnerability.types.ts b/packages/argv-parser/src/vulnerabilities/vulnerability.types.ts
index b98c0d312719e48ec1a95f6d476c7c5cb3dcf131..9d9f8c60f55bd0fbdf33c7dbb5f8d4447d59fd75 100644
--- a/packages/argv-parser/src/vulnerabilities/vulnerability.types.ts
+++ b/packages/argv-parser/src/vulnerabilities/vulnerability.types.ts
@@ -1,18 +1,124 @@
-export type VulnerabilityCategory =
-   | 'allowUnsafeDiffExternal'
-   | 'allowUnsafeFsMonitor'
-   | 'allowUnsafeGitProxy'
-   | 'allowUnsafeHooksPath'
-   | 'allowUnsafePack'
-   | 'allowUnsafeProtocolOverride'
-   | 'allowUnsafeSshCommand';
+export type VulnerabilityCategory = keyof VulnerabilityCategoryFlags;
 
 export interface Vulnerability {
    category: VulnerabilityCategory;
    message: string;
 }
 
-export interface ParsedVulnerabilities {
-   categories: Set<VulnerabilityCategory>;
-   vulnerabilities: Vulnerability[];
+export interface VulnerabilityCategoryFlags {
+   /**
+    * Use of the `alias.*` configuration settings in simple-git tasks
+    */
+   allowUnsafeAlias: boolean;
+
+   /**
+    * Use of the `core.askPass` configuration setting and environment variables in simple-git tasks
+    */
+   allowUnsafeAskPass: boolean;
+
+   /**
+    * Allows using environment variables to set configuration paths in simple-git tasks
+    */
+   allowUnsafeConfigPaths: boolean;
+
+   /**
+    * Allows setting configuration fields from environment variables in simple-git tasks. Any
+    * configuration set in this way will still be subject to the same block-listing checks and
+    * may require other unsafe flags to be enabled for use.
+    */
+   allowUnsafeConfigEnvCount: boolean;
+
+   /**
+    * Allows setting credential helper in simple-git tasks
+    */
+   allowUnsafeCredentialHelper: boolean;
+
+   /**
+    * Allows setting path to the text editor utility in simple-git tasks
+    */
+   allowUnsafeEditor: boolean;
+
+   /**
+    * Allows use of setting paths for merge tools in simple-git tasks
+    */
+   allowUnsafeMergeDriver: boolean;
+
+   /**
+    * Allows setting path to the pager utility in simple-git tasks
+    */
+   allowUnsafePager: boolean;
+
+   /**
+    * By default, `simple-git` prevents the use of inline configuration
+    * options to override the protocols available for the `git` child
+    * process to prevent accidental security vulnerabilities when
+    * unsanitised user data is passed directly into operations such as
+    * `git.addRemote`, `git.clone` or `git.raw`.
+    *
+    * Enable this override to use the `ext::` protocol (see examples on
+    * [git-scm.com](https://git-scm.com/docs/git-remote-ext#_examples)).
+    */
+   allowUnsafeProtocolOverride: boolean;
+
+   /**
+    * Given the possibility of using `--upload-pack` and `--receive-pack` as
+    * attack vectors, the use of these in any command (or the shorthand
+    * `-u` option in a `clone` operation) are blocked by default.
+    *
+    * Enable this override to permit the use of these arguments.
+    */
+   allowUnsafePack: boolean;
+
+   /**
+    * Using a `-c` switch to enable custom SSH commands opens up a potential
+    * attack vector for running arbitrary commands.
+    */
+   allowUnsafeSshCommand: boolean;
+
+   /**
+    * Using a `-c` switch to enable custom proxy command for the `git://` transport
+    * exposes and attack vector for running arbitrary commands.
+    */
+   allowUnsafeGitProxy: boolean;
+
+   /**
+    * Using a `-c` switch to enable custom hooks path commands to be run automatically
+    * exposes and attack vector for running arbitrary commands.
+    */
+   allowUnsafeHooksPath: boolean;
+
+   /**
+    * Using a `-c` switch to enable setting binary for processing diffs
+    * exposes and attack vector for running arbitrary commands.
+    */
+   allowUnsafeDiffExternal: boolean;
+
+   /**
+    * Using a `-c` switch to enable setting binary for retrieving text content of a file
+    */
+   allowUnsafeDiffTextConv: boolean;
+
+   /**
+    * Using a `-c` switch to enable setting binary for `smudge` and `clean` operations
+    * which can add and remove content to a file during checkout and commit.
+    */
+   allowUnsafeFilter: boolean;
+
+   /**
+    * Using a `-c` switch to enable setting the binary to which `git` will delegate
+    * file content change detection.
+    */
+   allowUnsafeFsMonitor: boolean;
+
+   /**
+    * Using a `-c` switch to configure the GPG signing program (`gpg.program`) or a
+    * per-format variant (`gpg.ssh.program`, `gpg.x509.program`). Controlling the signing
+    * binary allows an attacker to run arbitrary code whenever a commit or tag is signed.
+    */
+   allowUnsafeGpgProgram: boolean;
+
+   /**
+    * Allows overriding template directory either by environment variable or configuration in simple-git tasks
+    */
+   allowUnsafeTemplateDir: boolean;
 }
diff --git a/packages/argv-parser/test/__fixtures__/mocks.ts b/packages/argv-parser/test/__fixtures__/mocks.ts
index c0e549d53d12d5d5a0063fbf3c96f26bd27984ae..2216b1ffe4dd3bc840a46cc533cb3675757e346d 100644
--- a/packages/argv-parser/test/__fixtures__/mocks.ts
+++ b/packages/argv-parser/test/__fixtures__/mocks.ts
@@ -1,4 +1,7 @@
-import type { ConfigRead, ConfigWrite, ParsedFlag } from '../../src/parse-argv.types';
+import { expect } from 'vitest';
+
+import type { ConfigRead, ConfigWrite, ParsedFlag } from '../../src/args/parse-argv.types';
+import type { VulnerabilityCategory } from '../../src/vulnerabilities/vulnerability.types';
 
 export function aParsedFlag(name: string, value?: string): ParsedFlag {
    return value !== undefined ? { name: name, value } : { name: name };
@@ -15,3 +18,18 @@ export function aWriteConfig(
 export function aReadConfig(key: string, scope: ConfigRead['scope']): ConfigRead {
    return { key, scope };
 }
+
+export function aVulnerability(category: VulnerabilityCategory) {
+   return {
+      category,
+      message: expect.stringContaining(`enabling ${category}`),
+   };
+}
+
+export function oneVulnerability(category: VulnerabilityCategory) {
+   return [aVulnerability(category)];
+}
+
+export function noVulnerabilities() {
+   return [];
+}
diff --git a/packages/argv-parser/test/attack-vectors.spec.ts b/packages/argv-parser/test/attack-vectors.spec.ts
index b371c87388b82461244d63e6a6e805a336346eb3..193d81c5b2ec5414d80bbb97f333cb50a09e5007 100644
--- a/packages/argv-parser/test/attack-vectors.spec.ts
+++ b/packages/argv-parser/test/attack-vectors.spec.ts
@@ -1,7 +1,7 @@
-import { parseArgv } from '@simple-git/argv-parser';
+import { parseArgv, parseEnv } from '@simple-git/argv-parser';
 import { describe, expect, it } from 'vitest';
 
-import { aWriteConfig } from './__fixtures__/mocks';
+import { aWriteConfig, oneVulnerability } from './__fixtures__/mocks';
 
 describe('security edge cases', () => {
    it('detects core.sshCommand injection via -c on any sub-command', () => {
@@ -71,4 +71,15 @@ describe('security edge cases', () => {
       expect(flags).toEqual([]);
       expect(paths).toContain('-not-a-flag');
    });
+
+   it('detects use of template directory', () => {
+      const expected = oneVulnerability('allowUnsafeTemplateDir');
+
+      expect(parseArgv('any-cmd', '-c', 'init.templateDir=/foo')).toHaveProperty(
+         'vulnerabilities',
+         expected
+      );
+      expect(parseArgv('any-cmd', '--template=/foo')).toHaveProperty('vulnerabilities', expected);
+      expect(parseEnv({ 'Git_Template_Dir': '/foo' })).toHaveProperty('vulnerabilities', expected);
+   });
 });
diff --git a/packages/argv-parser/test/parse-argv.spec.ts b/packages/argv-parser/test/parse-argv.spec.ts
index 8b692b09f8cec5deb4e718107e7916ab0879bc81..11089461996b4a2f704b262009b123ca0f558cdd 100644
--- a/packages/argv-parser/test/parse-argv.spec.ts
+++ b/packages/argv-parser/test/parse-argv.spec.ts
@@ -17,7 +17,7 @@ describe('full ParsedArgv shape', () => {
          flags: [aParsedFlag('-m', 'initial')],
          paths: [],
          config: { write: [], read: [] },
-         vulnerabilities: { categories: new Set(), vulnerabilities: [] },
+         vulnerabilities: [],
       });
    });
 
@@ -27,7 +27,7 @@ describe('full ParsedArgv shape', () => {
          flags: [aParsedFlag('--force')],
          paths: [],
          config: { write: [], read: [] },
-         vulnerabilities: { categories: new Set(), vulnerabilities: [] },
+         vulnerabilities: [],
       });
    });
 
@@ -37,7 +37,7 @@ describe('full ParsedArgv shape', () => {
          flags: [],
          paths: [],
          config: { write: [], read: [] },
-         vulnerabilities: { categories: new Set(), vulnerabilities: [] },
+         vulnerabilities: [],
       });
    });
 
@@ -47,7 +47,7 @@ describe('full ParsedArgv shape', () => {
          flags: [],
          paths: [],
          config: { write: [], read: [] },
-         vulnerabilities: { categories: new Set(), vulnerabilities: [] },
+         vulnerabilities: [],
       });
    });
 
diff --git a/packages/argv-parser/test/parse-env.spec.ts b/packages/argv-parser/test/parse-env.spec.ts
new file mode 100644
index 0000000000000000000000000000000000000000..a932c4ae7d06df8712919d88f6832253df9669b1
--- /dev/null
+++ b/packages/argv-parser/test/parse-env.spec.ts
@@ -0,0 +1,71 @@
+import { parseEnv, type VulnerabilityCategory } from '@simple-git/argv-parser';
+import { describe, expect, it } from 'vitest';
+
+import {
+   aVulnerability,
+   aWriteConfig,
+   noVulnerabilities,
+   oneVulnerability,
+} from './__fixtures__/mocks';
+
+describe('parseEnv', () => {
+   describe('permitted settings', () => {
+      it('allows empty environment variables', () => {
+         expect(parseEnv({})).toHaveProperty('vulnerabilities', noVulnerabilities());
+      });
+
+      it('allows innocuous environment variables', () => {
+         expect(parseEnv({ 'PATH': '...', LANG: 'C', LC_ALL: 'C' })).toHaveProperty(
+            'vulnerabilities',
+            noVulnerabilities()
+         );
+      });
+   });
+
+   it.each<[string, string, VulnerabilityCategory | null]>([
+      ['EDITOR', 'malicious', 'allowUnsafeEditor'],
+      ['GIT_ASKPASS', 'malicious', 'allowUnsafeAskPass'],
+      ['GIT_CONFIG_GLOBAL', '/tmp/malicious', 'allowUnsafeConfigPaths'],
+      ['GIT_CONFIG_SYSTEM', '/tmp/malicious', 'allowUnsafeConfigPaths'],
+      ['GIT_CONFIG_COUNT', '1', 'allowUnsafeConfigEnvCount'],
+      ['GIT_CONFIG', '/tmp/malicious', 'allowUnsafeConfigPaths'],
+      ['GIT_EDITOR', '/tmp/malicious', 'allowUnsafeEditor'],
+      ['GIT_SEQUENCE_EDITOR', '/tmp/malicious', 'allowUnsafeEditor'],
+      ['GIT_EXEC_PATH', '/tmp/malicious', 'allowUnsafeConfigPaths'],
+      ['GIT_EXTERNAL_DIFF', '/tmp/malicious', 'allowUnsafeDiffExternal'],
+      ['GIT_PAGER', '/tmp/malicious', 'allowUnsafePager'],
+      ['GIT_PROXY_COMMAND', '/tmp/malicious', 'allowUnsafeGitProxy'],
+      ['GIT_SSH', '/tmp/malicious', 'allowUnsafeSshCommand'],
+      ['GIT_SSH_COMMAND', '/tmp/malicious', 'allowUnsafeSshCommand'],
+      ['PAGER', 'malicious', 'allowUnsafePager'],
+      ['PREFIX', 'malicious', 'allowUnsafeConfigPaths'],
+      ['SSH_ASKPASS', 'malicious', 'allowUnsafeAskPass'],
+   ])('with environment variable %s = %s', (key, value, category) => {
+      const expected = category ? oneVulnerability(category) : noVulnerabilities();
+      const parsed = parseEnv({ [key]: value });
+
+      expect(parsed.vulnerabilities).toEqual(expected);
+   });
+
+   it('triggers configuration warnings when using environment variables', () => {
+      const parsed = parseEnv({
+         'git_config_count': '2',
+         git_config_key_0: 'CORE.FSMonitor',
+         git_config_value_0: 'malicious',
+         git_config_key_1: 'user.name',
+         git_config_value_1: 'bob',
+      });
+
+      expect(parsed).toHaveProperty('config', {
+         read: [],
+         write: [
+            aWriteConfig('core.fsmonitor', 'env', 'malicious'),
+            aWriteConfig('user.name', 'env', 'bob'),
+         ],
+      });
+      expect(parsed).toHaveProperty('vulnerabilities', [
+         aVulnerability('allowUnsafeConfigEnvCount'),
+         aVulnerability('allowUnsafeFsMonitor'),
+      ]);
+   });
+});
diff --git a/packages/argv-parser/test/vulnerability-analysis.spec.ts b/packages/argv-parser/test/vulnerability-analysis.spec.ts
index d67e4d4377b0a552e3e1383291decbb543b2f195..b6a83517c3c3e7d0c29a486c3884866cbc760f75 100644
--- a/packages/argv-parser/test/vulnerability-analysis.spec.ts
+++ b/packages/argv-parser/test/vulnerability-analysis.spec.ts
@@ -1,26 +1,107 @@
 import { parseArgv, type VulnerabilityCategory } from '@simple-git/argv-parser';
 import { describe, expect, it } from 'vitest';
 
-function oneVulnerability(category: VulnerabilityCategory) {
-   return {
-      categories: new Set([category]),
-      vulnerabilities: [
-         {
-            category,
-            message: expect.stringContaining(`enabling ${category}`),
-         },
-      ],
-   };
-}
-
-function noVulnerabilities() {
-   return {
-      categories: new Set(),
-      vulnerabilities: [],
-   };
-}
+import { noVulnerabilities, oneVulnerability } from './__fixtures__/mocks';
 
 describe('VulnerabilityAnalysis', () => {
+   describe('permitted settings', () => {
+      it.skip.each<[string, string]>([
+         ['alias.status', 'safe'],
+         ['core.fsmonitor', 'false'],
+         ['core.gitproxy', 'none'],
+         ['credential.helper', 'osxkeychain'],
+      ])('allows writing %s = %s to the git config', (key, value) => {
+         expect(parseArgv('config', key, value)).toHaveProperty(
+            'vulnerabilities',
+            noVulnerabilities()
+         );
+      });
+
+      it('allows local cloning', () => {
+         const parsed = parseArgv('clone', '--no-checkout', '--', './first', 'second');
+         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
+      });
+
+      it('allows local cloning without checkout', () => {
+         const parsed = parseArgv('clone', '--no-checkout', '--', './first', 'second');
+         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
+      });
+
+      it('clone non-default branch is allowed (#1137)', async () => {
+         const parsed = parseArgv(
+            'clone',
+            '-b',
+            'non-default-branch',
+            '--',
+            'https://github.com/example/bruno.git',
+            '/tmp/target'
+         );
+         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
+      });
+
+      it('allows -u for non-clone commands', async () => {
+         const parsed = parseArgv('push', '-u', 'origin/main');
+         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
+      });
+
+      it('uses pathspec protection for -u in remote', async () => {
+         const parsed = parseArgv('clone', '--', '-u touch /tmp/pwn', 'file:///tmp/zero12');
+         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
+      });
+   });
+
+   it.each<[string, string, VulnerabilityCategory | null]>([
+      ['alias.status', '!malicious', 'allowUnsafeAlias'],
+      ['core.askPass', '!malicious', 'allowUnsafeAskPass'],
+      ['core.editor', 'malicious', 'allowUnsafeEditor'],
+      ['core.fsmonitor', 'malicious', 'allowUnsafeFsMonitor'],
+      ['core.gitproxy', 'malicious', 'allowUnsafeGitProxy'],
+      ['core.hooksPath', '/malicious', 'allowUnsafeHooksPath'],
+      ['core.pager', 'malicious', 'allowUnsafePager'],
+      ['core.sshCommand', 'malicious', 'allowUnsafeSshCommand'],
+      ['credential.helper', '/tmp/evil', 'allowUnsafeCredentialHelper'],
+      ['credential.https://example.com.helper', '!malicious', 'allowUnsafeCredentialHelper'],
+      ['credential.helper', '!malicious', 'allowUnsafeCredentialHelper'],
+      ['diff.command', 'malicious', 'allowUnsafeDiffExternal'],
+      ['diff.driver.command', 'malicious', 'allowUnsafeDiffExternal'],
+      ['diff.external', 'malicious', 'allowUnsafeDiffExternal'],
+      ['diff.textconv', 'malicious', 'allowUnsafeDiffTextConv'],
+      ['diff.driver.textconv', 'malicious', 'allowUnsafeDiffTextConv'],
+      ['filter.clean', 'malicious', 'allowUnsafeFilter'],
+      ['filter.driver.clean', 'malicious', 'allowUnsafeFilter'],
+      ['filter.smudge', 'malicious', 'allowUnsafeFilter'],
+      ['filter.driver.smudge', 'malicious', 'allowUnsafeFilter'],
+      ['gpg.program', 'malicious', 'allowUnsafeGpgProgram'],
+      ['gpg.type.program', 'malicious', 'allowUnsafeGpgProgram'],
+      ['init.templateDir', '/tmp/evil', 'allowUnsafeTemplateDir'],
+      ['merge.driver', '/tmp/evil', 'allowUnsafeMergeDriver'],
+      ['merge.foo.driver', '/tmp/evil', 'allowUnsafeMergeDriver'],
+      ['mergetool.path', '/tmp/evil', 'allowUnsafeMergeDriver'],
+      ['mergetool.foo.path', '/tmp/evil', 'allowUnsafeMergeDriver'],
+      ['mergetool.cmd', '/tmp/evil', 'allowUnsafeMergeDriver'],
+      ['mergetool.foo.cmd', '/tmp/evil', 'allowUnsafeMergeDriver'],
+      ['remote.receivepack', 'malicious', 'allowUnsafePack'],
+      ['remote.https://example.com.receivepack', 'malicious', 'allowUnsafePack'],
+      ['remote.uploadpack', 'malicious', 'allowUnsafePack'],
+      ['remote.https://example.com.uploadpack', 'malicious', 'allowUnsafePack'],
+      ['sequence.editor', 'malicious', 'allowUnsafeEditor'],
+   ])('writing %s = %s to the git config', (key, value, category) => {
+      const expected = category ? oneVulnerability(category) : noVulnerabilities();
+
+      // writing local config
+      expect(parseArgv('config', key, value).vulnerabilities).toEqual(expected);
+
+      // trailing inline config
+      expect(
+         parseArgv('clone', 'remote', 'local', '-c', `${key}=${value}`).vulnerabilities
+      ).toEqual(expected);
+
+      // leading inline config
+      expect(
+         parseArgv('-c', `${key}=${value}`, 'clone', 'remote', 'local').vulnerabilities
+      ).toEqual(expected);
+   });
+
    it.each([
       ['protocol.allow=always'],
       ['PROTOCOL.ALLOW=always'],
@@ -30,7 +111,7 @@ describe('VulnerabilityAnalysis', () => {
       ['protocol.ssh.ALLOW=always'],
       ['protocol.ext.allow=always'],
       ['protocol.git.ALLOW=never'],
-   ])('detects protocol.allow in format %s', async (cmd) => {
+   ])('Case insensitive configuration captures protocol.allow in format "%s"', async (cmd) => {
       const parsed = parseArgv('config', '-c', cmd, 'config', '--list');
       expect(parsed.vulnerabilities).toEqual(oneVulnerability('allowUnsafeProtocolOverride'));
 
@@ -52,7 +133,16 @@ describe('VulnerabilityAnalysis', () => {
 
    it.each<[VulnerabilityCategory, string]>([
       ['allowUnsafeDiffExternal', `diff.external=sh -c 'id > pwned'`],
+      ['allowUnsafeDiffTextConv', `diff.evil.textconv=touch /tmp/proof`],
+      ['allowUnsafeDiffExternal', `diff.evil.command=sh -c 'id > pwned'`],
+      ['allowUnsafeFilter', `filter.evil.clean=touch /tmp/proof`],
+      ['allowUnsafeFilter', `filter.evil.smudge=touch /tmp/proof`],
       ['allowUnsafeGitProxy', `core.gitProxy=sh -c 'id > pwned'`],
+      ['allowUnsafeGpgProgram', `gpg.program=malicious`],
+      ['allowUnsafeGpgProgram', `gpg.ssh.program=malicious`],
+      ['allowUnsafeGpgProgram', `gpg.x509.program=malicious`],
+      ['allowUnsafePack', `remote.origin.uploadpack=malicious`],
+      ['allowUnsafePack', `remote.origin.receivepack=malicious`],
       ['allowUnsafeHooksPath', `core.hooksPath=sh -c 'id > pwned'`],
       ['allowUnsafeFsMonitor', `core.FsMonitor=CMD`],
       ['allowUnsafeSshCommand', `core.sshCommand=sh -c 'id > pwned'`],
@@ -93,38 +183,4 @@ describe('VulnerabilityAnalysis', () => {
          ).toEqual(oneVulnerability('allowUnsafePack'));
       });
    });
-
-   describe('not-vulnerable', () => {
-      it('allows local cloning', () => {
-         const parsed = parseArgv('clone', '--no-checkout', '--', './first', 'second');
-         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
-      });
-
-      it('allows local cloning without checkout', () => {
-         const parsed = parseArgv('clone', '--no-checkout', '--', './first', 'second');
-         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
-      });
-
-      it('clone non-default branch is allowed (#1137)', async () => {
-         const parsed = parseArgv(
-            'clone',
-            '-b',
-            'non-default-branch',
-            '--',
-            'https://github.com/example/bruno.git',
-            '/tmp/target'
-         );
-         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
-      });
-
-      it('allows -u for non-clone commands', async () => {
-         const parsed = parseArgv('push', '-u', 'origin/main');
-         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
-      });
-
-      it('uses pathspec protection for -u in remote', async () => {
-         const parsed = parseArgv('clone', '--', '-u touch /tmp/pwn', 'file:///tmp/zero12');
-         expect(parsed.vulnerabilities).toEqual(noVulnerabilities());
-      });
-   });
 });
diff --git a/packages/argv-parser/test/vulnerability-check.spec.ts b/packages/argv-parser/test/vulnerability-check.spec.ts
new file mode 100644
index 0000000000000000000000000000000000000000..891871acc127d13b5d1c04a69c021f732a7e9013
--- /dev/null
+++ b/packages/argv-parser/test/vulnerability-check.spec.ts
@@ -0,0 +1,36 @@
+import { describe, expect, it } from 'vitest';
+
+import { vulnerabilityCheck } from '../src/vulnerabilities/vulnerability-check';
+import { aVulnerability, noVulnerabilities } from './__fixtures__/mocks';
+
+describe('vulnerability-check', () => {
+   describe('permitted settings', () => {
+      it('allows empty environment variables', () => {
+         expect(vulnerabilityCheck(['config', 'user.name', 'bob'], {})).toEqual(
+            noVulnerabilities()
+         );
+      });
+
+      it('allows innocuous environment variables', () => {
+         expect(vulnerabilityCheck([], { 'PATH': '...', LANG: 'C', LC_ALL: 'C' })).toEqual(
+            noVulnerabilities()
+         );
+      });
+   });
+
+   it('triggers configuration warnings when using environment variables', () => {
+      const parsed = vulnerabilityCheck(['config', 'filter.clean', 'malicious'], {
+         'git_config_count': '2',
+         git_config_key_0: 'CORE.FSMonitor',
+         git_config_value_0: 'malicious',
+         git_config_key_1: 'user.name',
+         git_config_value_1: 'bob',
+      });
+
+      expect(parsed).toEqual([
+         aVulnerability('allowUnsafeFilter'),
+         aVulnerability('allowUnsafeConfigEnvCount'),
+         aVulnerability('allowUnsafeFsMonitor'),
+      ]);
+   });
+});
diff --git a/simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts b/simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts
index 51600b98916a443ed33ab0203bdded1197b13420..7c54ed5ec4edc93f9a5ba036bad2bffadfb6bd90 100644
--- a/simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts
+++ b/simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts
@@ -1,18 +1,16 @@
-import type { SimpleGitPlugin } from './simple-git-plugin';
+import { vulnerabilityCheck } from '@simple-git/argv-parser';
 
 import { GitPluginError } from '../errors/git-plugin-error';
 import type { SimpleGitPluginConfig } from '../types';
-import { parseArgv } from '@simple-git/argv-parser';
+import type { SimpleGitPlugin } from './simple-git-plugin';
 
 export function blockUnsafeOperationsPlugin(
    options: SimpleGitPluginConfig['unsafe'] = {}
 ): SimpleGitPlugin<'spawn.args'> {
    return {
       type: 'spawn.args',
-      action(args) {
-         const parsed = parseArgv(...args);
-
-         for (const vulnerability of parsed.vulnerabilities.vulnerabilities) {
+      action(args, { env }) {
+         for (const vulnerability of vulnerabilityCheck(args, env)) {
             if (options[vulnerability.category] !== true) {
                throw new GitPluginError(undefined, 'unsafe', vulnerability.message);
             }
diff --git a/simple-git/src/lib/plugins/simple-git-plugin.ts b/simple-git/src/lib/plugins/simple-git-plugin.ts
index 05733221cee6ac61342bea3d33128d29761cb013..efe9fa30b3a5c3b47b04636b397ef67d39a53270 100644
--- a/simple-git/src/lib/plugins/simple-git-plugin.ts
+++ b/simple-git/src/lib/plugins/simple-git-plugin.ts
@@ -9,7 +9,9 @@ type SimpleGitTaskPluginContext = {
 export interface SimpleGitPluginTypes {
    'spawn.args': {
       data: string[];
-      context: SimpleGitTaskPluginContext & {};
+      context: SimpleGitTaskPluginContext & {
+         env: Record<string, string | undefined>;
+      };
    };
    'spawn.binary': {
       data: string;
diff --git a/simple-git/src/lib/runners/git-executor-chain.ts b/simple-git/src/lib/runners/git-executor-chain.ts
index 2fceb2e830ebfa27f2a28e5098b2b36a962d6331..043341abc9f57d794e47c8a9aa3eb6bf773f65d0 100644
--- a/simple-git/src/lib/runners/git-executor-chain.ts
+++ b/simple-git/src/lib/runners/git-executor-chain.ts
@@ -81,11 +81,10 @@ export class GitExecutorChain implements SimpleGitExecutor {
 
    private async attemptRemoteTask<R>(task: RunnableTask<R>, logger: OutputLogger) {
       const binary = this._plugins.exec('spawn.binary', '', pluginContext(task, task.commands));
-      const args = this._plugins.exec(
-         'spawn.args',
-         [...task.commands],
-         pluginContext(task, task.commands)
-      );
+      const args = this._plugins.exec('spawn.args', [...task.commands], {
+         ...pluginContext(task, task.commands),
+         env: { ...this.env },
+      });
 
       const raw = await this.gitResponse(
          task,
diff --git a/simple-git/src/lib/types/index.ts b/simple-git/src/lib/types/index.ts
index b8fc95e67be49b22c52e13395a79896751bf8d2b..f4f36cdd871b9edb65d3a1985167c6bdc8dd40dd 100644
--- a/simple-git/src/lib/types/index.ts
+++ b/simple-git/src/lib/types/index.ts
@@ -2,6 +2,7 @@ import type { SpawnOptions } from 'child_process';
 
 import type { SimpleGitTask } from './tasks';
 import type { SimpleGitProgressEvent } from './handlers';
+import { VulnerabilityCategoryFlags } from '@simple-git/argv-parser';
 
 export * from './handlers';
 export * from './tasks';
@@ -129,64 +130,15 @@ export interface SimpleGitPluginConfig {
 
    spawnOptions: Pick<SpawnOptions, 'uid' | 'gid'>;
 
-   unsafe: {
-      /**
-       * Allows potentially unsafe values to be supplied in the `binary` configuration option and
-       * `git.customBinary()` method call.
-       */
-      allowUnsafeCustomBinary?: boolean;
-
-      /**
-       * By default, `simple-git` prevents the use of inline configuration
-       * options to override the protocols available for the `git` child
-       * process to prevent accidental security vulnerabilities when
-       * unsanitised user data is passed directly into operations such as
-       * `git.addRemote`, `git.clone` or `git.raw`.
-       *
-       * Enable this override to use the `ext::` protocol (see examples on
-       * [git-scm.com](https://git-scm.com/docs/git-remote-ext#_examples)).
-       */
-      allowUnsafeProtocolOverride?: boolean;
-
-      /**
-       * Given the possibility of using `--upload-pack` and `--receive-pack` as
-       * attack vectors, the use of these in any command (or the shorthand
-       * `-u` option in a `clone` operation) are blocked by default.
-       *
-       * Enable this override to permit the use of these arguments.
-       */
-      allowUnsafePack?: boolean;
-
-      /**
-       * Using a `-c` switch to enable custom SSH commands opens up a potential
-       * attack vector for running arbitrary commands.
-       */
-      allowUnsafeSshCommand?: boolean;
-
-      /**
-       * Using a `-c` switch to enable custom proxy command for the `git://` transport
-       * exposes and attack vector for running arbitrary commands.
-       */
-      allowUnsafeGitProxy?: boolean;
-
-      /**
-       * Using a `-c` switch to enable custom hooks path commands to be run automatically
-       * exposes and attack vector for running arbitrary commands.
-       */
-      allowUnsafeHooksPath?: boolean;
-
-      /**
-       * Using a `-c` switch to enable setting binary for processing diffs
-       * exposes and attack vector for running arbitrary commands.
-       */
-      allowUnsafeDiffExternal?: boolean;
-
-      /**
-       * Using a `-c` switch to enable setting the binary to which `git` will delegate
-       * file content change detection.
-       */
-      allowUnsafeFsMonitor?: boolean;
-   };
+   unsafe: Partial<
+      VulnerabilityCategoryFlags & {
+         /**
+          * Allows potentially unsafe values to be supplied in the `binary` configuration option and
+          * `git.customBinary()` method call.
+          */
+         allowUnsafeCustomBinary: boolean;
+      }
+   >;
 }
 
 /**
diff --git a/simple-git/test/integration/plugin.unsafe.spec.ts b/simple-git/test/integration/plugin.unsafe.spec.ts
index 033ac960646b9b14a7965e09bace9d53fd4a834d..15886ff03e22c459409fe6b7f3980a41bc48f9c2 100644
--- a/simple-git/test/integration/plugin.unsafe.spec.ts
+++ b/simple-git/test/integration/plugin.unsafe.spec.ts
@@ -8,10 +8,57 @@ import {GitPluginError} from '../..';
 describe('plugin.unsafe', () => {
    let context: SimpleGitTestContext;
 
+   function pwnedPath() {
+      return join(context.root, 'pwn', 'touched');
+   }
+
+   function isPwned() {
+      return exists(pwnedPath());
+   }
+
    process.env.DEBUG = 'simple-git,simple-git:*';
 
    beforeEach(async () => (context = await createTestContext()));
 
+   describe('Command injection through .env', () => {
+      beforeEach( () => context.git.init());
+      beforeEach(() => context.dir('pwn'));
+
+      it('blocks core.fsmonitor by default', async () => {
+         const result = await promiseResult(
+            newSimpleGit(context.root).raw(
+               '-c', `core.fsmonitor=touch ${pwnedPath()}`, 'status'
+            )
+         );
+
+         assertGitError(result.error, 'allowUnsafeFsMonitor')
+         expect(isPwned()).toBe(false);
+
+
+         const unsafeResult = await promiseResult(
+            newSimpleGit(context.root, { unsafe: { allowUnsafeFsMonitor: true }}).raw(
+               '-c', `core.fsmonitor=touch ${pwnedPath()}`, 'status'
+            )
+         );
+
+         expect(unsafeResult.threw).toBe(false);
+         expect(isPwned()).toBe(true);
+      });
+
+      it('blocks filter.clean by default', async () => {
+         await context.file('file');
+
+         const result = await promiseResult(
+            newSimpleGit(context.root).raw(
+               '-c', `filter.evil.clean=touch ${pwnedPath()}`, 'add', 'file.txt'
+            )
+         );
+
+         assertGitError(result.error, 'allowUnsafeFilter')
+         expect(isPwned()).toBe(false);
+      });
+   });
+
    describe('CVE-2022-25860: command execution using clone -u', () => {
       function pwnedPath() {
          return join(context.root, 'pwn', 'touched');
diff --git a/simple-git/test/unit/clone.spec.ts b/simple-git/test/unit/clone.spec.ts
index 556223a7ed1b5045da9239a257a6eff70c51e6fa..ca6cc964905ed63a9bcb421543a1240687e05768 100644
--- a/simple-git/test/unit/clone.spec.ts
+++ b/simple-git/test/unit/clone.spec.ts
@@ -1,12 +1,7 @@
-import { promiseError } from '@kwsites/promise-result';
-import { SimpleGit, TaskOptions } from 'typings';
-import {
-   assertExecutedCommands,
-   assertGitError,
-   closeWithSuccess,
-   newSimpleGit,
-} from './__fixtures__';
-import { pathspec } from '@simple-git/args-pathspec';
+import {promiseError} from '@kwsites/promise-result';
+import {SimpleGit, TaskOptions} from 'typings';
+import {assertExecutedCommands, assertGitError, closeWithSuccess, newSimpleGit,} from './__fixtures__';
+import {pathspec} from '@simple-git/args-pathspec';
 
 describe('clone', () => {
    let git: SimpleGit;
@@ -39,13 +34,13 @@ describe('clone', () => {
       ],
       ['mirror', 'explicitly set', ['r', 'l'], ['clone', '--mirror', '--', 'r', 'l']],
       ['clone', 'kitchen sink', ['https://abcdefghijklmnopqrstuvwxyz01234567890.repo', 'dir',
-         ['--template=<template-directory>', '-l', '-s', '--no-hardlinks', '-q', '-n', '--bare', '--mirror',
+         ['-l', '-s', '--no-hardlinks', '-q', '-n', '--bare', '--mirror',
          '-o', 'alternative-origin', '-b', 'specific-branch', '--separate-git-dir', 'other-path',
          '--depth', '1', '--no-single-branch', '--no-tags', '--recurse-submodules=foo',
          '--no-shallow-submodules', '--no-remote-submodules', '--jobs', '2', '--sparse',
          '--no-reject-shallow', '--filter=sub-path', '--also-filter-submodules']],
 
-         ['clone', '--template=<template-directory>', '-l', '-s', '--no-hardlinks', '-q', '-n', '--bare', '--mirror',
+         ['clone', '-l', '-s', '--no-hardlinks', '-q', '-n', '--bare', '--mirror',
          '-o', 'alternative-origin', '-b', 'specific-branch', '--separate-git-dir', 'other-path',
          '--depth', '1', '--no-single-branch', '--no-tags', '--recurse-submodules=foo',
          '--no-shallow-submodules', '--no-remote-submodules', '--jobs', '2', '--sparse',
@@ -91,12 +86,6 @@ describe('clone', () => {
    });
 
    describe('failures', () => {
-      it('disallows upload-pack as remote/branch', async () => {
-         const error = await promiseError(git.clone('origin', '--upload-pack=touch ./foo'));
-
-         assertGitError(error, 'allowUnsafePack');
-      });
-
       it('disallows upload-pack as varargs', async () => {
          const error = await promiseError(
             git.clone('origin', 'main', {

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### .changeset/config.json
```
{
  "$schema": "https://unpkg.com/@changesets/config@1.6.4/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "linked": [],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": [
    "@simple-git/test-utils"
  ]
}

```

### .changeset/deep-ducks-care.md
[new file in patch, binary, or unreadable in pre-patch tree]

### docs/PLUGIN-UNSAFE-ACTIONS.md
```
## Unsafe Actions

As `simple-git` passes generated arguments through to a child process of the calling node.js process, it is recommended
that any parameter sourced from user input is validated before being passed to the `simple-git` API.

In some cases where there is an elevated potential for harm `simple-git` will throw an exception unless you have
explicitly opted in to the potentially unsafe action.

### Enabling custom upload and receive packs

Instead of using the default `git-receive-pack` and `git-upload-pack` binaries to parse incoming and outgoing
data, `git` can be configured to use _any_ arbitrary binary or evaluable script.

To avoid accidentally triggering the evaluation of a malicious script when merging user provided parameters
into command executed by `simple-git`, custom pack options (usually with the `--receive-pack` and `--upload-pack`)
are blocked without explicitly opting into their use  

```typescript
import { simpleGit } from 'simple-git';

// throws
await simpleGit()
   .raw('push', '--receive-pack=git-receive-pack-custom');

// allows calling clone with a helper transport
await simpleGit({ unsafe: { allowUnsafePack: true } })
   .raw('push', '--receive-pack=git-receive-pack-custom');
```

### Overriding allowed protocols

A standard installation of `git` permits `file`, `http` and `ssh` protocols for a remote. A range of 
[git remote helpers](https://git-scm.com/docs/gitremote-helpers) other than these default few can be
used by referring to te helper name in the remote protocol - for example the git file descriptor transport
[git-remote-fd](https://git-scm.com/docs/git-remote-fd) would be used in a remote protocol such as:

```
git fetch "fd::<infd>[,<outfd>][/<anything>]"
```

To avoid accidentally triggering a helper transport by passing through unsanitised user input to a function
that expects a remote, the use of `-c protocol.fd.allow=always` (or any variant of protocol permission changes)
will cause `simple-git` to throw unless it has been configured with:

```typescript
import { simpleGit } from 'simple-git';

// throws
await simpleGit()
   .raw('clone', 'ext::git-server-alias foo %G/repo', '-c', 'protocol.ext.allow=always');

// allows calling clone with a helper transport
await simpleGit({ unsafe: { allowUnsafeProtocolOverride: true } })
   .raw('clone', 'ext::git-server-alias foo %G/repo', '-c', 'protocol.ext.allow=always');
```

> *Be advised* helper transports can be used to call arbitrary binaries on the host machine.
> Do not allow them in applications where you are not in control of the input parameters.


```

### packages/argv-parser/index.ts
```
export { parseArgv } from './src/parse-argv';
export type {
   ConfigRead,
   ConfigScope,
   ConfigWrite,
   ParsedArgv,
   ParsedFlag,
} from './src/parse-argv.types';
export type {
   Vulnerability,
   VulnerabilityCategory,
} from './src/vulnerabilities/vulnerability.types';
export { vulnerabilityAnalysis } from './src/vulnerabilities/vulnerability-analysis';

```

### packages/argv-parser/src/args/parse-argv.ts
[new file in patch, binary, or unreadable in pre-patch tree]

### packages/argv-parser/src/args/parse-argv.types.ts
[new file in patch, binary, or unreadable in pre-patch tree]

### packages/argv-parser/src/config/analyse-config.ts
```
import { type Flag, scopedFlags } from '../flags/flags.helpers';
import type { ConfigScope, ConfigWrite, ParsedConfigActivity } from '../parse-argv.types';
import type { ConfigOperation } from './config.types';
import { detectConfigAction, toOperation } from './detect-config-action';

function parseAssignment(raw: string | undefined): { key: string; value: string } | null {
   const eq = raw?.indexOf('=') || -1;

   if (!raw || eq < 0) {
      return null;
   }

   return {
      key: raw.slice(0, eq).trim().toLowerCase(),
      value: raw.slice(eq + 1),
   };
}

function detectConfigScope(flags: Flag[]): ConfigScope {
   for (const { name } of scopedFlags(flags, 'task')) {
      switch (name) {
         case '--global':
            return 'global';
         case '--system':
            return 'system';
         case '--worktree':
            return 'worktree';
         case '--local':
            return 'local';
         case '--file':
         case '-f':
            return 'file';
      }
   }
   return 'local';
}

function detectConfigOverrideScope({ name }: Flag): ConfigScope | void {
   if (name === '-c' || name === '--config') {
      return 'inline';
   }
   if (name === '--config-env') {
      return 'env';
   }
}

/**
 * Generates the stream of ConfigWrite settings found in the supplied flags,
 * triggered by `-c` and `--config` for inline configuration and `--config-env`
 * to set a config setting based on environment variable.
 */
function* collectWriteFlags(flags: Flag[]): Generator<ConfigWrite> {
   for (const flag of flags) {
      const scope = detectConfigOverrideScope(flag);
      const assignment = scope && parseAssignment(flag.value);

      if (assignment) {
         yield {
            ...assignment,
            scope,
         };
      }
   }
}

export function collectConfigAccess(
   task: string | null,
   flags: Flag[],
   positionals: string[]
): ParsedConfigActivity {
   const parsedConfig: ParsedConfigActivity = {
      read: [],
      write: [...collectWriteFlags(flags)],
   };

   if (task === 'config') {
      appendParsedConfigAction(
         parsedConfig,
         detectConfigScope(flags),
         detectConfigAction(flags, positionals)
      );
   }

   return parsedConfig;
}

function appendParsedConfigAction(
   parsedConfig: ParsedConfigActivity,
   scope: ConfigScope,
   action: ConfigOperation | null
) {
   if (action === null) {
      return;
   }

   const config = toOperation(scope, action);
   if (action.isWrite) {
      parsedConfig.write.push(config);
   } else {
      parsedConfig.read.push(config);
   }
}

```

### packages/argv-parser/src/config/detect-config-action.ts
```
import { type Flag, scopedFlags } from '../flags/flags.helpers';
import type { ConfigScope } from '../parse-argv.types';
import type { ConfigOperation } from './config.types';
import {
   CONFIG_READ_FLAGS,
   CONFIG_READ_VERBS,
   CONFIG_WRITE_FLAGS,
   CONFIG_WRITE_VERBS,
} from './config-operands';

export function detectConfigAction(flags: Flag[], positionals: string[]): ConfigOperation | null {
   for (const { name } of scopedFlags(flags, 'task')) {
      if (CONFIG_WRITE_FLAGS.has(name)) {
         return configOperation(true, positionals);
      }
      if (CONFIG_READ_FLAGS.has(name)) {
         return configOperation(false, positionals);
      }
   }

   const verb = positionals.at(0)?.toLowerCase();

   if (verb === undefined) {
      return null;
   }

   if (CONFIG_WRITE_VERBS.has(verb)) {
      return configOperation(true, positionals.slice(1));
   }

   if (CONFIG_READ_VERBS.has(verb)) {
      return configOperation(false, positionals.slice(1));
   }

   if (positionals.length === 1) {
      return configOperation(false, positionals);
   }

   return configOperation(true, positionals);
}

function configOperation(isWrite = false, positionals: string[] = []): ConfigOperation | null {
   const key = positionals.at(0)?.toLowerCase();

   if (key === undefined) {
      return null;
   }

   return {
      isWrite,
      isRead: !isWrite,
      key,
      value: positionals.at(1),
   };
}

export function toOperation(scope: ConfigScope, operation: ConfigOperation) {
   if (operation.isWrite && operation.value !== undefined) {
      return { key: operation.key, value: operation.value, scope };
   }
   return { key: operation.key, scope };
}

```

### packages/argv-parser/src/env/parse-env.ts
[new file in patch, binary, or unreadable in pre-patch tree]

### packages/argv-parser/src/tokens/flag-specs.ts
```
// ── Option tables ─────────────────────────────────────────────────────────────
//
// Each scope has:
//   short  – Map<char, consumesNext>  (known single-letter switches; true = takes next token)
//   long   – Set<stem>                (long switch stems, without --, that take the next token)
//
// Only switches listed here are "known". An unknown char anywhere in a combined
// cluster causes the entire cluster to be kept as one opaque token.

export interface FlagSpec {
   readonly short: ReadonlyMap<string, boolean>;
   readonly long: ReadonlySet<string>;
}

const UNIVERSAL: FlagSpec = {
   short: new Map([
      ['c', true], //  -c <k=v>    set config key for this invocation
   ]),
   long: new Set(),
};

export const GLOBAL: FlagSpec = {
   short: new Map([
      ['C', true], //  -C <path>   change working directory
      ['P', false], // -P          no pager (alias for --no-pager)
      ['h', false], // -h          help
      ['p', false], // -p          paginate
      ['v', false], // -v          version
      ...UNIVERSAL.short.entries(),
   ]),
   long: new Set([
      'attr-source',
      'config-env',
      'exec-path',
      'git-dir',
      'list-cmds',
      'namespace',
      'super-prefix',
      'work-tree',
   ]),
};

const COMMANDS: Record<string, FlagSpec> = {
   clone: {
      short: new Map([
         ['b', true], // -b <branch>
         ['j', true], // -j <n>          parallel jobs
         ['l', false], // -l local
         ['n', false], // -n no-checkout
         ['o', true], // -o <name>       remote name
         ['q', false], // -q quiet
         ['s', false], // -s shared
         ['u', true], // -u <upload-pack>
      ]),
      long: new Set(['branch', 'config', 'jobs', 'origin', 'upload-pack', 'u']),
   },
   commit: {
      short: new Map([
         ['C', true], // -C <commit>  reuse message
         ['F', true], // -F <file>    read message from file
         ['c', true], // -c <commit>  reedit message
         ['m', true], // -m <msg>
         ['t', true], // -t <template>
      ]),
      long: new Set(['file', 'message', 'reedit-message', 'reuse-message', 'template']),
   },
   config: {
      short: new Map([
         ['e', false], // -e  open editor
         ['f', true], //  -f <file>
         ['l', false], // -l  list
      ]),
      long: new Set(['blob', 'comment', 'default', 'file', 'type', 'value']),
   },
   fetch: {
      short: new Map(),
      long: new Set(['upload-pack']),
   },
   pull: {
      short: new Map(),
      long: new Set(['upload-pack']),
   },
   push: {
      short: new Map(),
      long: new Set(['exec', 'receive-pack']),
   },
};

const EMPTY: FlagSpec = { short: new Map(), long: new Set() };

export function getFlagSpecForTask(task?: string | null) {
   const spec = COMMANDS[task ?? ''] ?? EMPTY;

   return {
      short: new Map([...UNIVERSAL.short.entries(), ...spec.short.entries()]),
      long: spec.long,
   };
}

```

### packages/argv-parser/src/vulnerabilities/detect-config-writes.ts
```
import type { ParsedConfigActivity } from '../parse-argv.types';
import type { Vulnerability, VulnerabilityCategory } from './vulnerability.types';

export function* detectConfigWrites({ write }: ParsedConfigActivity): Generator<Vulnerability> {
   for (const config of write) {
      for (const helper of preventUnsafeConfig) {
         const vulnerability = helper(config.key);
         if (vulnerability) {
            yield vulnerability;
         }
      }
   }
}

function preventConfigBuilder(
   config: string | RegExp,
   category: VulnerabilityCategory,
   message = String(config)
) {
   const regex = typeof config === 'string' ? new RegExp(`\\s*${config}`, 'i') : config;

   return function preventCommand(key: string): Vulnerability | void {
      if (regex.test(key)) {
         return {
            category,
            message: `Configuring ${message} is not permitted without enabling ${category}`,
         };
      }
   };
}

const preventUnsafeConfig = [
   preventConfigBuilder(
      /^\s*protocol(.[a-z]+)?.allow/i,
      'allowUnsafeProtocolOverride',
      'protocol.allow'
   ),
   preventConfigBuilder('core.sshCommand', 'allowUnsafeSshCommand'),
   preventConfigBuilder('core.fsmonitor', 'allowUnsafeFsMonitor'),
   preventConfigBuilder('core.gitProxy', 'allowUnsafeGitProxy'),
   preventConfigBuilder('core.hooksPath', 'allowUnsafeHooksPath'),
   preventConfigBuilder('diff.external', 'allowUnsafeDiffExternal'),
];

```

### packages/argv-parser/src/vulnerabilities/detect-upload-pack.ts
```
import type { Flag } from '../flags/flags.helpers';
import type { Vulnerability } from './vulnerability.types';

export function* detectUploadPack(task: null | string, flags: Flag[]): Generator<Vulnerability> {
   for (const flag of flags) {
      if (/^--(upload|receive)-pack/.test(flag.name)) {
         yield {
            category: 'allowUnsafePack',
            message:
               'Use of --upload-pack or --receive-pack is not permitted without enabling allowUnsafePack',
         };
      }
      if (task === 'clone' && (/^-\w*u/.test(flag.name) || flag.name === '--u')) {
         yield {
            category: 'allowUnsafePack',
            message:
               'Use of clone with option -u is not permitted without enabling allowUnsafePack',
         };
      }
      if (task === 'push' && /^--exec/.test(flag.name)) {
         yield {
            category: 'allowUnsafePack',
            message:
               'Use of push with option --exec is not permitted without enabling allowUnsafePack',
         };
      }
   }
}

```

### packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts
[new file in patch, binary, or unreadable in pre-patch tree]

### packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts
[new file in patch, binary, or unreadable in pre-patch tree]

### packages/argv-parser/src/vulnerabilities/vulnerability-analysis.ts
```
import type { Flag } from '../flags/flags.helpers';
import type { ParsedConfigActivity } from '../parse-argv.types';
import { detectConfigWrites } from './detect-config-writes';
import { detectUploadPack } from './detect-upload-pack';
import type {
   ParsedVulnerabilities,
   Vulnerability,
   VulnerabilityCategory,
} from './vulnerability.types';

export function vulnerabilityAnalysis(
   task: null | string,
   flags: Flag[],
   config: ParsedConfigActivity
): ParsedVulnerabilities {
   const vulnerabilities: Vulnerability[] = [
      ...detectUploadPack(task, flags),
      ...detectConfigWrites(config),
   ];
   const categories = vulnerabilities.reduce((all, vulnerability) => {
      return all.add(vulnerability.category);
   }, new Set<VulnerabilityCategory>());

   return {
      categories,
      vulnerabilities,
   };
}

```

### packages/argv-parser/src/vulnerabilities/vulnerability-check.ts
[new file in patch, binary, or unreadable in pre-patch tree]

### packages/argv-parser/src/vulnerabilities/vulnerability.types.ts
```
export type VulnerabilityCategory =
   | 'allowUnsafeDiffExternal'
   | 'allowUnsafeFsMonitor'
   | 'allowUnsafeGitProxy'
   | 'allowUnsafeHooksPath'
   | 'allowUnsafePack'
   | 'allowUnsafeProtocolOverride'
   | 'allowUnsafeSshCommand';

export interface Vulnerability {
   category: VulnerabilityCategory;
   message: string;
}

export interface ParsedVulnerabilities {
   categories: Set<VulnerabilityCategory>;
   vulnerabilities: Vulnerability[];
}

```

### simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts
```
import type { SimpleGitPlugin } from './simple-git-plugin';

import { GitPluginError } from '../errors/git-plugin-error';
import type { SimpleGitPluginConfig } from '../types';
import { parseArgv } from '@simple-git/argv-parser';

export function blockUnsafeOperationsPlugin(
   options: SimpleGitPluginConfig['unsafe'] = {}
): SimpleGitPlugin<'spawn.args'> {
   return {
      type: 'spawn.args',
      action(args) {
         const parsed = parseArgv(...args);

         for (const vulnerability of parsed.vulnerabilities.vulnerabilities) {
            if (options[vulnerability.category] !== true) {
               throw new GitPluginError(undefined, 'unsafe', vulnerability.message);
            }
         }

         return args;
      },
   };
}

```

### simple-git/src/lib/plugins/simple-git-plugin.ts
```
import { ChildProcess, SpawnOptions } from 'child_process';
import { GitExecutorResult } from '../types';

type SimpleGitTaskPluginContext = {
   readonly method: string;
   readonly commands: string[];
};

export interface SimpleGitPluginTypes {
   'spawn.args': {
      data: string[];
      context: SimpleGitTaskPluginContext & {};
   };
   'spawn.binary': {
      data: string;
      context: SimpleGitTaskPluginContext & {};
   };
   'spawn.options': {
      data: Partial<SpawnOptions>;
      context: SimpleGitTaskPluginContext & {};
   };
   'spawn.before': {
      data: void;
      context: SimpleGitTaskPluginContext & {
         kill(reason: Error): void;
      };
   };
   'spawn.after': {
      data: void;
      context: SimpleGitTaskPluginContext & {
         spawned: ChildProcess;
         close(exitCode: number, reason?: Error): void;
         kill(reason: Error): void;
      };
   };
   'task.error': {
      data: { error?: Error };
      context: SimpleGitTaskPluginContext & GitExecutorResult;
   };
}

export type SimpleGitPluginType = keyof SimpleGitPluginTypes;

export interface SimpleGitPlugin<T extends SimpleGitPluginType> {
   action(
      data: SimpleGitPluginTypes[T]['data'],
      context: SimpleGitPluginTypes[T]['context']
   ): typeof data;

   type: T;
}

```

### simple-git/src/lib/runners/git-executor-chain.ts
```
import { spawn, SpawnOptions } from 'child_process';
import { GitError } from '../errors/git-error';
import { OutputLogger } from '../git-logger';
import { PluginStore } from '../plugins';
import { EmptyTask, isBufferTask, isEmptyTask } from '../tasks/task';
import {
   GitExecutorResult,
   Maybe,
   outputHandler,
   RunnableTask,
   SimpleGitExecutor,
   SimpleGitTask,
} from '../types';
import { callTaskParser, first, GitOutputStreams, objectToString } from '../utils';
import { Scheduler } from './scheduler';
import { TasksPendingQueue } from './tasks-pending-queue';

export class GitExecutorChain implements SimpleGitExecutor {
   private _chain: Promise<any> = Promise.resolve();
   private _queue = new TasksPendingQueue();
   private _cwd: string | undefined;

   public get cwd() {
      return this._cwd || this._executor.cwd;
   }

   public set cwd(cwd: string) {
      this._cwd = cwd;
   }

   public get env() {
      return this._executor.env;
   }

   public get outputHandler() {
      return this._executor.outputHandler;
   }

   constructor(
      private _executor: SimpleGitExecutor,
      private _scheduler: Scheduler,
      private _plugins: PluginStore
   ) {}

   public chain() {
      return this;
   }

   public push<R>(task: SimpleGitTask<R>): Promise<R> {
      this._queue.push(task);

      return (this._chain = this._chain.then(() => this.attemptTask(task)));
   }

   private async attemptTask<R>(task: SimpleGitTask<R>): Promise<void | R> {
      const onScheduleComplete = await this._scheduler.next();
      const onQueueComplete = () => this._queue.complete(task);

      try {
         const { logger } = this._queue.attempt(task);
         return (await (isEmptyTask(task)
            ? this.attemptEmptyTask(task, logger)
            : this.attemptRemoteTask(task, logger))) as R;
      } catch (e) {
         throw this.onFatalException(task, e as Error);
      } finally {
         onQueueComplete();
         onScheduleComplete();
      }
   }

   private onFatalException<R>(task: SimpleGitTask<R>, e: Error) {
      const gitError =
         e instanceof GitError ? Object.assign(e, { task }) : new GitError(task, e && String(e));

      this._chain = Promise.resolve();
      this._queue.fatal(gitError);

      return gitError;
   }

   private async attemptRemoteTask<R>(task: RunnableTask<R>, logger: OutputLogger) {
      const binary = this._plugins.exec('spawn.binary', '', pluginContext(task, task.commands));
      const args = this._plugins.exec(
         'spawn.args',
         [...task.commands],
         pluginContext(task, task.commands)
      );

      const raw = await this.gitResponse(
         task,
         binary,
         args,
         this.outputHandler,
         logger.step('SPAWN')
      );
      const outputStreams = await this.handleTaskData(task, args, raw, logger.step('HANDLE'));

      logger(`passing response to task's parser as a %s`, task.format);

      if (isBufferTask(task)) {
         return callTaskParser(task.parser, outputStreams);
      }

      return callTaskParser(task.parser, outputStreams.asStrings());
   }

   private async attemptEmptyTask(task: EmptyTask, logger: OutputLogger) {
      logger(`empty task bypassing child process to call to task's parser`);
      return task.parser(this);
   }

   private handleTaskData<R>(
      task: SimpleGitTask<R>,
      args: string[],
      result: GitExecutorResult,
      logger: OutputLogger
   ): Promise<GitOutputStreams> {
      const { exitCode, rejection, stdOut, stdErr } = result;

      return new Promise((done, fail) => {
         logger(`Preparing to handle process response exitCode=%d stdOut=`, exitCode);

         const { error } = this._plugins.exec(
            'task.error',
            { error: rejection },
            {
               ...pluginContext(task, args),
               ...result,
            }
         );

         if (error && task.onError) {
            logger.info(`exitCode=%s handling with custom error handler`);

            return task.onError(
               result,
               error,
               (newStdOut) => {
                  logger.info(`custom error handler treated as success`);
                  logger(`custom error returned a %s`, objectToString(newStdOut));

                  done(
                     new GitOutputStreams(
                        Array.isArray(newStdOut) ? Buffer.concat(newStdOut) : newStdOut,
                        Buffer.concat(stdErr)
                     )
                  );
               },
               fail
            );
         }

         if (error) {
            logger.info(
               `handling as error: exitCode=%s stdErr=%s rejection=%o`,
               exitCode,
               stdErr.length,
               rejection
            );
            return fail(error);
         }

         logger.info(`retrieving task output complete`);
         done(new GitOutputStreams(Buffer.concat(stdOut), Buffer.concat(stdErr)));
      });
   }

   private async gitResponse<R>(
      task: SimpleGitTask<R>,
      command: string,
      args: string[],
      outputHandler: Maybe<outputHandler>,
      logger: OutputLogger
   ): Promise<GitExecutorResult> {
      const outputLogger = logger.sibling('output');
      const spawnOptions: SpawnOptions = this._plugins.exec(
         'spawn.options',
         {
            cwd: this.cwd,
            env: this.env,
            windowsHide: true,
         },
         pluginContext(task, task.commands)
      );

      return new Promise((done) => {
         const stdOut: Buffer[] = [];
         const stdErr: Buffer[] = [];

         logger.info(`%s %o`, command, args);
         logger('%O', spawnOptions);

         let rejection = this._beforeSpawn(task, args);
         if (rejection) {
            return done({
               stdOut,
               stdErr,
               exitCode: 9901,
               rejection,
            });
         }

         this._plugins.exec('spawn.before', undefined, {
            ...pluginContext(task, args),
            kill(reason) {
               rejection = reason || rejection;
            },
         });

         const spawned = spawn(command, args, spawnOptions);

         spawned.stdout!.on(
            'data',
            onDataReceived(stdOut, 'stdOut', logger, outputLogger.step('stdOut'))
         );
         spawned.stderr!.on(
            'data',
            onDataReceived(stdErr, 'stdErr', logger, outputLogger.step('stdErr'))
         );

         spawned.on('error', onErrorReceived(stdErr, logger));

         if (outputHandler) {
            logger(`Passing child process stdOut/stdErr to custom outputHandler`);
            outputHandler(command, spawned.stdout!, spawned.stderr!, [...args]);
         }

         this._plugins.exec('spawn.after', undefined, {
            ...pluginContext(task, args),
            spawned,
            close(exitCode: number, reason?: Error) {
               done({
                  stdOut,
                  stdErr,
                  exitCode,
                  rejection: rejection || reason,
               });
            },
            kill(reason: Error) {
               if (spawned.killed) {
                  return;
               }

               rejection = reason;
               spawned.kill('SIGINT');
            },
         });
      });
   }

   private _beforeSpawn<R>(task: SimpleGitTask<R>, args: string[]) {
      let rejection: Maybe<Error>;
      this._plugins.exec('spawn.before', undefined, {
         ...pluginContext(task, args),
         kill(reason) {
            rejection = reason || rejection;
         },
      });

      return rejection;
   }
}

function pluginContext<R>(task: SimpleGitTask<R>, commands: string[]) {
   return {
      method: first(task.commands) || '',
      commands,
   };
}

function onErrorReceived(target: Buffer[], logger: OutputLogger) {
   return (err: Error) => {
      logger(`[ERROR] child process exception %o`, err);
      target.push(Buffer.from(String(err.stack), 'ascii'));
   };
}

function onDataReceived(
   target: Buffer[],
   name: string,
   logger: OutputLogger,
   output: OutputLogger
) {
   return (buffer: Buffer) => {
      logger(`%s received %L bytes`, name, buffer);
      output(`%B`, buffer);
      target.push(buffer);
   };
}

```

### simple-git/src/lib/types/index.ts
```
import type { SpawnOptions } from 'child_process';

import type { SimpleGitTask } from './tasks';
import type { SimpleGitProgressEvent } from './handlers';

export * from './handlers';
export * from './tasks';

/**
 * Most tasks accept custom options as an array of strings as well as the
 * options object. Unless the task is explicitly documented as such, the
 * tasks will not accept both formats at the same time, preferring whichever
 * appears last in the arguments.
 */
export type TaskOptions<O extends Options = Options> = string[] | O;

/**
 * Options supplied in most tasks as an optional trailing object
 */
export type OptionsValues = null | string | number | (string | number)[];
export type Options = Record<string, OptionsValues>;

export type OptionFlags<FLAGS extends string, VALUE = null> = Partial<Record<FLAGS, VALUE>>;

/**
 * A function called by the executor immediately after creating a child
 * process. Allows the calling application to implement custom handling of
 * the incoming stream of data from the `git`.
 */
export type outputHandler = (
   command: string,
   stdout: NodeJS.ReadableStream,
   stderr: NodeJS.ReadableStream,
   args: string[]
) => void;

/**
 * Environment variables to be passed into the child process.
 */
export type GitExecutorEnv = NodeJS.ProcessEnv | undefined;

/**
 * Public interface of the Executor
 */
export interface SimpleGitExecutor {
   env: GitExecutorEnv;
   outputHandler?: outputHandler;
   cwd: string;

   chain(): SimpleGitExecutor;

   push<R>(task: SimpleGitTask<R>): Promise<R>;
}

/**
 * The resulting output from running the git child process
 */
export interface GitExecutorResult {
   stdOut: Buffer[];
   stdErr: Buffer[];
   exitCode: number;
   rejection: Maybe<Error>;
}

export interface SimpleGitPluginConfig {
   abort: AbortSignal;

   /**
    * Name of the binary the child processes will spawn - defaults to `git`,
    * supply as a tuple to enable the use of platforms that require `git` to be
    * called through an alternative binary (eg: `wsl git ...`).
    * Note: commands supplied in this way support a restricted set of characters
    * and should not be used as a way to supply arbitrary config arguments etc.
    */
   binary: string | [string] | [string, string];

   /**
    * Configures the events that should be used to determine when the unederlying child process has
    * been terminated.
    *
    * Version 2 will default to use `onClose=true, onExit=50` to mean the `close` event will be
    * used to immediately treat the child process as closed and start using the data from `stdOut`
    * / `stdErr`, whereas the `exit` event will wait `50ms` before treating the child process
    * as closed.
    *
    * This will be changed in version 3 to use `onClose=true, onExit=false` so that only the
    * close event is used to determine the termination of the process.
    */
   completion: {
      onClose?: boolean | number;
      onExit?: boolean | number;
   };

   /**
    * Configures the content of errors thrown by the `simple-git` instance for each task
    */
   errors(
      error: Buffer | Error | undefined,
      result: Omit<GitExecutorResult, 'rejection'>
   ): Buffer | Error | undefined;

   /**
    * Handler to be called with progress events emitted through the progress plugin
    */
   progress(data: SimpleGitProgressEvent): void;

   /**
    * Configuration for the `timeoutPlugin`
    */
   timeout: {
      /**
       * The number of milliseconds to wait after spawning the process / receiving
       * content on the stdOut/stdErr streams before forcibly closing the git process.
       */
      block: number;

      /**
       * Reset timeout plugin after receiving data on `stdErr` - set to `false` to ignore
       * `stdErr` content when determining whether to kill the process (defaults to `true`).
       */
      stdErr?: boolean;

      /**
       * Reset timeout plugin after receiving data on `stdOut` - set to `false` to ignore
       * `stdOut` content when determining whether to kill the process (defaults to `true`).
       */
      stdOut?: boolean;
   };

   spawnOptions: Pick<SpawnOptions, 'uid' | 'gid'>;

   unsafe: {
      /**
       * Allows potentially unsafe values to be supplied in the `binary` configuration option and
       * `git.customBinary()` method call.
       */
      allowUnsafeCustomBinary?: boolean;

      /**
       * By default, `simple-git` prevents the use of inline configuration
       * options to override the protocols available for the `git` child
       * process to prevent accidental security vulnerabilities when
       * unsanitised user data is passed directly into operations such as
       * `git.addRemote`, `git.clone` or `git.raw`.
       *
       * Enable this override to use the `ext::` protocol (see examples on
       * [git-scm.com](https://git-scm.com/docs/git-remote-ext#_examples)).
       */
      allowUnsafeProtocolOverride?: boolean;

      /**
       * Given the possibility of using `--upload-pack` and `--receive-pack` as
       * attack vectors, the use of these in any command (or the shorthand
       * `-u` option in a `clone` operation) are blocked by default.
       *
       * Enable this override to permit the use of these arguments.
       */
      allowUnsafePack?: boolean;

      /**
       * Using a `-c` switch to enable custom SSH commands opens up a potential
       * attack vector for running arbitrary commands.
       */
      allowUnsafeSshCommand?: boolean;

      /**
       * Using a `-c` switch to enable custom proxy command for the `git://` transport
       * exposes and attack vector for running arbitrary commands.
       */
      allowUnsafeGitProxy?: boolean;

      /**
       * Using a `-c` switch to enable custom hooks path commands to be run automatically
       * exposes and attack vector for running arbitrary commands.
       */
      allowUnsafeHooksPath?: boolean;

      /**
       * Using a `-c` switch to enable setting binary for processing diffs
       * exposes and attack vector for running arbitrary commands.
       */
      allowUnsafeDiffExternal?: boolean;

      /**
       * Using a `-c` switch to enable setting the binary to which `git` will delegate
       * file content change detection.
       */
      allowUnsafeFsMonitor?: boolean;
   };
}

/**
 * Optional configuration settings to be passed to the `simpleGit`
 * builder.
 */
export interface SimpleGitOptions extends Partial<SimpleGitPluginConfig> {
   /**
    * Base directory for all tasks run through this `simple-git` instance
    */
   baseDir: string;
   /**
    * Limit for the number of child processes that will be spawned concurrently from a `simple-git` instance
    */
   maxConcurrentProcesses: number;
   /**
    * Per-command configuration parameters to be passed with the `-c` switch to `git`
    */
   config: string[];
   /**
    * Enable trimming of trailing white-space in `git.raw`
    */
   trimmed: boolean;
}

export type Maybe<T> = T | undefined;
export type MaybeArray<T> = T | T[];

export type Primitives = string | number | boolean;

```
Callers & Entry Points (How public input reaches the modified code)
### packages/argv-parser/src/parse-argv.ts
```
import { collectConfigAccess } from './config/analyse-config';
import type { Flag } from './flags/flags.helpers';
import { parseGlobalFlags } from './flags/parse-global-flags';
import { parseTaskFlags } from './flags/parse-task-flags';
import type { ParsedArgv, ParsedFlag } from './parse-argv.types';
import { vulnerabilityAnalysis } from './vulnerabilities/vulnerability-analysis';

/**
 * Parse the tokens that would be forwarded to a `git` child-process and
 * return a structured summary of what the invocation does.
 */
export function parseArgv(...tokens: readonly unknown[]): ParsedArgv {
   const { flags, taskIndex } = parseGlobalFlags(tokens);

   const task = taskIndex < tokens.length ? String(tokens[taskIndex]).toLowerCase() : null;
   const taskTokens = task !== null ? tokens.slice(taskIndex + 1) : [];

   const { positionals, pathspecs } = parseTaskFlags(taskTokens, task, flags);
   const config = collectConfigAccess(task, flags, positionals);

   return {
      task,
      flags: flags.map(toParsedFlag),
      paths: pathspecs,
      config,
      vulnerabilities: vulnerabilityAnalysis(task, flags, config),
   };
}

function toParsedFlag({ value, name }: Flag): ParsedFlag {
   return value !== undefined ? { name, value } : { name };
}

```

### simple-git/src/lib/plugins/error-detection.plugin.ts
```
import { GitError } from '../errors/git-error';
import { GitExecutorResult, SimpleGitPluginConfig } from '../types';
import { SimpleGitPlugin } from './simple-git-plugin';

type TaskResult = Omit<GitExecutorResult, 'rejection'>;

function isTaskError(result: TaskResult) {
   return !!(result.exitCode && result.stdErr.length);
}

function getErrorMessage(result: TaskResult) {
   return Buffer.concat([...result.stdOut, ...result.stdErr]);
}

export function errorDetectionHandler(
   overwrite = false,
   isError = isTaskError,
   errorMessage: (result: TaskResult) => Buffer | Error = getErrorMessage
) {
   return (error: Buffer | Error | undefined, result: TaskResult) => {
      if ((!overwrite && error) || !isError(result)) {
         return error;
      }

      return errorMessage(result);
   };
}

export function errorDetectionPlugin(
   config: SimpleGitPluginConfig['errors']
): SimpleGitPlugin<'task.error'> {
   return {
      type: 'task.error',
      action(data, context) {
         const error = config(data.error, {
            stdErr: context.stdErr,
            stdOut: context.stdOut,
            exitCode: context.exitCode,
         });

         if (Buffer.isBuffer(error)) {
            return { error: new GitError(undefined, error.toString('utf-8')) };
         }

         return {
            error,
         };
      },
   };
}

```

### simple-git/src/lib/plugins/plugin-store.ts
```
import { EventEmitter } from 'node:events';

import type {
   SimpleGitPlugin,
   SimpleGitPluginType,
   SimpleGitPluginTypes,
} from './simple-git-plugin';
import { append, asArray } from '../utils';
import type { SimpleGitPluginConfig } from '../types';

export class PluginStore {
   private plugins: Set<SimpleGitPlugin<SimpleGitPluginType>> = new Set();
   private events = new EventEmitter();

   on<K extends keyof SimpleGitPluginConfig>(
      type: K,
      listener: (data: SimpleGitPluginConfig[K]) => void
   ) {
      this.events.on(type, listener);
   }

   reconfigure<K extends keyof SimpleGitPluginConfig>(type: K, data: SimpleGitPluginConfig[K]) {
      this.events.emit(type, data);
   }

   public append<T extends SimpleGitPluginType>(type: T, action: SimpleGitPlugin<T>['action']) {
      const plugin = append(this.plugins, { type, action });

      return () => this.plugins.delete(plugin);
   }

   public add<T extends SimpleGitPluginType>(
      plugin: void | SimpleGitPlugin<T> | SimpleGitPlugin<T>[]
   ) {
      const plugins: SimpleGitPlugin<T>[] = [];

      asArray(plugin).forEach((plugin) => plugin && this.plugins.add(append(plugins, plugin)));

      return () => {
         plugins.forEach((plugin) => this.plugins.delete(plugin));
      };
   }

   public exec<T extends SimpleGitPluginType>(
      type: T,
      data: SimpleGitPluginTypes[T]['data'],
      context: SimpleGitPluginTypes[T]['context']
   ): typeof data {
      let output = data;
      const contextual = Object.freeze(Object.create(context));

      for (const plugin of this.plugins) {
         if (plugin.type === type) {
            output = plugin.action(output, contextual);
         }
      }

      return output;
   }
}

```

### simple-git/src/lib/plugins/completion-detection.plugin.ts
```
import { deferred, DeferredPromise } from '@kwsites/promise-deferred';
import { SimpleGitPluginConfig } from '../types';
import { delay } from '../utils';
import { SimpleGitPlugin } from './simple-git-plugin';

const never = deferred().promise;

export function completionDetectionPlugin({
   onClose = true,
   onExit = 50,
}: SimpleGitPluginConfig['completion'] = {}): SimpleGitPlugin<'spawn.after'> {
   function createEvents() {
      let exitCode = -1;
      const events = {
         close: deferred(),
         closeTimeout: deferred(),
         exit: deferred(),
         exitTimeout: deferred(),
      };

      const result = Promise.race([
         onClose === false ? never : events.closeTimeout.promise,
         onExit === false ? never : events.exitTimeout.promise,
      ]);

      configureTimeout(onClose, events.close, events.closeTimeout);
      configureTimeout(onExit, events.exit, events.exitTimeout);

      return {
         close(code: number) {
            exitCode = code;
            events.close.done();
         },
         exit(code: number) {
            exitCode = code;
            events.exit.done();
         },
         get exitCode() {
            return exitCode;
         },
         result,
      };
   }

   function configureTimeout(
      flag: boolean | number,
      event: DeferredPromise<void>,
      timeout: DeferredPromise<void>
   ) {
      if (flag === false) {
         return;
      }

      (flag === true ? event.promise : event.promise.then(() => delay(flag))).then(timeout.done);
   }

   return {
      type: 'spawn.after',
      async action(_data, { spawned, close }) {
         const events = createEvents();

         let deferClose = true;
         let quickClose = () => void (deferClose = false);

         spawned.stdout?.on('data', quickClose);
         spawned.stderr?.on('data', quickClose);
         spawned.on('error', quickClose);

         spawned.on('close', (code: number) => events.close(code));
         spawned.on('exit', (code: number) => events.exit(code));

         try {
            await events.result;
            if (deferClose) {
               await delay(50);
            }
            close(events.exitCode);
         } catch (err) {
            close(events.exitCode, err as Error);
         }
      },
   };
}

```

### simple-git/src/lib/plugins/index.ts
```
export * from './abort-plugin';
export { blockUnsafeOperationsPlugin } from './block-unsafe-operations-plugin';
export * from './command-config-prefixing-plugin';
export * from './completion-detection.plugin';
export * from './custom-binary.plugin';
export * from './error-detection.plugin';
export * from './plugin-store';
export * from './progress-monitor-plugin';
export * from './simple-git-plugin';
export * from './spawn-options-plugin';
export * from './timout-plugin';

```

### simple-git/src/lib/runners/git-executor.ts
```
import type { PluginStore } from '../plugins';
import type { GitExecutorEnv, outputHandler, SimpleGitExecutor, SimpleGitTask } from '../types';

import { GitExecutorChain } from './git-executor-chain';
import { Scheduler } from './scheduler';

export class GitExecutor implements SimpleGitExecutor {
   private _chain = new GitExecutorChain(this, this._scheduler, this._plugins);

   public env: GitExecutorEnv;
   public outputHandler?: outputHandler;

   constructor(
      public cwd: string,
      private _scheduler: Scheduler,
      private _plugins: PluginStore
   ) {}

   chain(): SimpleGitExecutor {
      return new GitExecutorChain(this, this._scheduler, this._plugins);
   }

   push<R>(task: SimpleGitTask<R>): Promise<R> {
      return this._chain.push(task);
   }
}

```

### simple-git/src/lib/plugins/abort-plugin.ts
```
import { SimpleGitOptions } from '../types';
import { SimpleGitPlugin } from './simple-git-plugin';
import { GitPluginError } from '../errors/git-plugin-error';

export function abortPlugin(signal: SimpleGitOptions['abort']) {
   if (!signal) {
      return;
   }

   const onSpawnAfter: SimpleGitPlugin<'spawn.after'> = {
      type: 'spawn.after',
      action(_data, context) {
         function kill() {
            context.kill(new GitPluginError(undefined, 'abort', 'Abort signal received'));
         }

         signal.addEventListener('abort', kill);

         context.spawned.on('close', () => signal.removeEventListener('abort', kill));
      },
   };

   const onSpawnBefore: SimpleGitPlugin<'spawn.before'> = {
      type: 'spawn.before',
      action(_data, context) {
         if (signal.aborted) {
            context.kill(new GitPluginError(undefined, 'abort', 'Abort already signaled'));
         }
      },
   };

   return [onSpawnBefore, onSpawnAfter];
}

```

### simple-git/src/lib/plugins/timout-plugin.ts
```
import type { SimpleGitPlugin } from './simple-git-plugin';

import type { SimpleGitOptions } from '../types';
import { GitPluginError } from '../errors/git-plugin-error';

export function timeoutPlugin({
   block,
   stdErr = true,
   stdOut = true,
}: Exclude<SimpleGitOptions['timeout'], undefined>): SimpleGitPlugin<'spawn.after'> | void {
   if (block > 0) {
      return {
         type: 'spawn.after',
         action(_data, context) {
            let timeout: NodeJS.Timeout;

            function wait() {
               timeout && clearTimeout(timeout);
               timeout = setTimeout(kill, block);
            }

            function stop() {
               context.spawned.stdout?.off('data', wait);
               context.spawned.stderr?.off('data', wait);
               context.spawned.off('exit', stop);
               context.spawned.off('close', stop);
               timeout && clearTimeout(timeout);
            }

            function kill() {
               stop();
               context.kill(new GitPluginError(undefined, 'timeout', `block timeout reached`));
            }

            stdOut && context.spawned.stdout?.on('data', wait);
            stdErr && context.spawned.stderr?.on('data', wait);
            context.spawned.on('exit', stop);
            context.spawned.on('close', stop);

            wait();
         },
      };
   }
}

```

### simple-git/src/lib/plugins/progress-monitor-plugin.ts
```
import { SimpleGitOptions } from '../types';
import { asNumber, including } from '../utils';

import { SimpleGitPlugin } from './simple-git-plugin';

export function progressMonitorPlugin(progress: Exclude<SimpleGitOptions['progress'], void>) {
   const progressCommand = '--progress';
   const progressMethods = ['checkout', 'clone', 'fetch', 'pull', 'push'];

   const onProgress: SimpleGitPlugin<'spawn.after'> = {
      type: 'spawn.after',
      action(_data, context) {
         if (!context.commands.includes(progressCommand)) {
            return;
         }

         context.spawned.stderr?.on('data', (chunk: Buffer) => {
            const message = /^([\s\S]+?):\s*(\d+)% \((\d+)\/(\d+)\)/.exec(chunk.toString('utf8'));
            if (!message) {
               return;
            }

            progress({
               method: context.method,
               stage: progressEventStage(message[1]),
               progress: asNumber(message[2]),
               processed: asNumber(message[3]),
               total: asNumber(message[4]),
            });
         });
      },
   };

   const onArgs: SimpleGitPlugin<'spawn.args'> = {
      type: 'spawn.args',
      action(args, context) {
         if (!progressMethods.includes(context.method)) {
            return args;
         }

         return including(args, progressCommand);
      },
   };

   return [onArgs, onProgress];
}

function progressEventStage(input: string) {
   return String(input.toLowerCase().split(' ', 1)) || 'unknown';
}

```

### packages/argv-parser/src/parse-argv.types.ts
```
import type { ParsedVulnerabilities } from './vulnerabilities/vulnerability.types';

/** Where a config value originates / which scope it targets. */
export type ConfigScope =
   | 'inline' // runtime override via -c key=value (no file written)
   | 'env' // runtime override via --config-env=key=VAR
   | 'local' // .git/config (git's default when no scope flag is given)
   | 'global' // ~/.gitconfig
   | 'system' // /etc/gitconfig
   | 'worktree' // .git/config.worktree
   | 'file'; // explicit path via --file / -f

/** A single flag or option found in the token list. */
export interface ParsedFlag {
   /** Canonical name: e.g. `'-m'`, `'--amend'`, `'--no-verify'`. */
   name: string;
   /** Value consumed by this flag, when applicable. */
   value?: string;
}

/** A config key that this invocation reads via `git config`. */
export interface ConfigRead {
   /** Lower-cased dotted key, e.g. `'user.name'`. */
   key: string;
   scope: ConfigScope;
}

/** A config key that this invocation writes. */
export interface ConfigWrite extends ConfigRead {
   /**
    * The value being written.
    * Absent for delete-style operations (`--unset`, `--remove-section`).
    * For `scope: 'env'` this is the environment-variable *name*, not the
    * resolved config value.
    */
   value?: string;
}

export interface ParsedConfigActivity {
   /** Config keys read by a `git config` read operation. */
   read: ConfigRead[];
   /** Config keys written by this invocation (inline overrides and `git config` writes). */
   write: ConfigWrite[];
}

/**
 * Fully parsed representation of a set of varargs to be passed into the `git` child process.
 */
export interface ParsedArgv {
   /**
    * The git sub-command, e.g. `'commit'`, `'push'`.
    * `null` when the list contains only global flags (`['--version']`, `[]`).
    */
   task: string | null;

   /**
    * Every flag and option in the tokens (global + command-level), with
    * combined short clusters expanded: `-uc` → `[{name:'-u'}, {name:'-c'}]`.
    */
   flags: ParsedFlag[];

   /**
    * File-system paths: tokens after `--`, or `pathspec()` wrapper objects.
    * */
   paths: string[];

   /**
    * Activities being requested for the `git` config
    */
   config: ParsedConfigActivity;

   /**
    * Attack vectors discovered in the arguments
    */
   vulnerabilities: ParsedVulnerabilities;
}

```

### simple-git/src/lib/plugins/command-config-prefixing-plugin.ts
```
import { prefixedArray } from '../utils';
import { SimpleGitPlugin } from './simple-git-plugin';

export function commandConfigPrefixingPlugin(
   configuration: string[]
): SimpleGitPlugin<'spawn.args'> {
   const prefix = prefixedArray(configuration, '-c');

   return {
      type: 'spawn.args',
      action(data) {
         return [...prefix, ...data];
      },
   };
}

```

### simple-git/src/lib/plugins/spawn-options-plugin.ts
```
import { SpawnOptions } from 'child_process';
import { pick } from '../utils';
import { SimpleGitPlugin } from './simple-git-plugin';

export function spawnOptionsPlugin(
   spawnOptions: Partial<SpawnOptions>
): SimpleGitPlugin<'spawn.options'> {
   const options = pick(spawnOptions, ['uid', 'gid']);

   return {
      type: 'spawn.options',
      action(data) {
         return { ...options, ...data };
      },
   };
}

```

### simple-git/src/lib/plugins/suffix-paths.plugin.ts
```
import { SimpleGitPlugin } from './simple-git-plugin';
import { isPathSpec, toPaths } from '@simple-git/args-pathspec';

export function suffixPathsPlugin(): SimpleGitPlugin<'spawn.args'> {
   return {
      type: 'spawn.args',
      action(data) {
         const prefix: string[] = [];
         let suffix: undefined | string[];
         function append(args: string[]) {
            (suffix = suffix || []).push(...args);
         }

         for (let i = 0; i < data.length; i++) {
            const param = data[i];

            if (isPathSpec(param)) {
               append(toPaths(param));
               continue;
            }

            if (param === '--') {
               append(
                  data.slice(i + 1).flatMap((item) => (isPathSpec(item) && toPaths(item)) || item)
               );
               break;
            }

            prefix.push(param);
         }

         return !suffix ? prefix : [...prefix, '--', ...suffix.map(String)];
      },
   };
}

```

### simple-git/src/lib/tasks/check-is-repo.ts
```
import { ExitCodes } from '../utils';
import { Maybe, StringTask } from '../types';

export enum CheckRepoActions {
   BARE = 'bare',
   IN_TREE = 'tree',
   IS_REPO_ROOT = 'root',
}

const onError: StringTask<boolean>['onError'] = ({ exitCode }, error, done, fail) => {
   if (exitCode === ExitCodes.UNCLEAN && isNotRepoMessage(error)) {
      return done(Buffer.from('false'));
   }

   fail(error);
};

const parser: StringTask<boolean>['parser'] = (text) => {
   return text.trim() === 'true';
};

export function checkIsRepoTask(action: Maybe<CheckRepoActions>): StringTask<boolean> {
   switch (action) {
      case CheckRepoActions.BARE:
         return checkIsBareRepoTask();
      case CheckRepoActions.IS_REPO_ROOT:
         return checkIsRepoRootTask();
   }

   const commands = ['rev-parse', '--is-inside-work-tree'];

   return {
      commands,
      format: 'utf-8',
      onError,
      parser,
   };
}

export function checkIsRepoRootTask(): StringTask<boolean> {
   const commands = ['rev-parse', '--git-dir'];

   return {
      commands,
      format: 'utf-8',
      onError,
      parser(path) {
         return /^\.(git)?$/.test(path.trim());
      },
   };
}

export function checkIsBareRepoTask(): StringTask<boolean> {
   const commands = ['rev-parse', '--is-bare-repository'];

   return {
      commands,
      format: 'utf-8',
      onError,
      parser,
   };
}

function isNotRepoMessage(error: Error): boolean {
   return /(Not a git repository|Kein Git-Repository)/i.test(String(error));
}

```

### packages/argv-parser/src/flags/parse-task-flags.ts
```
import { isPathSpec, toPaths } from '@simple-git/args-pathspec';

import { getFlagSpecForTask } from '../tokens/flag-specs';
import { expandToken } from '../tokens/token-expander';
import type { Flag } from './flags.helpers';

type TaskFlags = {
   flags: Flag[];
   positionals: string[];
   pathspecs: string[];
};

export function parseTaskFlags(
   tokens: readonly unknown[],
   task: string | null,
   flags: Flag[] = []
): TaskFlags {
   const spec = getFlagSpecForTask(task);
   const positionals: string[] = [];
   const pathspecs: string[] = [];

   let i = 0;
   while (i < tokens.length) {
      const current = tokens[i];

      if (isPathSpec(current)) {
         pathspecs.push(...toPaths(current as string));
         i++;
         continue;
      }

      const raw = String(current);

      if (raw === '--') {
         for (let j = i + 1; j < tokens.length; j++) {
            const t = tokens[j];
            isPathSpec(t) ? pathspecs.push(...toPaths(t as string)) : pathspecs.push(String(t));
         }
         break;
      }

      if (!raw.startsWith('-') || raw.length < 2) {
         positionals.push(raw);
         i++;
         continue;
      }

      const parsed = expandToken(raw, spec);
      let next = i + 1;

      for (const token of parsed) {
         const flag: Flag = {
            name: token.name,
            value: token.value,
            absorbedNext: false,
            isGlobal: false,
         };
         if (
            token.needsNext &&
            flag.value === undefined &&
            next < tokens.length &&
            !isPathSpec(tokens[next])
         ) {
            flag.value = String(tokens[next]);
            flag.absorbedNext = true;
            next++;
         }
         flags.push(flag);
      }

      i = next;
   }

   return { flags, positionals, pathspecs };
}

```

### packages/argv-parser/src/tokens/token-expander.ts
```
import { GLOBAL } from './flag-specs';

/** Parse a single raw token (e.g. `'-m'`, `'--amend'`, `'-uc'`) into one or
 *  more switch descriptors.  Values are not yet resolved for needsNext=true. */
export function expandToken(
   raw: string,
   spec = GLOBAL
): Array<{
   name: string;
   value?: string;
   needsNext: boolean;
}> {
   if (raw.startsWith('--')) {
      const eq = raw.indexOf('=');
      if (eq > 2) {
         return [{ name: raw.slice(0, eq), value: raw.slice(eq + 1), needsNext: false }];
      }
      const stem = raw.slice(2);
      return [{ name: raw, needsNext: spec.long.has(stem) }];
   }

   // Single short switch
   if (raw.length === 2) {
      const char = raw.charAt(1);
      const consumes = spec.short.get(char);
      return [{ name: raw, needsNext: consumes === true }];
   }

   // Combined short cluster: try to expand char-by-char
   return expandCluster(raw, spec.short);
}

function expandCluster(
   raw: string,
   shortSpec: ReadonlyMap<string, boolean>
): Array<{ name: string; value?: string; needsNext: boolean }> {
   const chars = raw.slice(1).split('');
   const result: Array<{ name: string; value?: string; needsNext: boolean }> = [];

   for (let i = 0; i < chars.length; i++) {
      const char = chars[i];
      const consumes = shortSpec.get(char);

      if (consumes === undefined) {
         // Unknown char: keep the whole raw token as opaque
         return [{ name: raw, needsNext: false }];
      }

      if (consumes) {
         const remainder = chars.slice(i + 1).join('');
         if (remainder) {
            const remainderAllKnown = [...remainder].every((c) => shortSpec.has(c));
            if (!remainderAllKnown) {
               // Remaining chars are the embedded value, not separate flags
               result.push({ name: `-${char}`, value: remainder, needsNext: false });
               return result;
            }
         }
      }

      result.push({ name: `-${char}`, needsNext: consumes });
   }

   return result;
}

```

### simple-git/src/lib/parsers/parse-pull.ts
```
import { PullDetail, PullFailedResult, PullResult, RemoteMessages } from '../../../typings';
import { PullFailedSummary, PullSummary } from '../responses/PullSummary';
import { TaskParser } from '../types';
import { append, LineParser, parseStringResponse } from '../utils';
import { parseRemoteMessages } from './parse-remote-messages';

const FILE_UPDATE_REGEX = /^\s*(.+?)\s+\|\s+\d+\s*(\+*)(-*)/;
const SUMMARY_REGEX = /(\d+)\D+((\d+)\D+\(\+\))?(\D+(\d+)\D+\(-\))?/;
const ACTION_REGEX = /^(create|delete) mode \d+ (.+)/;

const parsers: LineParser<PullResult>[] = [
   new LineParser(FILE_UPDATE_REGEX, (result, [file, insertions, deletions]) => {
      result.files.push(file);

      if (insertions) {
         result.insertions[file] = insertions.length;
      }

      if (deletions) {
         result.deletions[file] = deletions.length;
      }
   }),
   new LineParser(SUMMARY_REGEX, (result, [changes, , insertions, , deletions]) => {
      if (insertions !== undefined || deletions !== undefined) {
         result.summary.changes = +changes || 0;
         result.summary.insertions = +insertions || 0;
         result.summary.deletions = +deletions || 0;
         return true;
      }
      return false;
   }),
   new LineParser(ACTION_REGEX, (result, [action, file]) => {
      append(result.files, file);
      append(action === 'create' ? result.created : result.deleted, file);
   }),
];

const errorParsers: LineParser<PullFailedResult>[] = [
   new LineParser(/^from\s(.+)$/i, (result, [remote]) => void (result.remote = remote)),
   new LineParser(/^fatal:\s(.+)$/, (result, [message]) => void (result.message = message)),
   new LineParser(
      /([a-z0-9]+)\.\.([a-z0-9]+)\s+(\S+)\s+->\s+(\S+)$/,
      (result, [hashLocal, hashRemote, branchLocal, branchRemote]) => {
         result.branch.local = branchLocal;
         result.hash.local = hashLocal;
         result.branch.remote = branchRemote;
         result.hash.remote = hashRemote;
      }
   ),
];

export const parsePullDetail: TaskParser<string, PullDetail> = (stdOut, stdErr) => {
   return parseStringResponse(new PullSummary(), parsers, [stdOut, stdErr]);
};

export const parsePullResult: TaskParser<string, PullResult> = (stdOut, stdErr) => {
   return Object.assign(
      new PullSummary(),
      parsePullDetail(stdOut, stdErr),
      parseRemoteMessages<RemoteMessages>(stdOut, stdErr)
   );
};

export function parsePullErrorResult(stdOut: string, stdErr: string) {
   const pullError = parseStringResponse(new PullFailedSummary(), errorParsers, [stdOut, stdErr]);

   return pullError.message && pullError;
}

```

### simple-git/typings/simple-git.d.ts
```
import * as resp from './response';
import * as types from './types';
import { GitError } from './errors';

export interface SimpleGitFactory {
   (baseDir?: string, options?: Partial<types.SimpleGitOptions>): SimpleGit;

   (baseDir: string): SimpleGit;

   (options: Partial<types.SimpleGitOptions>): SimpleGit;
}

export type Response<T> = SimpleGit & Promise<T>;

export interface SimpleGitBase {
   /**
    * Adds one or more files to source control
    */
   add(files: string | string[], callback?: types.SimpleGitTaskCallback<string>): Response<string>;

   /**
    * Sets the working directory of the subsequent commands.
    */
   cwd(
      directory: { path: string; root?: boolean },
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   cwd<path extends string>(
      directory: path,
      callback?: types.SimpleGitTaskCallback<path>
   ): Response<path>;

   /**
    * Compute object ID from a file
    */
   hashObject(path: string, callback?: types.SimpleGitTaskCallback): Response<string>;

   hashObject(
      path: string,
      write?: boolean,
      callback?: types.SimpleGitTaskCallback
   ): Response<string>;

   /**
    * Initialize a git repo
    */
   init(
      bare: boolean,
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<resp.InitResult>
   ): Response<resp.InitResult>;

   init(
      bare: boolean,
      callback?: types.SimpleGitTaskCallback<resp.InitResult>
   ): Response<resp.InitResult>;

   init(
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<resp.InitResult>
   ): Response<resp.InitResult>;

   init(callback?: types.SimpleGitTaskCallback<resp.InitResult>): Response<resp.InitResult>;

   /**
    * Runs a merge, `options` can be either an array of arguments
    * supported by the [`git merge`](https://git-scm.com/docs/git-merge)
    * or an options object.
    *
    * Conflicts during the merge result in an error response,
    * the response type whether it was an error or success will be a MergeSummary instance.
    * When successful, the MergeSummary has all detail from a the PullSummary
    *
    * @see https://github.com/steveukx/git-js/blob/master/src/responses/MergeSummary.js
    * @see https://github.com/steveukx/git-js/blob/master/src/responses/PullSummary.js
    */
   merge(
      options: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<resp.MergeResult>
   ): Response<resp.MergeResult>;

   /**
    * Merges from one branch to another, equivalent to running `git merge ${remote} ${branch}`, the `options` argument can
    * either be an array of additional parameters to pass to the command or null / omitted to be ignored.
    */
   mergeFromTo<E extends GitError>(
      remote: string,
      branch: string,
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<resp.MergeResult, E>
   ): Response<resp.MergeResult>;

   mergeFromTo<E extends GitError>(
      remote: string,
      branch: string,
      callback?: types.SimpleGitTaskCallback<resp.MergeResult, E>
   ): Response<resp.MergeResult>;

   /**
    * Sets a handler function to be called whenever a new child process is created, the handler function will be called
    * with the name of the command being run and the stdout & stderr streams used by the ChildProcess.
    *
    * @example
    * require('simple-git')
    *    .outputHandler(function (command, stdout, stderr) {
    *       stdout.pipe(process.stdout);
    *    })
    *    .checkout('https://github.com/user/repo.git');
    *
    * @see https://nodejs.org/api/child_process.html#child_process_class_childprocess
    * @see https://nodejs.org/api/stream.html#stream_class_stream_readable
    */
   outputHandler(handler: types.outputHandler | void): this;

   /**
    * Pushes the current committed changes to a remote, optionally specify the names of the remote and branch to use
    * when pushing. Supply multiple options as an array of strings in the first argument - see examples below.
    */
   push(
      remote?: string,
      branch?: string,
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<resp.PushResult>
   ): Response<resp.PushResult>;

   push(
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<resp.PushResult>
   ): Response<resp.PushResult>;

   push(callback?: types.SimpleGitTaskCallback<resp.PushResult>): Response<resp.PushResult>;

   /**
    * Stash the local repo
    */
   stash(
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   stash(callback?: types.SimpleGitTaskCallback<string>): Response<string>;

   /**
    * Show the working tree status.
    */
   status(
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<resp.StatusResult>
   ): Response<resp.StatusResult>;

   status(callback?: types.SimpleGitTaskCallback<resp.StatusResult>): Response<resp.StatusResult>;
}

export interface SimpleGit extends SimpleGitBase {
   /**
    * Add an annotated tag to the head of the current branch
    */
   addAnnotatedTag(
      tagName: string,
      tagMessage: string,
      callback?: types.SimpleGitTaskCallback<{ name: string }>
   ): Response<{ name: string }>;

   /**
    * Add config to local git instance for the specified `key` (eg: user.name) and value (eg: 'your name').
    * Set `append` to true to append to rather than overwrite the key
    */
   addConfig(
      key: string,
      value: string,
      append?: boolean,
      scope?: keyof typeof types.GitConfigScope,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   addConfig(
      key: string,
      value: string,
      append?: boolean,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   addConfig(
      key: string,
      value: string,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   /**
    * Applies a patch to the repo
    */
   applyPatch(
      patches: string | string[],
      options: types.TaskOptions<types.ApplyOptions>,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   applyPatch(
      patches: string | string[],
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   /**
    * Configuration values visible to git in the current working directory
    */
   listConfig(
      scope: keyof typeof types.GitConfigScope,
      callback?: types.SimpleGitTaskCallback<resp.ConfigListSummary>
   ): Response<resp.ConfigListSummary>;

   listConfig(
      callback?: types.SimpleGitTaskCallback<resp.ConfigListSummary>
   ): Response<resp.ConfigListSummary>;

   /**
    * Adds a remote to the list of remotes.
    *
    * - `remoteName` Name of the repository - eg "upstream"
    * - `remoteRepo` Fully qualified SSH or HTTP(S) path to the remote repo
    * - `options` Optional additional settings permitted by the `git remote add` command, merged into the command prior to the repo name and remote url
    */
   addRemote(
      remoteName: string,
      remoteRepo: string,
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   addRemote(
      remoteName: string,
      remoteRepo: string,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   /**
    * Add a lightweight tag to the head of the current branch
    */
   addTag(
      name: string,
      callback?: types.SimpleGitTaskCallback<{ name: string }>
   ): Response<{ name: string }>;

   /**
    * Equivalent to `catFile` but will return the native `Buffer` of content from the git command's stdout.
    */
   binaryCatFile(options: string[], callback?: types.SimpleGitTaskCallback<any>): Response<any>;

   /**
    * List all branches
    */
   branch(
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<resp.BranchSummary>
   ): Response<resp.BranchSummary>;

   /**
    * List of local branches
    */
   branchLocal(
      callback?: types.SimpleGitTaskCallback<resp.BranchSummary>
   ): Response<resp.BranchSummary>;

   /**
    * Returns a list of objects in a tree based on commit hash.
    * Passing in an object hash returns the object's content, size, and type.
    *
    * Passing "-p" will instruct cat-file to determine the object type, and display its formatted contents.
    *
    * @see https://git-scm.com/docs/git-cat-file
    */
   catFile(options: string[], callback?: types.SimpleGitTaskCallback<string>): Response<string>;

   catFile(callback?: types.SimpleGitTaskCallback<string>): Response<string>;

   /**
    * Check if a pathname or pathnames are excluded by .gitignore
    *
    */
   checkIgnore(
      pathNames: string[],
      callback?: types.SimpleGitTaskCallback<string[]>
   ): Response<string[]>;

   checkIgnore(path: string, callback?: types.SimpleGitTaskCallback<string[]>): Response<string[]>;

   /**
    * Validates that the current working directory is a valid git repo file path.
    *
    * To make a more specific assertion of the repo, add the `action` argument:
    *
    * - `bare` to validate that the working directory is inside a bare repo.
    * - `root` to validate that the working directory is the root of a repo.
    * - `tree` (default value when omitted) to simply validate that the working
    *    directory is the descendent of a repo
    */
   checkIsRepo(
      action?: types.CheckRepoActions,
      callback?: types.SimpleGitTaskCallback<boolean>
   ): Response<boolean>;

   checkIsRepo(callback?: types.SimpleGitTaskCallback<boolean>): Response<boolean>;

   /**
    * Checkout a tag or revision, any number of additional arguments can be passed to the `git checkout` command
    * by supplying either a string or array of strings as the `what` parameter.
    */
   checkout(
      what: string,
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   checkout(what: string, callback?: types.SimpleGitTaskCallback<string>): Response<string>;

   checkout(
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<string>
   ): Response<string>;

   /**
    * Checkout a remote branch - equivalent to `git checkout -b ${branchName} ${startPoint}`
    *
    * - branchName name of branch.
    * - startPoint (e.g origin/development).
    */
   checkoutBranch(
      branchName: string,
      startPoint: string,
      callback?: types.SimpleGitTaskCallback<void>
   ): Response<void>;

   checkoutBranch(
      branchName: string,
      startPoint: string,
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<void>
   ): Response<void>;

   /**
    * Internally uses pull and tags to get the list of tags then checks out the latest tag.
    */
   checkoutLatestTag(
      branchName: string,
      startPoint: string,
      callback?: types.SimpleGitTaskCallback<void>
   ): Response<void>;

   /**
    * Checkout a local branch - equivalent to `git checkout -b ${branchName}`
    */
   checkoutLocalBranch(
      branchName: string,
      callback?: types.SimpleGitTaskCallback<void>
   ): Response<void>;

   checkoutLocalBranch(
      branchName: string,
      options?: types.TaskOptions,
      callback?: types.SimpleGitTaskCallback<void>
   ): Response<void>;

   /**
    * Deletes unwanted content from the local repo - when supplying the first argument as
    * an array of `CleanOptions`, the array must include one of `CleanOptions.FORCE` or
    * `CleanOptions.DRY_RUN`.
    *
    * eg:
    *
    * ```typescript
    await git.clean(CleanOptions.FORCE);
    await git.clean(CleanOptions.DRY_RUN + CleanOptions.RECURSIVE);
    await git.clean(CleanOptions.FORCE, ['./path']);
    await git.clean(CleanOptions.IGNORED + CleanOptions.FORCE, {'./path': null});
    * ```
    */
   clean(
      args: types.CleanOptions[],
      options?: types.TaskOptions,
      callback
... [truncated]
```

### simple-git/src/lib/tasks/check-ignore.ts
```
import { StringTask } from '../types';
import { parseCheckIgnore } from '../responses/CheckIgnore';

export function checkIgnoreTask(paths: string[]): StringTask<string[]> {
   return {
      commands: ['check-ignore', ...paths],
      format: 'utf-8',
      parser: parseCheckIgnore,
   };
}

```

### simple-git/typings/index.d.ts
```
import { SimpleGitFactory } from './simple-git';

export { pathspec } from '@simple-git/args-pathspec';

export * from './simple-git';
export * from './errors';
export * from './response';
export * from './types';

export declare const gitP: SimpleGitFactory;

export declare const simpleGit: SimpleGitFactory;

export default simpleGit;

```

### simple-git/src/lib/utils/git-output-streams.ts
```
import { TaskResponseFormat } from '../types';

export class GitOutputStreams<T extends TaskResponseFormat = Buffer> {
   constructor(
      public readonly stdOut: T,
      public readonly stdErr: T
   ) {}

   asStrings(): GitOutputStreams<string> {
      return new GitOutputStreams(this.stdOut.toString('utf8'), this.stdErr.toString('utf8'));
   }
}

```

### simple-git/src/lib/tasks/hash-object.ts
```
import { straightThroughStringTask } from './task';
import { StringTask } from '../types';

/**
 * Task used by `git.hashObject`
 */
export function hashObjectTask(filePath: string, write: boolean): StringTask<string> {
   const commands = ['hash-object', filePath];
   if (write) {
      commands.push('-w');
   }

   return straightThroughStringTask(commands, true);
}

```

### simple-git/src/lib/errors/git-plugin-error.ts
```
import { SimpleGitOptions, SimpleGitTask } from '../types';
import { GitError } from './git-error';

export class GitPluginError extends GitError {
   constructor(
      public task?: SimpleGitTask<any>,
      public readonly plugin?: keyof SimpleGitOptions,
      message?: string
   ) {
      super(task, message);
      Object.setPrototypeOf(this, new.target.prototype);
   }
}

```

### simple-git/src/lib/tasks/move.ts
```
import { MoveResult } from '../../../typings';
import { parseMoveResult } from '../parsers/parse-move';
import { StringTask } from '../types';
import { asArray } from '../utils';

export function moveTask(from: string | string[], to: string): StringTask<MoveResult> {
   return {
      commands: ['mv', '-v', ...asArray(from), to],
      format: 'utf-8',
      parser: parseMoveResult,
   };
}

```

### simple-git/src/lib/tasks/change-working-directory.ts
```
import { folderExists } from '../utils';
import { SimpleGitExecutor } from '../types';
import { adhocExecTask } from './task';

export function changeWorkingDirectoryTask(directory: string, root?: SimpleGitExecutor) {
   return adhocExecTask((instance: SimpleGitExecutor) => {
      if (!folderExists(directory)) {
         throw new Error(`Git.cwd: cannot change to non-directory "${directory}"`);
      }

      return ((root || instance).cwd = directory);
   });
}

```

### simple-git/src/lib/tasks/status.ts
```
import { StatusResult } from '../../../typings';
import { parseStatusSummary } from '../responses/StatusSummary';
import { StringTask } from '../types';

const ignoredOptions = ['--null', '-z'];

export function statusTask(customArgs: string[]): StringTask<StatusResult> {
   const commands = [
      'status',
      '--porcelain',
      '-b',
      '-u',
      '--null',
      ...customArgs.filter((arg) => !ignoredOptions.includes(arg)),
   ];

   return {
      format: 'utf-8',
      commands,
      parser(text: string) {
         return parseStatusSummary(text);
      },
   };
}

```

### simple-git/src/lib/utils/simple-git-options.ts
```
import { SimpleGitOptions } from '../types';

const defaultOptions: Omit<SimpleGitOptions, 'baseDir'> = {
   binary: 'git',
   maxConcurrentProcesses: 5,
   config: [],
   trimmed: false,
};

export function createInstanceConfig(
   ...options: Array<Partial<SimpleGitOptions> | undefined>
): SimpleGitOptions {
   const baseDir = process.cwd();
   const config: SimpleGitOptions = Object.assign(
      { baseDir, ...defaultOptions },
      ...options.filter((o) => typeof o === 'object' && o)
   );

   config.baseDir = config.baseDir || baseDir;
   config.trimmed = config.trimmed === true;

   return config;
}

```

### simple-git/src/lib/errors/git-construct-error.ts
```
import { GitError } from './git-error';
import { SimpleGitOptions } from '../types';

/**
 * The `GitConstructError` is thrown when an error occurs in the constructor
 * of the `simple-git` instance itself. Most commonly as a result of using
 * a `baseDir` option that points to a folder that either does not exist,
 * or cannot be read by the user the node script is running as.
 *
 * Check the `.message` property for more detail including the properties
 * passed to the constructor.
 */
export class GitConstructError extends GitError {
   constructor(
      public readonly config: SimpleGitOptions,
      message: string
   ) {
      super(undefined, message);
   }
}

```

### simple-git/src/lib/tasks/init.ts
```
import { InitResult } from '../../../typings';
import { parseInit } from '../responses/InitSummary';
import { StringTask } from '../types';

const bareCommand = '--bare';

function hasBareCommand(command: string[]) {
   return command.includes(bareCommand);
}

export function initTask(bare = false, path: string, customArgs: string[]): StringTask<InitResult> {
   const commands = ['init', ...customArgs];
   if (bare && !hasBareCommand(commands)) {
      commands.splice(1, 0, bareCommand);
   }

   return {
      commands,
      format: 'utf-8',
      parser(text: string): InitResult {
         return parseInit(commands.includes('--bare'), path, text);
      },
   };
}

```

### simple-git/src/lib/tasks/sub-module.ts
```
import { StringTask } from '../types';
import { straightThroughStringTask } from './task';

export function addSubModuleTask(repo: string, path: string): StringTask<string> {
   return subModuleTask(['add', repo, path]);
}

export function initSubModuleTask(customArgs: string[]): StringTask<string> {
   return subModuleTask(['init', ...customArgs]);
}

export function subModuleTask(customArgs: string[]): StringTask<string> {
   const commands = [...customArgs];
   if (commands[0] !== 'submodule') {
      commands.unshift('submodule');
   }

   return straightThroughStringTask(commands);
}

export function updateSubModuleTask(customArgs: string[]): StringTask<string> {
   return subModuleTask(['update', ...customArgs]);
}

```

### simple-git/src/lib/tasks/merge.ts
```
import { MergeResult } from '../../../typings';
import { GitResponseError } from '../errors/git-response-error';
import { parseMergeResult } from '../parsers/parse-merge';
import { StringTask } from '../types';
import { configurationErrorTask, EmptyTask } from './task';

export function mergeTask(customArgs: string[]): EmptyTask | StringTask<MergeResult> {
   if (!customArgs.length) {
      return configurationErrorTask('Git.merge requires at least one option');
   }

   return {
      commands: ['merge', ...customArgs],
      format: 'utf-8',
      parser(stdOut, stdErr): MergeResult {
         const merge = parseMergeResult(stdOut, stdErr);
         if (merge.failed) {
            throw new GitResponseError(merge);
         }

         return merge;
      },
   };
}

```

### simple-git/src/lib/tasks/fetch.ts
```
import { FetchResult } from '../../../typings';
import { parseFetchResult } from '../parsers/parse-fetch';
import { StringTask } from '../types';

import { configurationErrorTask, EmptyTask } from './task';

function disallowedCommand(command: string) {
   return /^--upload-pack(=|$)/.test(command);
}

export function fetchTask(
   remote: string,
   branch: string,
   customArgs: string[]
): StringTask<FetchResult> | EmptyTask {
   const commands = ['fetch', ...customArgs];
   if (remote && branch) {
      commands.push(remote, branch);
   }

   const banned = commands.find(disallowedCommand);
   if (banned) {
      return configurationErrorTask(`git.fetch: potential exploit argument blocked.`);
   }

   return {
      commands,
      format: 'utf-8',
      parser: parseFetchResult,
   };
}

```

### simple-git/src/lib/tasks/push.ts
```
import { PushResult } from '../../../typings';
import { parsePushResult as parser } from '../parsers/parse-push';
import { StringTask } from '../types';
import { append, remove } from '../utils';

type PushRef = { remote?: string; branch?: string };

export function pushTagsTask(ref: PushRef = {}, customArgs: string[]): StringTask<PushResult> {
   append(customArgs, '--tags');
   return pushTask(ref, customArgs);
}

export function pushTask(ref: PushRef = {}, customArgs: string[]): StringTask<PushResult> {
   const commands = ['push', ...customArgs];
   if (ref.branch) {
      commands.splice(1, 0, ref.branch);
   }
   if (ref.remote) {
      commands.splice(1, 0, ref.remote);
   }

   remove(commands, '-v');
   append(commands, '--verbose');
   append(commands, '--porcelain');

   return {
      commands,
      format: 'utf-8',
      parser,
   };
}

```

### simple-git/src/lib/tasks/stash-list.ts
```
import { LogOptions, LogResult } from '../../../typings';
import { logFormatFromCommand } from '../args/log-format';
import { createListLogSummaryParser } from '../parsers/parse-list-log-summary';
import type { StringTask } from '../types';
import { validateLogFormatConfig } from './diff';
import { parseLogOptions } from './log';
import type { EmptyTask } from './task';

export function stashListTask(
   opt: LogOptions = {},
   customArgs: string[]
): EmptyTask | StringTask<LogResult> {
   const options = parseLogOptions<any>(opt);
   const commands = ['stash', 'list', ...options.commands, ...customArgs];
   const parser = createListLogSummaryParser(
      options.splitter,
      options.fields,
      logFormatFromCommand(commands)
   );

   return (
      validateLogFormatConfig(commands) || {
         commands,
         format: 'utf-8',
         parser,
      }
   );
}

```

### simple-git/src/lib/utils/task-parser.ts
```
import type { MaybeArray, TaskParser, TaskResponseFormat } from '../types';
import { GitOutputStreams } from './git-output-streams';
import { LineParser } from './line-parser';
import { asArray, toLinesWithContent } from './util';

export function callTaskParser<INPUT extends TaskResponseFormat, RESPONSE>(
   parser: TaskParser<INPUT, RESPONSE>,
   streams: GitOutputStreams<INPUT>
) {
   return parser(streams.stdOut, streams.stdErr);
}

export function parseStringResponse<T>(
   result: T,
   parsers: LineParser<T>[],
   texts: MaybeArray<string>,
   trim = true
): T {
   asArray(texts).forEach((text) => {
      for (let lines = toLinesWithContent(text, trim), i = 0, max = lines.length; i < max; i++) {
         const line = (offset = 0) => {
            if (i + offset >= max) {
               return;
            }
            return lines[i + offset];
         };

         parsers.some(({ parse }) => parse(line, result));
      }
   });

   return result;
}

```

### simple-git/typings/types.d.ts
```
export type { RemoteWithoutRefs, RemoteWithRefs } from '../src/lib/responses/GetRemoteSummary';
export type { LogOptions, DefaultLogFields } from '../src/lib/tasks/log';

export type {
   outputHandler,
   Options,
   TaskOptions,
   SimpleGitOptions,
   SimpleGitProgressEvent,
   SimpleGitTaskCallback,
} from '../src/lib/types';

export type { ApplyOptions } from '../src/lib/tasks/apply-patch';
export { CheckRepoActions } from '../src/lib/tasks/check-is-repo';
export { CleanOptions, CleanMode } from '../src/lib/tasks/clean';
export type { CloneOptions } from '../src/lib/tasks/clone';
export { GitConfigScope } from '../src/lib/tasks/config';
export type { CountObjectsResult } from '../src/lib/tasks/count-objects';
export { DiffNameStatus } from '../src/lib/tasks/diff-name-status';
export { GitGrepQuery, grepQueryBuilder } from '../src/lib/tasks/grep';
export { ResetOptions, ResetMode } from '../src/lib/tasks/reset';
export type { VersionResult } from '../src/lib/tasks/version';

```

### simple-git/src/lib/tasks/pull.ts
```
import { PullResult } from '../../../typings';
import { GitResponseError } from '../errors/git-response-error';
import { parsePullErrorResult, parsePullResult } from '../parsers/parse-pull';
import { Maybe, StringTask } from '../types';
import { bufferToString } from '../utils';

export function pullTask(
   remote: Maybe<string>,
   branch: Maybe<string>,
   customArgs: string[]
): StringTask<PullResult> {
   const commands: string[] = ['pull', ...customArgs];
   if (remote && branch) {
      commands.splice(1, 0, remote, branch);
   }

   return {
      commands,
      format: 'utf-8',
      parser(stdOut, stdErr): PullResult {
         return parsePullResult(stdOut, stdErr);
      },
      onError(result, _error, _done, fail) {
         const pullError = parsePullErrorResult(
            bufferToString(result.stdOut),
            bufferToString(result.stdErr)
         );
         if (pullError) {
            return fail(new GitResponseError(pullError));
         }

         fail(_error);
      },
   };
}

```

### simple-git/src/lib/tasks/apply-patch.ts
```
import { straightThroughStringTask } from './task';
import { OptionFlags, Options, StringTask } from '../types';

export type ApplyOptions = Options &
   OptionFlags<
      | '--stat'
      | '--numstat'
      | '--summary'
      | '--check'
      | '--index'
      | '--intent-to-add'
      | '--3way'
      | '--apply'
      | '--no-add'
      | '-R'
      | '--reverse'
      | '--allow-binary-replacement'
      | '--binary'
      | '--reject'
      | '-z'
      | '--inaccurate-eof'
      | '--recount'
      | '--cached'
      | '--ignore-space-change'
      | '--ignore-whitespace'
      | '--verbose'
      | '--unsafe-paths'
   > &
   OptionFlags<'--whitespace', 'nowarn' | 'warn' | 'fix' | 'error' | 'error-all'> &
   OptionFlags<'--build-fake-ancestor' | '--exclude' | '--include' | '--directory', string> &
   OptionFlags<'-p' | '-C', number>;

export function applyPatchTask(patches: string[], customArgs: string[]): StringTask<string> {
   return straightThroughStringTask(['apply', ...customArgs, ...patches]);
}

```

### simple-git/src/lib/tasks/tag.ts
```
import { TagResult } from '../../../typings';
import { parseTagList } from '../responses/TagList';
import { StringTask } from '../types';

/**
 * Task used by `git.tags`
 */
export function tagListTask(customArgs: string[] = []): StringTask<TagResult> {
   const hasCustomSort = customArgs.some((option) => /^--sort=/.test(option));

   return {
      format: 'utf-8',
      commands: ['tag', '-l', ...customArgs],
      parser(text: string) {
         return parseTagList(text, hasCustomSort);
      },
   };
}

/**
 * Task used by `git.addTag`
 */
export function addTagTask(name: string): StringTask<{ name: string }> {
   return {
      format: 'utf-8',
      commands: ['tag', name],
      parser() {
         return { name };
      },
   };
}

/**
 * Task used by `git.addTag`
 */
export function addAnnotatedTagTask(
   name: string,
   tagMessage: string
): StringTask<{ name: string }> {
   return {
      format: 'utf-8',
      commands: ['tag', '-a', '-m', tagMessage, name],
      parser() {
         return { name };
      },
   };
}

```

### simple-git/src/lib/tasks/reset.ts
```
import type { Maybe, OptionFlags, Options } from '../types';
import { asStringArray } from '../utils';
import { straightThroughStringTask } from './task';

export enum ResetMode {
   MIXED = 'mixed',
   SOFT = 'soft',
   HARD = 'hard',
   MERGE = 'merge',
   KEEP = 'keep',
}

const validResetModes = asStringArray(Object.values(ResetMode));

export type ResetOptions = Options &
   OptionFlags<'-q' | '--quiet' | '--no-quiet' | '--pathspec-from-nul'> &
   OptionFlags<'--pathspec-from-file', string>;

export function resetTask(mode: Maybe<ResetMode>, customArgs: string[]) {
   const commands: string[] = ['reset'];
   if (isValidResetMode(mode)) {
      commands.push(`--${mode}`);
   }
   commands.push(...customArgs);

   return straightThroughStringTask(commands);
}

export function getResetMode(mode: ResetMode | unknown): Maybe<ResetMode> {
   if (isValidResetMode(mode)) {
      return mode;
   }

   switch (typeof mode) {
      case 'string':
      case 'undefined':
         return ResetMode.SOFT;
   }

   return;
}

function isValidResetMode(mode: ResetMode | unknown): mode is ResetMode {
   return typeof mode === 'string' && validResetModes.includes(mode);
}

```

### simple-git/src/lib/errors/git-error.ts
```
import type { SimpleGitTask } from '../types';

/**
 * The `GitError` is thrown when the underlying `git` process throws a
 * fatal exception (eg an `ENOENT` exception when attempting to use a
 * non-writable directory as the root for your repo), and acts as the
 * base class for more specific errors thrown by the parsing of the
 * git response or errors in the configuration of the task about to
 * be run.
 *
 * When an exception is thrown, pending tasks in the same instance will
 * not be executed. The recommended way to run a series of tasks that
 * can independently fail without needing to prevent future tasks from
 * running is to catch them individually:
 *
 * ```typescript
 import { gitP, SimpleGit, GitError, PullResult } from 'simple-git';

 function catchTask (e: GitError) {
   return e.
 }

 const git = gitP(repoWorkingDir);
 const pulled: PullResult | GitError = await git.pull().catch(catchTask);
 const pushed: string | GitError = await git.pushTags().catch(catchTask);
 ```
 */
export class GitError extends Error {
   constructor(
      public task?: SimpleGitTask<any>,
      message?: string
   ) {
      super(message);
      Object.setPrototypeOf(this, new.target.prototype);
   }
}

```

### simple-git/src/lib/tasks/diff.ts
```
import { StringTask } from '../types';
import { DiffResult } from '../../../typings';
import { isLogFormat, LogFormat, logFormatFromCommand } from '../args/log-format';
import { getDiffParser } from '../parsers/parse-diff-summary';
import { configurationErrorTask, EmptyTask } from './task';

export function diffSummaryTask(customArgs: string[]): StringTask<DiffResult> | EmptyTask {
   let logFormat = logFormatFromCommand(customArgs);

   const commands = ['diff'];

   if (logFormat === LogFormat.NONE) {
      logFormat = LogFormat.STAT;
      commands.push('--stat=4096');
   }

   commands.push(...customArgs);

   return (
      validateLogFormatConfig(commands) || {
         commands,
         format: 'utf-8',
         parser: getDiffParser(logFormat),
      }
   );
}

export function validateLogFormatConfig(customArgs: unknown[]): EmptyTask | void {
   const flags = customArgs.filter(isLogFormat);

   if (flags.length > 1) {
      return configurationErrorTask(
         `Summary flags are mutually exclusive - pick one of ${flags.join(',')}`
      );
   }

   if (flags.length && customArgs.includes('-z')) {
      return configurationErrorTask(
         `Summary flag ${flags} parsing is not compatible with null termination option '-z'`
      );
   }
}

```

### simple-git/src/lib/parsers/parse-branch-delete.ts
```
import { BranchMultiDeleteResult } from '../../../typings';
import {
   BranchDeletionBatch,
   branchDeletionFailure,
   branchDeletionSuccess,
} from '../responses/BranchDeleteSummary';
import { TaskParser } from '../types';
import { ExitCodes, LineParser, parseStringResponse } from '../utils';

const deleteSuccessRegex = /(\S+)\s+\(\S+\s([^)]+)\)/;
const deleteErrorRegex = /^error[^']+'([^']+)'/m;

const parsers: LineParser<BranchMultiDeleteResult>[] = [
   new LineParser(deleteSuccessRegex, (result, [branch, hash]) => {
      const deletion = branchDeletionSuccess(branch, hash);

      result.all.push(deletion);
      result.branches[branch] = deletion;
   }),
   new LineParser(deleteErrorRegex, (result, [branch]) => {
      const deletion = branchDeletionFailure(branch);

      result.errors.push(deletion);
      result.all.push(deletion);
      result.branches[branch] = deletion;
   }),
];

export const parseBranchDeletions: TaskParser<string, BranchMultiDeleteResult> = (
   stdOut,
   stdErr
) => {
   return parseStringResponse(new BranchDeletionBatch(), parsers, [stdOut, stdErr]);
};

export function hasBranchDeletionError(data: string, processExitCode: ExitCodes): boolean {
   return processExitCode === ExitCodes.ERROR && deleteErrorRegex.test(data);
}

```

### simple-git/src/lib/task-callback.ts
```
import { GitError } from './errors/git-error';
import { GitResponseError } from './errors/git-response-error';
import { SimpleGitTask, SimpleGitTaskCallback } from './types';
import { NOOP } from './utils';

export function taskCallback<R>(
   task: SimpleGitTask<R>,
   response: Promise<R>,
   callback: SimpleGitTaskCallback<R> = NOOP
) {
   const onSuccess = (data: R) => {
      callback(null, data);
   };

   const onError = (err: GitError | GitResponseError) => {
      if (err?.task === task) {
         callback(
            err instanceof GitResponseError ? addDeprecationNoticeToError(err) : err,
            undefined as any
         );
      }
   };

   response.then(onSuccess, onError);
}

function addDeprecationNoticeToError(err: GitResponseError) {
   let log = (name: string) => {
      console.warn(
         `simple-git deprecation notice: accessing GitResponseError.${name} should be GitResponseError.git.${name}, this will no longer be available in version 3`
      );
      log = NOOP;
   };

   return Object.create(err, Object.getOwnPropertyNames(err.git).reduce(descriptorReducer, {}));

   function descriptorReducer(all: PropertyDescriptorMap, name: string): typeof all {
      if (name in err) {
         return all;
      }

      all[name] = {
         enumerable: false,
         configurable: false,
         get() {
            log(name);
            return err.git[name];
         },
      };

      return all;
   }
}

```

### simple-git/src/lib/tasks/task.ts
```
import { TaskConfigurationError } from '../errors/task-configuration-error';
import type { BufferTask, EmptyTaskParser, SimpleGitTask, StringTask } from '../types';

export const EMPTY_COMMANDS: [] = [];

export type EmptyTask = {
   commands: typeof EMPTY_COMMANDS;
   format: 'empty';
   parser: EmptyTaskParser;
   onError?: undefined;
};

export function adhocExecTask(parser: EmptyTaskParser): EmptyTask {
   return {
      commands: EMPTY_COMMANDS,
      format: 'empty',
      parser,
   };
}

export function configurationErrorTask(error: Error | string): EmptyTask {
   return {
      commands: EMPTY_COMMANDS,
      format: 'empty',
      parser() {
         throw typeof error === 'string' ? new TaskConfigurationError(error) : error;
      },
   };
}

export function straightThroughStringTask(commands: string[], trimmed = false): StringTask<string> {
   return {
      commands,
      format: 'utf-8',
      parser(text) {
         return trimmed ? String(text).trim() : text;
      },
   };
}

export function straightThroughBufferTask(commands: string[]): BufferTask<Buffer> {
   return {
      commands,
      format: 'buffer',
      parser(buffer) {
         return buffer;
      },
   };
}

export function isBufferTask<R>(task: SimpleGitTask<R>): task is BufferTask<R> {
   return task.format === 'buffer';
}

export function isEmptyTask<R>(task: SimpleGitTask<R>): task is EmptyTask {
   return task.format === 'empty' || !task.commands.length;
}

```

### simple-git/src/lib/tasks/remote.ts
```
import {
   parseGetRemotes,
   parseGetRemotesVerbose,
   type RemoteWithoutRefs,
   type RemoteWithRefs,
} from '../responses/GetRemoteSummary';
import type { StringTask } from '../types';
import { straightThroughStringTask } from './task';

export function addRemoteTask(
   remoteName: string,
   remoteRepo: string,
   customArgs: string[]
): StringTask<string> {
   return straightThroughStringTask(['remote', 'add', ...customArgs, remoteName, remoteRepo]);
}

export function getRemotesTask(verbose: true): StringTask<RemoteWithRefs[]>;
export function getRemotesTask(verbose: false): StringTask<RemoteWithoutRefs[]>;
export function getRemotesTask(
   verbose: boolean
): StringTask<RemoteWithRefs[] | RemoteWithoutRefs[]> {
   const commands = ['remote'];
   if (verbose) {
      commands.push('-v');
   }

   return {
      commands,
      format: 'utf-8',
      parser: verbose ? parseGetRemotesVerbose : parseGetRemotes,
   };
}

export function listRemotesTask(customArgs: string[]): StringTask<string> {
   const commands = [...customArgs];
   if (commands[0] !== 'ls-remote') {
      commands.unshift('ls-remote');
   }

   return straightThroughStringTask(commands);
}

export function remoteTask(customArgs: string[]): StringTask<string> {
   const commands = [...customArgs];
   if (commands[0] !== 'remote') {
      commands.unshift('remote');
   }

   return straightThroughStringTask(commands);
}

export function removeRemoteTask(remoteName: string) {
   return straightThroughStringTask(['remote', 'remove', remoteName]);
}

```

### simple-git/src/lib/plugins/custom-binary.plugin.ts
```
import type { SimpleGitOptions } from '../types';

import { GitPluginError } from '../errors/git-plugin-error';
import { asArray } from '../utils';
import { PluginStore } from './plugin-store';

const WRONG_NUMBER_ERR = `Invalid value supplied for custom binary, requires a single string or an array containing either one or two strings`;
const WRONG_CHARS_ERR = `Invalid value supplied for custom binary, restricted characters must be removed or supply the unsafe.allowUnsafeCustomBinary option`;

function isBadArgument(arg: string) {
   return !arg || !/^([a-z]:)?([a-z0-9/.\\_~-]+)$/i.test(arg);
}

function toBinaryConfig(
   input: string[],
   allowUnsafe: boolean
): { binary: string; prefix?: string } {
   if (input.length < 1 || input.length > 2) {
      throw new GitPluginError(undefined, 'binary', WRONG_NUMBER_ERR);
   }

   const isBad = input.some(isBadArgument);
   if (isBad) {
      if (allowUnsafe) {
         console.warn(WRONG_CHARS_ERR);
      } else {
         throw new GitPluginError(undefined, 'binary', WRONG_CHARS_ERR);
      }
   }

   const [binary, prefix] = input;
   return {
      binary,
      prefix,
   };
}

export function customBinaryPlugin(
   plugins: PluginStore,
   input: SimpleGitOptions['binary'] = ['git'],
   allowUnsafe = false
) {
   let config = toBinaryConfig(asArray(input), allowUnsafe);

   plugins.on('binary', (input) => {
      config = toBinaryConfig(asArray(input), allowUnsafe);
   });

   plugins.append('spawn.binary', () => {
      return config.binary;
   });

   plugins.append('spawn.args', (data) => {
      return config.prefix ? [config.prefix, ...data] : data;
   });
}

```

(+17 more files reference the changed code)
Repository Map
.yarn/releases/yarn-4.12.0.cjs
devtools/log.ts
devtools/package-json.ts
devtools/package-versions.ts
devtools/repo-root.ts
devtools/reset-package-json.ts
devtools/vite-config.ts
packages/args-pathspec/index.ts
packages/args-pathspec/src/pathspec.ts
packages/args-pathspec/test/pathspec.spec.ts
packages/args-pathspec/vite.config.ts
packages/argv-parser/index.ts
packages/argv-parser/src/config/analyse-config.ts
packages/argv-parser/src/config/config-operands.ts
packages/argv-parser/src/config/config.types.ts
packages/argv-parser/src/config/detect-config-action.ts
packages/argv-parser/src/flags/flags.helpers.ts
packages/argv-parser/src/flags/parse-global-flags.ts
packages/argv-parser/src/flags/parse-task-flags.ts
packages/argv-parser/src/parse-argv.ts
packages/argv-parser/src/parse-argv.types.ts
packages/argv-parser/src/tokens/flag-specs.ts
packages/argv-parser/src/tokens/token-expander.ts
packages/argv-parser/src/vulnerabilities/detect-config-writes.ts
packages/argv-parser/src/vulnerabilities/detect-upload-pack.ts
packages/argv-parser/src/vulnerabilities/vulnerability-analysis.ts
packages/argv-parser/src/vulnerabilities/vulnerability.types.ts
packages/argv-parser/test/attack-vectors.spec.ts
packages/argv-parser/test/parse-argv.spec.ts
packages/argv-parser/test/parse-config-inline.spec.ts
packages/argv-parser/test/parse-config-read.spec.ts
packages/argv-parser/test/parse-config-write.spec.ts
packages/argv-parser/test/parse-flags.spec.ts
packages/argv-parser/test/parse-paths.spec.ts
packages/argv-parser/test/task-detection.spec.ts
packages/argv-parser/test/vulnerability-analysis.spec.ts
packages/argv-parser/vite.config.ts
packages/babel-config/babel.config.js
packages/test-es-module-consumer/suite.mjs
packages/test-es-module-consumer/test-default-as.mjs
packages/test-es-module-consumer/test-default.mjs
packages/test-es-module-consumer/test-named.mjs
packages/test-es-module-consumer/test.mjs
packages/test-javascript-consumer/suite.js
packages/test-javascript-consumer/test-default-as.js
packages/test-javascript-consumer/test-default.js
packages/test-javascript-consumer/test-named.js
packages/test-javascript-consumer/test.js
packages/test-typescript-consumer/babel.config.js
packages/test-typescript-consumer/test/ts-default-from-root.spec.ts
packages/test-typescript-consumer/test/ts-named-import.spec.ts
packages/test-typescript-esm-consumer/babel.config.js
packages/test-typescript-esm-consumer/test/ts-default-renamed-import.spec.ts
packages/test-typescript-esm-consumer/test/ts-named-import.spec.ts
packages/test-utils/index.ts
packages/test-utils/src/create-abort-controller.ts
packages/test-utils/src/create-test-context.ts
packages/test-utils/src/expectations.ts
packages/test-utils/src/instance.ts
packages/test-utils/src/like.ts
packages/test-utils/src/setup/setup-conflicted.ts
packages/test-utils/src/setup/setup-files.ts
packages/test-utils/src/setup/setup-ignored.ts
packages/test-utils/src/setup/setup-init.ts
packages/test-utils/src/wait.ts
simple-git/babel.config.js
simple-git/jest.config.js
simple-git/promise.js
simple-git/scripts/build.js
simple-git/scripts/log.js
simple-git/src/esm.mjs
simple-git/src/git.js
simple-git/src/index.js
simple-git/src/lib/api.ts
simple-git/src/lib/args/log-format.ts
simple-git/src/lib/errors/git-construct-error.ts
simple-git/src/lib/errors/git-error.ts
simple-git/src/lib/errors/git-plugin-error.ts
simple-git/src/lib/errors/git-response-error.ts
simple-git/src/lib/errors/task-configuration-error.ts
simple-git/src/lib/git-factory.ts
simple-git/src/lib/git-logger.ts
simple-git/src/lib/parsers/parse-branch-delete.ts
simple-git/src/lib/parsers/parse-branch.ts
simple-git/src/lib/parsers/parse-commit.ts
simple-git/src/lib/parsers/parse-diff-summary.ts
simple-git/src/lib/parsers/parse-fetch.ts
simple-git/src/lib/parsers/parse-list-log-summary.ts
simple-git/src/lib/parsers/parse-merge.ts
simple-git/src/lib/parsers/parse-move.ts
simple-git/src/lib/parsers/parse-pull.ts
simple-git/src/lib/parsers/parse-push.ts
simple-git/src/lib/parsers/parse-remote-messages.ts
simple-git/src/lib/parsers/parse-remote-objects.ts
simple-git/src/lib/plugins/abort-plugin.ts
simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts
simple-git/src/lib/plugins/command-config-prefixing-plugin.ts
simple-git/src/lib/plugins/completion-detection.plugin.ts
simple-git/src/lib/plugins/custom-binary.plugin.ts
simple-git/src/lib/plugins/error-detection.plugin.ts
simple-git/src/lib/plugins/index.ts
simple-git/src/lib/plugins/plugin-store.ts
simple-git/src/lib/plugins/progress-monitor-plugin.ts
simple-git/src/lib/plugins/simple-git-plugin.ts
simple-git/src/lib/plugins/spawn-options-plugin.ts
simple-git/src/lib/plugins/suffix-paths.plugin.ts
simple-git/src/lib/plugins/timout-plugin.ts
simple-git/src/lib/responses/BranchDeleteSummary.ts
simple-git/src/lib/responses/BranchSummary.ts
simple-git/src/lib/responses/CheckIgnore.ts
simple-git/src/lib/responses/CleanSummary.ts
simple-git/src/lib/responses/ConfigList.ts
simple-git/src/lib/responses/DiffSummary.ts
simple-git/src/lib/responses/FileStatusSummary.ts
simple-git/src/lib/responses/GetRemoteSummary.ts
simple-git/src/lib/responses/InitSummary.ts
simple-git/src/lib/responses/MergeSummary.ts
simple-git/src/lib/responses/PullSummary.ts
simple-git/src/lib/responses/StatusSummary.ts
simple-git/src/lib/responses/TagList.ts
simple-git/src/lib/runners/git-executor-chain.ts
simple-git/src/lib/runners/git-executor.ts
simple-git/src/lib/runners/promise-wrapped.ts
simple-git/src/lib/runners/scheduler.ts
simple-git/src/lib/runners/tasks-pending-queue.ts
simple-git/src/lib/simple-git-api.ts
simple-git/src/lib/task-callback.ts
simple-git/src/lib/tasks/apply-patch.ts
simple-git/src/lib/tasks/branch.ts
simple-git/src/lib/tasks/change-working-directory.ts
simple-git/src/lib/tasks/check-ignore.ts
simple-git/src/lib/tasks/check-is-repo.ts
simple-git/src/lib/tasks/checkout.ts
simple-git/src/lib/tasks/clean.ts
simple-git/src/lib/tasks/clone.ts
simple-git/src/lib/tasks/commit.ts
simple-git/src/lib/tasks/config.ts
simple-git/src/lib/tasks/count-objects.ts
simple-git/src/lib/tasks/diff-name-status.ts
simple-git/src/lib/tasks/diff.ts
simple-git/src/lib/tasks/fetch.ts
simple-git/src/lib/tasks/first-commit.ts
simple-git/src/lib/tasks/grep.ts
simple-git/src/lib/tasks/hash-object.ts
simple-git/src/lib/tasks/init.ts
simple-git/src/lib/tasks/log.ts
simple-git/src/lib/tasks/merge.ts
simple-git/src/lib/tasks/move.ts
simple-git/src/lib/tasks/pull.ts
simple-git/src/lib/tasks/push.ts
simple-git/src/lib/tasks/remote.ts
simple-git/src/lib/tasks/reset.ts
simple-git/src/lib/tasks/show.ts
simple-git/src/lib/tasks/stash-list.ts
simple-git/src/lib/tasks/status.ts
simple-git/src/lib/tasks/sub-module.ts
simple-git/src/lib/tasks/tag.ts
simple-git/src/lib/tasks/task.ts
simple-git/src/lib/tasks/version.ts
simple-git/src/lib/types/handlers.ts
simple-git/src/lib/types/index.ts
simple-git/src/lib/types/tasks.ts
simple-git/src/lib/utils/argument-filters.ts
simple-git/src/lib/utils/exit-codes.ts
simple-git/src/lib/utils/git-output-streams.ts
simple-git/src/lib/utils/index.ts
simple-git/src/lib/utils/line-parser.ts
simple-git/src/lib/utils/simple-git-options.ts
simple-git/src/lib/utils/task-options.ts
simple-git/src/lib/utils/task-parser.ts
simple-git/src/lib/utils/util.ts
simple-git/test/integration/add.spec.ts
simple-git/test/integration/bad-initial-path.spec.ts
simple-git/test/integration/branches-show-current.spec.ts
simple-git/test/integration/branches.spec.ts
simple-git/test/integration/broken-chains.spec.ts
simple-git/test/integration/change-directory.spec.ts
simple-git/test/integration/check-ignore.win32.spec.ts
simple-git/test/integration/check-is-repo.spec.ts
simple-git/test/integration/checkout.spec.ts
simple-git/test/integration/clean.spec.ts
simple-git/test/integration/commit.spec.ts
simple-git/test/integration/concurrent-commands.spec.ts
simple-git/test/integration/config.spec.ts
simple-git/test/integration/diff.spec.ts
simple-git/test/integration/exec.spec.ts
simple-git/test/integration/fetch.spec.ts
simple-git/test/integration/grep.spec.ts
simple-git/test/integration/log-name-status.spec.ts
simple-git/test/integration/log-numstat.spec.ts
simple-git/test/integration/log.spec.ts
simple-git/test/integration/merge-integration.spec.ts
simple-git/test/integration/output-handler.spec.ts
simple-git/test/integration/plugin.abort.spec.ts
simple-git/test/integration/plugin.completion.spec.ts
simple-git/test/integration/plugin.progress.spec.ts
simple-git/test/integration/plugin.timeout.spec.ts
simple-git/test/integration/plugin.unsafe.spec.ts
simple-git/test/integration/promise-from-root.spec.ts
simple-git/test/integration/promise.spec.ts
simple-git/test/integration/pull-fails-ff.spec.ts
simple-git/test/integration/remote.spec.ts
simple-git/test/integration/reset.spec.ts
simple-git/test/integration/rev-parse.spec.ts
simple-git/test/integration/status.spec.ts
simple-git/test/integration/tag.spec.ts
simple-git/test/integration/version.spec.ts
simple-git/test/unit/__mocks__/mock-child-process.ts
simple-git/test/unit/add.spec.ts
simple-git/test/unit/apply-patch.spec.ts
simple-git/test/unit/args.log-format.spec.ts
simple-git/test/unit/branch.spec.ts
simple-git/test/unit/catfile.spec.ts
simple-git/test/unit/check-ignore.spec.ts
simple-git/test/unit/check-is-repo.spec.ts
simple-git/test/unit/checkout.spec.ts
simple-git/test/unit/child-process.spec.ts
simple-git/test/unit/clean.spec.ts
simple-git/test/unit/clone.spec.ts
simple-git/test/unit/commit.spec.ts
simple-git/test/unit/config.spec.ts
simple-git/test/unit/count-objects.spec.ts
simple-git/test/unit/cwd.spec.ts
simple-git/test/unit/diff.spec.ts
simple-git/test/unit/fetch.spec.ts
simple-git/test/unit/first-commit.spec.ts
simple-git/test/unit/git-executor.spec.ts
simple-git/test/unit/git.spec.ts
simple-git/test/unit/grep.spec.ts
simple-git/test/unit/hash-object.spec.ts
simple-git/test/unit/init.spec.ts
simple-git/test/unit/log.spec.ts
simple-git/test/unit/logging.spec.ts
simple-git/test/unit/merge.spec.ts
simple-git/test/unit/mv.spec.ts
simple-git/test/unit/output-handler.spec.ts
simple-git/test/unit/plugins/plugin.abort.spec.ts
simple-git/test/unit/plugins/plugin.binary.spec.ts
simple-git/test/unit/plugins/plugin.completion-detection.spec.ts
simple-git/test/unit/plugins/plugin.error.spec.ts
simple-git/test/unit/plugins/plugin.pathspec.spec.ts
simple-git/test/unit/plugins/plugin.unsafe.spec.ts
simple-git/test/unit/plugins/plugins.spec.ts
simple-git/test/unit/promises.spec.ts
simple-git/test/unit/pull.spec.ts
simple-git/test/unit/push.spec.ts
simple-git/test/unit/raw.spec.ts
simple-git/test/unit/rebase.spec.ts
simple-git/test/unit/remote-messages.spec.ts
simple-git/test/unit/remote.spec.ts
simple-git/test/unit/reset.spec.ts
simple-git/test/unit/rev-parse.spec.ts
simple-git/test/unit/revert.spec.ts
simple-git/test/unit/rm.spec.ts
simple-git/test/unit/scheduler.spec.ts
simple-git/test/unit/show.spec.ts
simple-git/test/unit/stash-list.spec.ts
simple-git/test/unit/stash.spec.ts
simple-git/test/unit/status.spec.ts
simple-git/test/unit/sub-module.spec.ts
simple-git/test/unit/tags.spec.ts
simple-git/test/unit/task-options.spec.ts
simple-git/test/unit/update-server-info.spec.ts
simple-git/test/unit/utils.spec.ts
simple-git/test/unit/version.spec.ts
simple-git/typings/errors.d.ts
simple-git/typings/index.d.ts
simple-git/typings/response.d.ts
simple-git/typings/simple-git.d.ts
simple-git/typings/types.d.ts
Package Manifests (Dependencies, scripts, build configuration)
### package.json
```
{
  "name": "@simple-git/repo",
  "version": "3.1.1",
  "private": true,
  "workspaces": [
    "packages/*",
    "simple-git"
  ],
  "resolutions": {
    "jest": "29.7.0",
    "typescript": "^5.7.3"
  },
  "scripts": {
    "build": "yarn workspaces foreach -A run build",
    "build:pkg": "yarn workspaces foreach -A run build:pkg",
    "build:pkg:reset": "tsx ./devtools/reset-package-json",
    "clean": "git clean -fxd -e .idea -e node_modules -e .yarn",
    "clean:cache": "git clean -fxd .yarn node_modules packages simple-git",
    "lint": "biome check",
    "lint:fix": "biome check --write",
    "test": "yarn workspaces foreach -A run test",
    "test:win": "yarn workspaces foreach -A run test:win"
  },
  "dependencies": {
    "@changesets/changelog-github": "^0.5.2",
    "@changesets/cli": "^2.29.8",
    "tsx": "^4.21.0",
    "typescript": "^5"
  },
  "devDependencies": {
    "@biomejs/biome": "^2.1.4",
    "@kwsites/exec-p": "^0.4.0"
  },
  "packageManager": "yarn@4.12.0"
}

```
Context & Existing Test Patterns
Existing test files touched by the patch: packages/argv-parser/test/__fixtures__/mocks.ts, packages/argv-parser/test/attack-vectors.spec.ts, packages/argv-parser/test/parse-argv.spec.ts, packages/argv-parser/test/parse-env.spec.ts, packages/argv-parser/test/vulnerability-analysis.spec.ts, packages/argv-parser/test/vulnerability-check.spec.ts, simple-git/test/integration/plugin.unsafe.spec.ts, simple-git/test/unit/clone.spec.ts
Repository top-level entries: .changeset, .editorconfig, .git-blame-ignore-revs, .github, .gitignore, .nvmrc, .yarn, .yarnrc.yml, CHANGELOG.md, LICENSE, biome.json, devtools, docs, examples, package.json, packages, readme.md, simple-git, tsconfig.json, yarn.lock
Project's own test patterns and conventions:
### packages/argv-parser/test/__fixtures__/mocks.ts
```
import type { ConfigRead, ConfigWrite, ParsedFlag } from '../../src/parse-argv.types';

export function aParsedFlag(name: string, value?: string): ParsedFlag {
   return value !== undefined ? { name: name, value } : { name: name };
}

export function aWriteConfig(
   key: string,
   scope: ConfigWrite['scope'],
   value?: string
): ConfigWrite {
   return value !== undefined ? { key, scope, value } : { key, scope };
}

export function aReadConfig(key: string, scope: ConfigRead['scope']): ConfigRead {
   return { key, scope };
}

```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Approved design (previous step)
<instruction_md>
# Git started a program named in caller-supplied configuration

## What we observed

Our deployment service uses simple-git to clone a repository and forwards a configuration value chosen by the tenant. On that clone we passed `credential.helper` inline, with the value set to a program path the tenant controls. The call returned normally and the program ran during the clone. We already get a refusal for a custom upload or receive pack, and for a change that widens which protocol helpers git may launch, so we expected the same refusal here. A configuration value that names an external program, or that selects a directory of scripts to copy into a repository, should be refused unless we have explicitly enabled that risk.

## Impact

A tenant who can choose that configuration also chooses a program the git process will execute. On our runners that is enough to run code inside the job and to receive credentials the helper interface is handed.

## What must keep working

Ordinary repository settings must still be accepted: the committer name and email, line-ending and whitespace choices, and the default branch name. Callers who have opted in to a custom upload or receive pack, or to a non-default protocol helper, must still be able to use those. Reading and writing a normal configuration key, and creating a commit that carries an explicit message, must keep working.

</instruction_md>
<task_metadata_json>
{
  "entry_point": "simpleGit().clone() and simpleGit().raw() forwarding caller-supplied inline git configuration",
  "techniques": [
    1,
    2,
    3,
    5,
    9,
    12,
    13,
    15
  ],
  "trap": {
    "paths": [
      "simple-git/src/lib/runners/git-executor-chain.ts"
    ],
    "contract": "Committer name and email, line-ending and whitespace choices, the default branch name, a normal configuration read or write, an explicit commit message, and an already opted-in custom pack or protocol helper must still succeed."
  },
  "fix_places": [
    "packages/argv-parser/index.ts",
    "packages/argv-parser/src/env/parse-env.ts",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts",
    "packages/argv-parser/src/vulnerabilities/vulnerability-analysis.ts",
    "packages/argv-parser/src/vulnerabilities/vulnerability-check.ts",
    "simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts",
    "simple-git/src/lib/runners/git-executor-chain.ts"
  ],
  "unrelated_files": [
    "packages/argv-parser/src/args/parse-argv.ts",
    "packages/argv-parser/src/args/parse-argv.types.ts",
    "packages/argv-parser/src/config/analyse-config.ts",
    "packages/argv-parser/src/config/detect-config-action.ts",
    "packages/argv-parser/src/tokens/flag-specs.ts",
    "packages/argv-parser/src/vulnerabilities/detect-config-writes.ts",
    "packages/argv-parser/src/vulnerabilities/detect-upload-pack.ts",
    "packages/argv-parser/src/vulnerabilities/vulnerability.types.ts",
    "simple-git/src/lib/plugins/simple-git-plugin.ts",
    "simple-git/src/lib/types/index.ts"
  ]
}
</task_metadata_json>

# Split generation (this request)
The report, metadata and check patches were approved in the previous step. Return ONLY the `<hidden_tests_py>` block,
following every test constraint above. Keep the suite lean: at most 6 `test_security_*` and 6 `test_functional_*`
tests, each focused and under 60 lines. Do not repeat the instruction, metadata or patches.

