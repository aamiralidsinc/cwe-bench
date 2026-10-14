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
