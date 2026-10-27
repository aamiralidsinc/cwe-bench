# Task quality before trials

Every failing run is audited and every both-model failure gets a fairness review. The pieces below move part of that
assurance before trials. They are warning-only: nothing here blocks a task, and the fairness review after trials
still decides.

## Shared refusal helpers

`common/builder/templates/support/refusal/` holds one helper per test stack:

| Stack | File | Entry points |
|---|---|---|
| pytest | `refusal.py` | `refused_or(call, ok=..., refusals=(...))`, `must_refuse`, `attempt` |
| JS/TS (vitest, jest, node:test) | `refusal.mjs` | `refusedOr(call, {ok, refusals})`, `mustRefuse`, `attempt` |
| Go | `refusal.go` | `refusal.Do(t, call, refusals...)`, `refusal.MustRefuse` |
| JUnit | `Refusal.java` | `Refusal.refusedOr(call, ok, Refusal.class...)`, `mustRefuse`, `attempt` |
| PHPUnit | `Refusal.php` | `Refusal::refusedOr($call, $ok, [...])`, `mustRefuse`, `attempt` |

A security test that drives a hardened function or handler directly passes when the call is refused or when it
completes safely:
- **Refused:** a 4xx status (on the result or on the exception), or one of the refusal exceptions the test declares
  (the product's own: `PermissionError`, a framework `ForbiddenHttpException`, an `ErrForbidden`).
- **Not a refusal:** a 5xx, a panic, or any other exception. These fail the test, so a fix that merely breaks the call
  is still caught (wrong-fix class `crash_as_refusal`).
- **Side effects:** the test checks them after every outcome.

## Scoring robustness

The template `score.py` counts a test that errors during setup as failed in every result format:
- an `<error>` or `<failure>` in a test case;
- a `<testsuite>` that declares more errors or failures than its test cases show, or holds an `<error>` of its own
  (a fixture, class or module setup that failed);
- a runner that exited non-zero, or timed out, while its report shows no failing test case. The template `test.sh`
  records each group's exit code in `/logs/verifier/<group>.rc`;
- where no exit code is recorded: a load failure in the runner's log (collection error, build failure, failed suite).

Each such failure appears in `results.json` as `<group>::setup error (...)` and in `setup_errors`, so the gate's
oracle run fails on a setup error at build time. Re-scoring the 1,092 graded runs recorded by 2026-10-27 with the template
gives the same reward for every run.

## The lint

```
python3 -I common/lint/task_lint.py tasks/<slug> [--repo <checkout>]
python3 -I common/lint/task_lint.py --all tasks --repo-root ~/.tb-graders/cwe/work --out lint-out
python3 -m pytest common/lint/tests
```

`--repo` (or `--repo-root` with `<slug>/repo` or `<slug>/src` checkouts) lets stand-ins be compared member by member
with the real classes. `--all` writes one JSON report per task and `SUMMARY.md`.

| Finding | Severity | What it looks for |
|---|---|---|
| `scoring` | warn | The task's own `score.py`, run against synthetic results, scores a grading outcome too well (setup errors, a crashed runner, skipped or unreadable reports, an empty group) |
| `refusal-not-accepted` | warn | A security test drives internal code directly with no refusal handling, while other security tests of the task accept a refusal and the instruction allows refusing |
| `stand-in-class` | warn / info | A test file declares a product class. With the repository: the public members of the real class that the stand-in lacks |
| `layer-replaced` | warn / info | The harness replaces a product module (a relative mock, a product `sys.modules` entry, a proxy): a correct fix inside it is not observed |
| `network-layer` | warn | A fake network replaces `fetch` or one HTTP client but not name resolution and connections |
| `hosts-loopback` | warn / info | `test.sh` maps a name to a loopback address; a warning when functional tests treat that name as an ordinary host |
| `workspace-tests` | warn | The project's own tests run from `/workspace`, which the agent can edit, without being restored from `/tests` |
| `hypothesis-deadline` | warn | A Hypothesis `@given` test with the default 200 ms deadline (including the project's copied tests) |
| `timing-assertion` | info | A wall-clock limit inside an assertion |
| `dependency-mock` | info | A mocked library: it must offer every export a correct fix may use |
| `direct-drive` | info | A security test with no entry point: the instruction should name the layer it drives |
| `custom-report` | info | A custom JUnit writer: it must record a test file that fails to load as an error |
| `runner-exit-ignored` | info | `test.sh` does not record the runner's exit code |

The builder runs the lint before the gate and fixes every warning, or records in `notes.md` why it does not apply
(`common/builder/TASK-BUILD-PROMPT-v1.md`, Tests).

## Layer-neutral harnesses

Where the lint reports `layer-replaced` or `network-layer`, the fairness review confirms that a correct fix placed
inside the replaced component is still observed. If it is not, the stand-in moves below that component, as in a
fake network that answers name resolution and connections rather than `fetch`.
