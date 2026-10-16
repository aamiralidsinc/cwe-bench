# Round 1 under a 60-minute limit (partial-progress exhibit)

Date: 2026-10-16. Source: every round-1 trial (186), read via `build/audit_results.py` (ledger
reproduced exactly), with per-run edit times taken from the agent transcripts.

**What this is, and what it is not.**
- Our acceptance rule stays the same. A failure counts only when the run **finishes and leaves
  the vulnerability open**. A run that times out is never a failure, at any limit. By that rule,
  round 1 has 0 tasks that both models fail.
- This page answers a narrower comparison question. CWE-bench and similar benchmarks give each
  attempt **1 hour** and grade the code as it stands at the limit (arXiv 2610.17020). Which of our
  tasks did a model fail to fix completely within that hour?
- It is evidence of partial progress against those benchmarks' setting, not a set of accepted tasks.
- Our runs had a 2 h limit (60 min before 2026-10-15). The agent is never told its limit, so its
  first 60 minutes match a 1 h run.
- Code at exactly minute 60 was not saved. "Fixed by 60" below means the last source edit of a
  later-graded solve came before minute 60; edits made through shell commands were found by
  pattern matching.

## Pairs with no complete fix within 60 minutes

| Task | Model | Earliest counted solve (min) | Last source edit (min) | Note |
|---|---|---|---|---|
| jackson-databind-sib | DeepSeek | none | – | **Genuine failure, not timing: 0/6, each run finished in 14–18 min** |
| asyncssh | DeepSeek | none counted | – | Only offline graded run scored 0.9167 (audit pending); fresh runs started 2026-10-16 |
| async-http-client | DeepSeek | 64.7 | 64.5 | |
| async-http-client | MiMo | 73.1 (also 76.2, 111.8) | 64.1 | All 3 solves edited past minute 60 |
| asyncssh | MiMo | 95.9 | 93.3 | |
| argo-workflows | MiMo | 77.4 | 70.5 | |
| filament | MiMo | 83.8 | 82.2 | |
| rclone-sib | MiMo | 80.8 | 77.8 | |
| trigger-dev | MiMo | 86.1 | 85.0 | |
| hickory-dns | MiMo | 62.0 | 60.9 | Borderline |
| rclone | MiMo | 63.8 | 59.0 | Was restoring the vulnerable code to test between 59.6 and 60.3, so its code at 60:00 was broken |

Pairs whose only solve came after 60 min but whose last edit came before it (probably solved
within 1 h, so not counted here): ruby-saml/MiMo (63.7, last edit 56.5), stigmem/MiMo (64.6,
last edit 48.1).

## Tasks where neither model had a complete fix within 60 minutes

| Task | Track | DeepSeek | MiMo |
|---|---|---|---|
| **asyncssh** | stacking (6 CWEs) | no counted solve | first solve at 95.9 min |
| **async-http-client** | mined | first solve at 64.7 min | first solve at 73.1 min |

Plus **jackson-databind-sib**, where DeepSeek genuinely fails (finished runs, 0/6) and MiMo
solved at 44 min.

## Summary for comparison with 1-hour benchmarks

- Pairs not fixed within 60 min: **11 of 38**. 10 are the timing cases in the table; the other is
  jackson-databind-sib/DeepSeek, which failed with finished runs.
- Under a 1-hour reading, tasks neither model fixed: **2 of 19** (asyncssh, async-http-client).
- Under our acceptance rule (finished runs only): **0 of 19**. This is the number that counts.
- Speed: MiMo's median solve takes 60 min, against DeepSeek's 23 min. MiMo is slow rather than
  unable. A 1-hour benchmark would score MiMo much lower on these same tasks.

Data: `research/partial-progress-60min/` (`runs.tsv`, `pairs.tsv`).
