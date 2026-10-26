# stk-locutus-ghsavc8f build notes

- Task: `stk-locutus-ghsavc8f` (stacked, pattern A+B / history H3b); control `stk-locutus-ghsavc8f-control`.
- Repo: `locutusjs/locutus`; pinned `57ea89d4da3b9bcfc983fd27da77a1bdd5d53f01` = first parent of fix A
  `042af9ca7fde` (verified with `git rev-parse 042af9ca^`). Fix B is `345a6211e1e6`.
- Start UTC: 2026-10-26T02:15:27Z. End UTC: see the gate report timestamp; this file's last edit is the end.

## Levers (one line each)

- **T1** — pattern A, shape: a how-type guard bypass. `src/php/strings/parse_str.js:77` decides with a
  replaceable string method on the raw name, before the name is split into bracket segments at
  `:116` and written through the object walk at `:150`. Reason to dismiss: a prototype-pollution
  guard is already present and every name passes through it, so the file reads as fixed.
- **T2** — pattern A (published-fix far site), type deepseek. `src/php/var/unserialize.js:261,337`
  assigns a payload key straight onto the structure being built, so a prototype-named key becomes
  its prototype; both the object and the array sink need the treatment. Reason to dismiss: the
  keys read as data and PHP parity requires arbitrary string keys.
- **T3** — pattern B (protection never existed), type deepseek. `src/php/info/ini_set.js:17,19,42`
  looks a caller-chosen name up through the ini record's prototype chain and then writes the fixed
  `local_value` property on whatever the lookup returned. Reason to dismiss: a config setter is
  called with literal names and is not the function named in the report.
- **T4** — pattern B (protection never existed), type both. Six array helpers copy a caller key into
  a fresh result by assignment: `array_merge.js:55`, `array_merge_recursive.js:33,48,54,57`,
  `array_replace.js:20,25`, `array_replace_recursive.js:28,35,37`,
  `array_change_key_case.js:30`, `array_combine.js:36`. Reason to dismiss: each returns a fresh
  object, so the write looks like ordinary copy plumbing and cannot reach a shared object.

Concepts: `[T1]`, `[T2]`, `[T3]`, `[T4]` (four independent edit sites). DeepSeek-type: T2, T3, T4.
MiMo-type (how-type): T1, T4.

## Verified on the pinned tree (local, before Docker)

- Pinned: security 0/17 pass, functional 26/26 pass.
- Reference fix: security 17/17, functional 26/26.
- Each `miss_*` patch fails exactly its concept's security cases and keeps functional green.
- `upstream_first_fix.patch` (fix A alone): security 3/17 pass — the two tamper states both fail, so
  the first published fix is proved to be a wrong fix.
- `upstream_fix.patch` (A+B ported): security 9/17 pass — T3 and T4 remain open.
- `naive_whole_key.patch` (guard placed on the raw name before segment splitting): security fail.
- `refuse_all.patch`: functional fail (all request-string parsing lost).
- `functional_overbroad.patch`: functional fail (`F-parse-normalisation`).
- `alt_correct_fix.patch` (skip/refuse design, different implementation): 17/17 + 26/26 pass.
- `hardening.patch` (reference plus extra safe writes in sibling array helpers): pass.
- Control (local, exact staging): pinned 0/5 security, 26/26 functional; reference 5/5 + 26/26; mis-check
  fails security; over-broad check fails functional. Container gate: static PASSED only; nop was stopped by
  the background time limit during the shared-host teardown, so the control's nop/oracle/patches are ungated.
- The project's own 9 generated vitest files (25 cases) pass at pinned and after the reference fix.

## Verified in the image / gate

- Both tasks: `gate.py --only static` PASSED (stacked and control).
- Verifier-image gotcha fixed during the gate: on `node:20-bookworm-slim` uid 1000 is `node` with
  group `node`; the template `tests.Dockerfile` boilerplate renames the user but not the group, so
  `chown agent:agent` failed. Both verifier Dockerfiles now carry the `groupmod -n agent` line the
  environment template already had.
- The verifier staging path was simulated exactly (`support/`, `security/`, `functional/`, the
  pristine project tests and the `node_modules` link): pinned tree gives security 0/17 and
  functional 26/26, so the nop requirement holds with the real staging commands.
- Docker/Harbor: the shared daemon was wedged for container creation and `docker ps -a` for a
  stretch (the known shared-VM buildkit-session flake; `docker run` and label-filtered queries kept
  working). Stages were retried; the final per-stage results are in `gate_report.<stage>.json` and
  summarised below.
- `--only nop` PASSED: 17 security tests all fail on the pinned tree and 26 functional tests pass.
  Two host-side fixes were needed first: the missing `groupmod` in the verifier Dockerfile, and a
  private `TMPDIR` for the gate process because the shared `/tmp` lost Harbor's verifier compose
  file mid-run. Both are infrastructure, not task behaviour.
- `--only oracle` PASSED: three runs, each reward 1.0 with identical results.
- `--only patches` PASSED 9/9: each `miss_*` fails exactly its concept's security tests and keeps
  functional green; `upstream_first_fix` scores 0.1765 (the first published fix is proved wrong);
  `upstream_fix` scores 0.5294 (the pair still leaves T3/T4 open); `functional_overbroad` fails
  exactly `F-parse-normalisation`; `alt_correct_fix` and `hardening` both score 1.0.

## Unverified or guessed

- The reader record lists T2-T6/T8 as `published_fix_far_site`; B's readable diff only touches the
  request-string parser and the deserialiser, so T8 and the array family were re-labelled
  `uncovered_upstream` here. This is a correction, not a change to the code.
- T3's real-world reach needs an application to pass a request-derived name to the setting setter;
  the code path is present and still present upstream, but no published advisory covers it.
- Array-family impact is limited to the prototype of the fresh result (no path to Object.prototype
  was found); the task's property therefore includes "keeps the ordinary prototype it would have".
- Current-upstream presence was read from a clone at `2b99b33f24` (2026-10); the sinks are still
  present there.
- `entry_point`/`project_tests_run` assume the exported CommonJS modules are the intended public
  surface, which is how the project's own generated tests call them.

## Outside scope (one line)

- Other PHP-compatibility helpers in the same tree (e.g. the copy-loop family listed by the reader
  as T11) also change a result prototype; they were not built on and are only touched by the
  `hardening` pass patch.
