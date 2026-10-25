# FAIRNESS validation — pv-nx

Validator role: check the DeepSeek reviewer's GATE_A: NOT_READY claim (build/pv-nx/FAIRNESS.md) and the
independent run audit (~/.tb-graders/cwe/jobs/ext-actions-pv-nx-*/*/postmortem-20261025T171051Z/verdict.json).
No code was run. Read: tasks/pv-nx/instruction.md, every file in tasks/pv-nx/tests/, solution/fix.patch,
environment/injection.patch (for the batch function's error path), build/pv-nx/{manifest.json,notes.md,checks/*.patch,FAIRNESS.md},
the six audit verdicts, each run's verifier/results.json, trial.log and artifacts/manifest.json.

## 1. Are the two tests unfair (does a correct fix fail them)?

### The instruction sanctions refusing this request

- "A cache entry may only ever affect ... the declared outputs of the task it belongs to, each of which must resolve inside the project."
- "Only outputs that resolve outside the project are invalid."
- "nothing else on the machine may be created, changed or deleted. If a request cannot satisfy this, it is refused: the unsafe part is not applied, and the run reports the problem instead of continuing as if it had succeeded."
- "The link is only a pointer: nothing may be written through it." (This is said about an output that *is* a link. Nothing is said about a link already in the workspace on the path *to* an output.)

In both tests `ws/dist` is a pre-existing symlink to `outside`, and the declared output is `dist/payload.js`.
Through that link the output resolves to `outside/payload.js`, which is outside the project, so a literal reader
has an invalid output. The instruction's remedy for that is to refuse and report, which in a napi export means
returning an error (a JS exception). The reference does something else: `create_dir_all_within` deletes the
user's `ws/dist` link and creates a real directory (fix.patch, "such a symlink/file is replaced with a real
directory"). `ws/dist` is neither the cache entry nor the declared output (`dist/payload.js`), so that deletion
is itself hard to square with "nothing else ... deleted". Replacement is defensible expert behaviour, but it is
not the only correct fix, and refusal is the one the instruction names.

### sec-restore: restoring does not write through an existing workspace link — UNFAIR

```js
48  cache.copyFilesFromCache(resultFor(artifact), ['dist/payload.js']);
50  assert.equal(fs.existsSync(path.join(outside, 'payload.js')), false, ...);
52  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'payload.js'), 'utf8'), 'PWNED',
53    'the declared output itself is still restored inside the workspace');
```

A refusing fix throws at line 48 (no try/catch), so the test fails before any assertion. Even without the throw,
line 52 can only pass if the link is replaced. Both mechanisms fail a correct fix. Compare its sibling
"an absolute output outside the workspace is not applied", which wraps the call (`try { ... } catch { /* refusing is an acceptable outcome */ }`, lines 66-70).
The manifest's `crash_as_refusal` entry says "the tests judge the filesystem outcome", which is not true for this test.

### sec-batch: a batch restore does not write through an existing workspace link — UNFAIR (the reviewer is wrong here)

```js
45  cache.applyRemoteCacheResultsBatch(['b2'], [resultFor(artifact)], [['dist/payload.js']]);
47  assert.equal(fs.existsSync(path.join(outside, 'payload.js')), false, ...);
```

The reviewer says the batch twin "accepts refusal". It does not. Line 45 has no try/catch, and the batch function
propagates every per-entry error with `?` (injection.patch, `apply_remote_cache_results_batch`; the reference
keeps that). So a refusal that reports the problem, which is what the instruction requires, throws and fails the
test. The only non-write-through behaviour it accepts is a *silent* skip, which the instruction rules out ("reports
the problem instead of continuing as if it had succeeded"). The run audit is right: both tests fail a correct
refusing fix. The reviewer's "That fix scores 0.9333" is also wrong: a refusing fix fails both tests,
13/15 = 0.8667, which is exactly the score every graded run got.

Leniency only, not unfairness: the batch test passes a silent skip. Neither test checks the link is left intact
on refusal.

## 2. Graded runs — does any fail a fair test?

| run | reward | failing tests | fails a fair test? |
|---|---|---|---|
| deepseek-a1 pv-nx__wg9zozS | 0.8667 | the two link tests only; 13 other security + 8/8 functional pass | not shown |
| deepseek-a2 pv-nx__6GrCdNd | 0.8667 | same two | not shown |
| deepseek-a3 pv-nx__UbYwnjX | 0.8667 | same two | not shown |
| mimo-a1 pv-nx__9LyLCG4 | 0.8667 | same two | not shown |
| mimo-a2 pv-nx__Cha4e3K | 0.8667 | same two | not shown |
| mimo-a3 pv-nx__Rn7oSrk | never graded | — | — |

Every graded run passes every test that is not in dispute. Each run's two failures fit either (a) a real
write-through (fails the fair line 50 / 47 assertion) or (b) a sanctioned refusal (an exception at line 48 / 45).
Nothing saved tells these apart: results.json records only "fail", trial.log holds no verifier output, the
transcript is "(no transcript)", and artifacts/manifest.json lists /workspace with no files kept. So no run is
shown to fail a fair test, and none can count as a breaker failure on the present record.

## 3. Minimal test repair

restore.test.js, lines 48-53:

```js
let refused = false;
try { cache.copyFilesFromCache(resultFor(artifact), ['dist/payload.js']); }
catch { refused = true; /* refusing is an acceptable outcome */ }
assert.equal(fs.existsSync(path.join(outside, 'payload.js')), false,
  'nothing may be written through a pre-existing link in the workspace');
if (!refused) {
  assert.equal(fs.lstatSync(path.join(ws, 'dist')).isSymbolicLink(), false);
  assert.equal(fs.readFileSync(path.join(ws, 'dist', 'payload.js'), 'utf8'), 'PWNED',
    'a restore that does not refuse must still restore the declared output inside the workspace');
}
```

batch.test.js, line 45: wrap the call in `try { ... } catch { /* refusing is an acceptable outcome */ }`; keep line 47 as is.

The reference still passes (no throw, link replaced, `PWNED` restored). `secfail_extraction_only` still fails both
tests (it writes through). `functional_fail_refuse_all` is still caught by the functional group. Re-run the gate's
oracle and patches stages after the edit. The unconditional "nothing outside" assertion keeps the security point.
Optionally (a quality fix, not required): fix the manifest's `crash_as_refusal` line, which is wrong for these
two tests as they stand.

## 4. Can the five runs be rescored from saved per-test results?

No. After the repair, each test's outcome depends on *how* the run's code failed it: an exception with nothing
written outside → pass; a write-through → still fail. The saved results.json has only pass/fail per test, with no
failure messages, JUnit XML, logs or code. So the repaired outcome cannot be derived. Each run is either 1.0
(refused) or 0.8667 (wrote through), and only re-running the trials (or recovering the original Actions workspace)
can settle it.

VALIDATION: CONFIRM_NOT_READY
RESCORE_WITHOUT_CODE: NOT_POSSIBLE
