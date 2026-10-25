# Trial runs made off the VM (ext-actions-* jobs)

`common/audit/audit_results.py` reads only trial folders under `~/.tb-graders/cwe/jobs`. Runs made on GitHub
Actions are imported into that folder as `ext-actions-<source>-<model>-a<N>` jobs, so that the ledger stays the one
source of verdicts. Each job folder has an `EXTERNAL.md` naming its source artifact.

What an imported run contains: Harbor's `config.json`, `result.json`, `verifier/results.json`, `verifier/reward.json`
and the small harness logs (`job.log`, `trial.log`, `harbor-stdout.log`). The Actions artifact did **not** keep the
final code or the agent transcript. Their post-run audits (`postmortem-*/`) were made from the tests, the grading
output, the logs and the build records, with an addendum to the auditor brief saying so (project-owner rule,
2026-10-25: missing code or transcript is not by itself a reason to distrust a run).

## Imported 2026-10-25

| Jobs | Source | Why |
|---|---|---|
| `ext-actions-pv-<task>-{deepseek,mimo}-a*` (47 runs, 7 tasks) | precision_validation trials (arm A: pv-quarkus, pv-spring-ws; arm B: pv-svgo, pv-pacioli, pv-device-builder, pv-nx, pv-apostrophe) | both models failed 3/3 there; tasks copied to `tasks/pv-*`, build records to `build/pv-*` |
| `ext-actions-atrisk-yamcs-ds-{deepseek,mimo}-a1` | precision_validation at-risk re-trial `ta06` | both models solved the delivered package `yamcs-subscription-authz-bypass` (built from yamcs-ds) |
| `ext-actions-atrisk-knowns-ds-mimo-a2` | at-risk re-trial `ta04` | MiMo solved the delivered package `knowns-memory-id-path-injection` (built from knowns-ds) |

The at-risk runs graded the **delivered** packages, whose checksums differ from the VM's last yamcs-ds / knowns-ds
runs. Their `config.json` / `result.json` task path was pointed at the VM task name; the original path is kept in
`config.task.imported_original_path`. knowns MiMo `a1` (0.8571) was not imported: MiMo's `a2` solve decides MiMo.

Raw artifacts (decrypted): `~/.tb-graders/cwe/precision_validation/trial-logs/` on the Mac. Actions keeps the
encrypted originals for 7 days only.
