# Round-1 analysis: shared context (2026-10-16)

Goal of the project: Harbor security-fix tasks where pass@3 = 0 for BOTH DeepSeek V4.1 Flash
(`deepseek-flash`) and Xiaomi MiMo-V2.6-Pro (`mimo`), per (task, model) pair. Round 1 is finished:
every pair re-run OFFLINE (model API only, web tools disabled, 2 h limit), every graded run audited by
an Opus sub-agent (postmortem verdict.json), and 16 tasks' tests repaired today (lenient/unfair tests
flagged by audits), with saved solves regraded on the repaired tests.

Final audited standing (build/audit/ledger.md is the source of truth; build/audit_results.py builds it):
36 pairs solved, 1 failed (jackson-databind-sib / DeepSeek 0/6), 1 open (asyncssh / DeepSeek: its only
offline solve failed a new test judged FAIR; fresh runs pending). 0 breakers. trigger-dev's repair is
still running — treat its tests as in flux.

Notable "real defect" findings from today's regrades and fairness reviews (code-level, not test faults):
- asyncssh / DeepSeek r11: guarded `send_pktsize == 0` AFTER the dropbear `-= 1` adjustment, so a peer
  advertising 0 with a dropbear banner gets -1 and the endpoint spins (fairness review: FAIR).
- async-http-client / DeepSeek uGhFbba and MiMo tfkenPc: decoded the caller's Cookie header strictly
  (or quote-aware), so a malformed caller value "names nothing" and the store's same-named session is
  substituted (fairness review: FAIR). MiMo's 3 fresh offline runs all solved it after the repair.
- rclone / DeepSeek r11: fell back to access-key-ID / md5 when the proxy returned no secret.
- argo-workflows r11 (both models): top-level field denylist that ignores spec.templateDefaults.
- webob / MiMo r12: rewrote relative_url('//host') — functional regression.
- jackson-databind-sib / DeepSeek: dismissed the injected any-setter siblings as out of scope in all 6
  runs (the only genuine failure).
- filament / MiMo r11: refused with HTTP 500 instead of 4xx — set aside (rule added after the run).
- cloudreve (both): 16.7 MP thumbnail cap, induced by the instruction's own wording.

Key locations (repo root /Users/dev/terminal-bench/cwe-bench):
- Screener: sourcer/ (README.md, weights.json, weights.v1.json, osv_sourcer.py, stacking_screener.py,
  shortlist-20.tsv, stacking-shortlist.tsv, index/), ALGORITHM.md, taxonomy.md, taxonomy_research.md.
- Taxonomy research: research/*.md (severity_findings, attack_taxonomies_findings, owasp_top10_findings,
  cwe_hierarchy_top25_findings), research/raw/.
- Earlier own-run analysis: research/own-runs/ (FINDINGS.md, task_table.tsv, test_results.tsv,
  lookups.tsv, TEST-REPAIRS.md).
- Tasks: tasks/<task>/ (instruction.md, tests/); build/<task>/ (manifest.json with the candidate row,
  notes.md incl. "2026-10-16 test repair", checks/*.patch, gate_report.json).
- Results: RESULTS.md, build/audit/ledger.md, build/audit/*.tsv (trials.tsv, time_breakdown.tsv,
  excluded_runs.tsv, contaminated.tsv, task_defects.tsv, audit_carryover.tsv, offline_since.tsv).
- Trials: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (result.json, agent/ transcript, verifier/,
  final-code/, regrade-*/REGRADE.json, postmortem-*/verdict.json + POSTMORTEM.json). Folders named
  setaside-regrade-* or jobs named _userstopped-* are deliberately excluded.
- Builder rules: builder/BUILDER.md (§3f-3g); gate: builder/gate.py; trial procedure:
  build/TRIAL-PROCEDURE.md.

Rules: read-only except your own output file(s) under research/round1-analysis/. No web lookups of
these tasks' upstream fixes. Don't start Docker builds, trials or regrades. Small n (≈20 tasks, ≈38
pairs): state uncertainty honestly, never overclaim a correlation.
