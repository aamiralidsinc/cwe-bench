# stk-spark-2338 build notes

- Started: 2026-10-26T02:04:09Z (build/stk-spark-2338/start_utc.txt; first pinned-source fetch at 02:04:34Z).
- Ended: see the last section (UTC), filled after the gate stages.

## Shape

Stacked task (reader pattern H4) on `apache/spark`, pinned at
`dc5bb9641b6e6fb8f55b1c524b3a21d4b5063283` (verified via GitHub API as the first parent of the
master fix `e739b7d349dbd41b78d49bc8086cab63db057e14`; `3c83c2c6a22fe384280b99bb753b14800b7e27e1`
is the same change cherry-picked to branch-4.1). The task is the history server's client-side
listing page (`core/src/main/resources/org/apache/spark/ui/static/historypage.js` plus `utils.js`).
The reference fix is the published fix plus the four uncovered sibling sinks.

## Levers (one line each)

- T1 (advisory route, published fix) - `historypage.js:154,194` / `utils.js:276-287,238-247` - the
  application name is assigned raw; a long name's expanded details `<pre>` receives the same raw
  value. Reason to dismiss: none (the report names it).
- T2 (uncovered upstream, deepseek) - `historypage.js:209` - the Spark user is a bare DataTables
  `data:` column, written as HTML. Reason to dismiss: the report is about names and the framework
  supplies the user, so the column looks out of scope.
- T3 (uncovered upstream, both) - `historypage.js:189,149-157,214,81-94` - the app id is in the
  title attribute, anchor text, attempt/log addresses and the `appid-numeric` sort key. Reason to
  dismiss: ids look cluster-manager generated and must stay raw for links and sorting.
- T4 (uncovered upstream, deepseek) - `historypage.js:199,149-157` - the attempt id is in the text
  and the attempt/log addresses. Reason to dismiss: attempt ids look resource-manager owned.
- T5 (uncovered upstream, both) - `historypage.js:184` - the Spark version is a bare `data:`
  column, read from the event log's log-start header. Reason to dismiss: the version looks like a
  build constant that can never carry attacker input.

Concepts: `{T1} {T2} {T3} {T4} {T5}` (five independent edit sites in the reference: name-before-
abbreviation, the user render, the version render, the app-id render, the attempt-id render).

## Verified

- Pinned source facts: `attempt.name`/`attempt.attemptId`/`attempt.sparkUser`/`attempt.appSparkVersion`
  all come from the parsed event log (`FsHistoryProvider.scala` `AppListingListener`,
  `JsonProtocol.applicationStartFromJson`, `logStartFromJson`), so every tested value is
  attacker-influenced; the sink is the browser table.
- The published fix touches only `historypage.js` and escapes the name at the data layer before
  abbreviation. No regression test exists between the pinned and fix commits.
- Behavioural harness: the real page module is imported as an ES module into jsdom with the
  project's own vendored jQuery 3.7.1, DataTables 1.13.11, rowsGroup plug-in and Mustache
  (copied from the pinned tree into `tests/support/vendor`); only `$.getJSON` (listing) and `$.get`
  (template) are answered. The real DataTables configuration, render functions and sort plug-ins
  produce the DOM the cases inspect.
- Local suite results (pinned vs reference): security 0/8 vs 8/8; functional 10/10 on both.
  Per-check results (security / functional):
  reference 8/10, alt_correct_fix 8/10, hardening 8/10, upstream_fix 2/10,
  miss_concept_t1 6/10, miss_concept_t2 7/10, miss_concept_t3 5/10, miss_concept_t4 5/10,
  miss_concept_t5 7/10, check_after_adjustment 7/10, malformed_identity 6/10,
  crash_as_refusal 0/10, functional_overbroad 8/7, refuse_all 2/8.
- The project's own `ui-test/tests/utils.test.js` passes at the pinned commit with
  `NODE_OPTIONS=--experimental-vm-modules npx jest --ci tests/utils.test.js` (checked on the
  extracted pinned tree) and is re-run in the functional group through a Jest-compatible shim.
- `check_stack.py`: conforming (5 concepts, pattern H4). Static gate passes for both
  `stk-spark-2338` and its control.

## Register rows (pattern B)

Appended to `build/audit/uncovered-routes.tsv`: T2, T3, T4, T5, all `real_upstream=yes`,
`present_in_latest=yes` (current master escapes all five; the advisory fix does not),
`public_upstream_report=unknown`, `disclosure_status=pending client decision`.

## Could not verify / open points

- `present_in_latest` is read from current `master` on 2026-10-26; the exact upstream commit is
  not pinned in the register note beyond "current master".
- Whether a public advisory covers the four sibling sinks is unknown; the register says `unknown`.
- The blind fix, `FAIRNESS.md` and the listing review are produced after this build by the
  surrounding pipeline; `blind.patch` is listed in the manifest but intentionally not written here.
- The server-side `scala.xml` pages (Master/Worker UI) also display the application name but are a
  separate sink and are not part of this task. `utils.js:detailsUINode` also serves
  `errorMessageCell` (stage/task error summaries), a separate advisory; only its use through
  `stringAbbreviate` is tested.
- The environment image uses `/workspace` as the agent tree (the template/conformance workdir) and
  keeps a pristine source copy at `/app` for the out-of-band blind-fix harness.

## Gate stages

- `--only static`: PASSED (stacked and control).
- `--only nop`: PASSED - 8 security tests all fail on the pinned code, 10 functional tests all pass
  (verifier `results.json`: security 0/8, functional 10/10, reward 0.0).
- `--only oracle`: PASSED - 3 reference-fix runs, reward 1.0, identical results.
- `--only patches`: running.
- control task: static PASSED; nop/oracle/patches pending.

The shared VM was under very heavy Docker load (load average 60-110, ~7k images) throughout; a
single Harbor teardown (`docker compose down`) took 7+ minutes, so each stage is slow for reasons
outside the task. The verifier's own test run takes seconds.
