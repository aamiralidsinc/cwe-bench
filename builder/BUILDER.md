# Task builder brief

You turn ONE shortlisted candidate (a real security fix in a real open-source
repository) into ONE Harbor-format security-fix task, and you prove with the
gate script that it works. Work on that one candidate only.

A solver agent will later be given the vulnerable repository and a
vulnerability report, and must fix the flaw. Hidden tests decide the score.
The task is useful only if a correct fix scores 1.0, and a lazy fix (one that
blocks just the reported input, or that removes the feature) does not.

## Inputs

- The candidate row (JSON, given with this brief): repository, vulnerable
  parent commit, fix commit, CWE, the reader's notes on the flaw and on the
  "tempting wrong fix". Fields ending in `_GUESS` or `_JUDGEMENT` are another
  reader's opinion: verify them against the code, do not trust them.
- `SLUG`: the task's directory name (given with this brief).
- Templates: `cwe-bench/builder/templates/` (`task.toml`, `test.sh`, `score.py`).
- Agent layer: `cwe-bench/harness/claude-code.Dockerfile.snippet`.
- Working example of the Harbor layout: `cwe-bench/harness/smoke-task/`.

## Outputs

```
cwe-bench/tasks/SLUG/
  instruction.md          the vulnerability report
  task.toml               from the template, [metadata] filled in
  environment/Dockerfile  repo at the vulnerable commit, everything installed
  solution/solve.sh       applies /solution/fix.patch to /app
  solution/fix.patch      the reference fix (source changes only)
  tests/test.sh           from the template; runs both groups, then score.py
  tests/score.py          copied unchanged from the template
  tests/security/...      exploit tests
  tests/functional/...    feature tests
cwe-bench/build/SLUG/
  manifest.json           see "Manifest"
  checks/*.patch          the wrong fixes used to test the tests
  notes.md                short: what you verified, what you could not
```

Scratch work (clones, experiments) goes in `~/.tb-graders/cwe/work/SLUG/`,
never inside `cwe-bench/`.

## Steps

### 3a. Environment
- `environment/Dockerfile`: start from a small official base image, fetch the
  repository at the VULNERABLE commit into `/app` (`git init` + `git fetch
  --depth 1 origin <sha>` + checkout works when the sha is reachable), then
  delete `/app/.git` so the later history is not in the image.
- Install every dependency, test tool and service the project and your tests
  need. The task must run with NO network after the image is built: no
  downloads in `test.sh`, in the tests, or at service start-up. If the project
  needs a database or cache, install it in the same image and start it from
  `test.sh` (and document how the solver can start it, in instruction.md).
- Install `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- Append the agent layer snippet unchanged at the end.
- Keep the image as small and quick to build as the project allows.
- Confirm the project's own existing tests for the affected area run and pass
  in the image at the vulnerable commit.

### 3b. Exploit
- Reproduce the flaw on the vulnerable code THROUGH A REAL ENTRY POINT: an HTTP
  request to the running application, a CLI invocation, or the library's public
  API as a downstream user would call it. Not by calling an internal helper.
- If you cannot make the exploit work on the vulnerable commit, stop and
  report `abandoned` with the reason. Do not write tests for a flaw you did
  not reproduce.
- Then find VARIANTS: other inputs, encodings, code paths, endpoints or call
  sites that reach the same root cause. Read the fix and ask "where else is
  this trust decision made?". Each variant must really work on the vulnerable
  code. Variants are the point of the task: a fix that only blocks the
  reported input must still fail.
### 3c. Tests
- `tests/security/`: one test per distinct exploit/variant. Each goes through
  the real entry point and asserts the attack is BLOCKED. On vulnerable code it
  must FAIL (attack succeeds); on fixed code it must PASS. At least 4, covering
  more than one code path / input class.
- `tests/functional/`: legitimate-use tests plus, where they exist, the
  project's own tests for the affected area. These assert the feature still
  works, so a fix that over-blocks or deletes the feature fails. At least 5.
- Write tests so they emit JUnit XML into the two directories the template
  names. Copy `score.py` unchanged. Edit only the marked command lines in
  `test.sh`.
- No test may reach the network or depend on the fix commit being present.
- **Hidden tests never go into the image.** The agent works in the same
  container the tests later run in, so anything under `environment/` is
  readable and runnable by the agent. Earlier tasks (hickory-dns, rclone,
  russh) baked their test harness into `/opt/harness`, and agents ran the
  hidden suite and fixed until it passed. All test code, test helpers and
  harness sources live under `tests/`. `test.sh` copies them into place
  (e.g. `/opt/harness`) at grading time. To keep grading fast for compiled
  languages, pre-build dependencies in the image against **stubs**: a Rust
  crate with empty `src/lib.rs` / `tests/*.rs`, or Go files that keep the real
  file's `package` line and blank-import (`_ "pkg"`) everything it imports, but
  define no tests. The gate fails any task whose `environment/` contains test
  definitions, test names from `tests/security/`, or copies of files in
  `tests/`.

### 3d / 3e. Oracle and the before/after proof
- `solution/fix.patch`: the upstream fix reduced to SOURCE changes only (drop
  edits to the repo's own test files, changelogs, docs). `solve.sh` applies it
  to `/app`.
- The gate runs this for you, but convince yourself first: vulnerable code →
  security tests fail, functional pass; after the patch → all pass, twice,
  identically.

### 3f. The wrong-fix patches (this is what tests the tests)
Put these under `build/SLUG/checks/` and list them in the manifest:
- One `security_fail` patch: the tempting shallow fix (blocks the reported
  input only, or patches one site). It must make functional tests pass but
  leave at least one security test failing. If it makes them all pass, your
  variants are too weak — add variants until it fails.
- One `functional_fail` patch: a fix that kills the exploit by disabling or
  over-restricting the feature. It must break at least one functional test. If
  it does not, your functional tests do not protect the feature — add one.
- Optional `pass` patch: a correct fix written differently from the upstream
  one (e.g. the fix placed at a different-but-valid layer). It must score 1.0.
  Include one whenever a second valid fix is plausible: it proves the tests do
  not just hard-code the upstream patch's shape, which is the main defect that
  made real benchmarks reject tasks.
- **Required `pass` patch, `"kind": "hardening"`:** the reference fix plus
  defensive hardening of the product code your security tests import. For
  example, make a shared path helper throw on traversal. It must score 1.0. The
  gate report lists each security test's product imports
  (`security_test_product_imports`) so you know what to harden.
- **Required `pass` patch, `"kind": "blind"`:** a fix written by a fresh agent
  that sees only `instruction.md` and the repository, never the reference fix,
  the tests or this build. It must score 1.0.
  - Ask the same agent to name the vulnerable mechanisms. If it names an injected
    sibling's mechanism from the instruction alone, the instruction leaks it.
    Rewrite the instruction at the level of the security property.
- Both are warnings for tasks built before 2026-10-16. Set `"strict_gate": true`
  in the manifest of every new task, so the gate fails without them.

### 3g. Test rules learned from our own runs (2026-10-16)
Two of our three "per-model failures" turned out to be test faults; the full
analysis is in `research/own-runs/FINDINGS.md`. Correct fixes failed for these
reasons:
- **The test called product code to compute its expected value or to clean up.**
  actualbudget called `getPathForUserFile`, which MiMo had hardened, so the test
  crashed. Compute expected values in the test itself.
- **The test asserted one exact refusal status** (trigger-dev: only 405; argo:
  only 403). Assert that the attack is blocked: any 4xx, plus no side effect.
  The gate fails exact-status assertions in security tests unless the line
  carries `gate: exact-status-ok` after review.
- **The test used a constant the instruction never states** (argo's 2 MB limit,
  taken from upstream). Either state it in the instruction, or test far beyond
  any reasonable value: argo now streams 128 MiB and checks that the body was
  not read in full.
- **The test varied a setting other than the one the instruction names.**
  stigmem said "bound to a non-loopback address" (`host`) but varied
  `node_url`. Make each scenario unambiguous by setting every candidate knob.
- **The test exercised a layer the instruction does not describe.** stigmem v4
  called an internal function; the instruction says "at startup". Drive the
  entry point the instruction names.
- **A test relied on an interface that only the fix introduces.** rclone's correct-secret
  tests needed the proxy to return the secret as `_secret_access_key`, a field documented
  only in the upstream fix. If a test needs such a contract, state it in the instruction.
- **Fake permission checks answered the same for every resource.** argo's tests did, so a fix
  that checked permission on the wrong resource passed. Make stubs answer per resource and
  verb, like real RBAC.
- **A functional test used a fixture outside the instruction's scope.**
  trigger-dev used a batch that doesn't exist where the instruction says
  "their own batches". Seed the real object the instruction refers to.

## Manifest (`build/SLUG/manifest.json`)

```json
{
  "slug": "SLUG",
  "candidate": { ...the row you were given... },
  "verified": {
    "exploit_entry_point": "how the exploit reaches the flaw",
    "variants": ["list each variant and the path it exercises"],
    "services": ["postgres"],
    "project_tests_run": "which existing tests you ran and that they passed"
  },
  "leak_terms": ["words the instruction must not contain: the vuln's common",
                 "name, the fixing function, the CVE, distinctive identifiers"],
  "patch_checks": [
    {"patch": "shallow_poc_only.patch",   "expect": "security_fail"},
    {"patch": "disable_feature.patch",    "expect": "functional_fail"},
    {"patch": "alt_correct_fix.patch",    "expect": "pass"}
  ],
  "status": "built",
  "notes": "anything the gate cannot see"
}
```

## instruction.md (the report)
Write it as a real vulnerability report a user or triager would file: the
observed impact and how it is triggered, through the real entry point. State
the security property that must hold and that the feature must keep working.
NO fix, NO file or function names, NO line numbers, NO CVE/GHSA id, NO count of
how many places need changing. The gate rejects the task if any of those leak.

## Run the gate
```
python3 -I cwe-bench/builder/gate.py SLUG
```
It runs static → nop → oracle → patches and writes
`build/SLUG/gate_report.json`. The task is built only when it prints PASSED.
Use `--only static` while iterating to check the cheap things first.

## Report back
State plainly: PASSED or not; the funnel facts (did the exploit reproduce, how
many variants, how many security/functional tests, which services); every
guess you could not verify; and if abandoned, exactly why (could not build,
could not reproduce, flaky, needs network at run time, needs a GUI/kernel/GPU).
Do not claim a task is good because the upstream fix exists — claim it only
when the gate prints PASSED.

## Common build gotchas (from pilot builds)
- **setuptools-scm / git-derived versions:** stripping `/app/.git` breaks
  `pip install -e .` for projects that derive their version from git. Set
  `ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_<PKG>=<version>` before the install,
  or install before removing `.git`.
- **starlette/FastAPI TestClient** needs `httpx` in the image; it is synchronous
  so `pytest-asyncio` is not required.
- **PHP/Laravel** tasks can run offline via Orchestra Testbench + in-memory
  SQLite (no DB service); install the needed php extensions in the image.
- If a gate `nop` stage fails with a truncated "Docker compose build failed",
  reproduce with a direct `docker build` of environment/ to see the real error.
