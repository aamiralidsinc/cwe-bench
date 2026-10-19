# Decision record: what was dropped or narrowed after the 2026-10-16 stops

Status: blocked folder; read `BLOCKED.md` first. Mechanisms are described at the level of the
decision only.

| # | What | Decision | Why | Cost | Replaced by |
|---|---|---|---|---|---|
| 1 | Framework scout: an open-ended search for new weaknesses across large frameworks, with no published advisory as the starting point | Dropped | Stopped by the classifier; unresolved disclosure question | Real: a narrower pool of hosts | Pattern B, scoped to one published advisory's own protection (`builder/PROMPT-TEMPLATES-SPEC.md` §1.5), plus the v4-draft re-rank of the 1,462 published advisories (`sourcer/rerank-v4-draft/`) |
| 2 | Second jackson-databind task, on its polymorphic type validator | Dropped, never retried | The builder brief was stopped | One candidate task fewer; the bar for the others is unchanged | Hosts from the screener (`builder/SCREENER-PROMPT-v1.md`) |
| 3 | Exploit-level detail in briefs, notes and write-ups | Narrowed to one line per mechanism | Long exploit-level text was stopped repeatedly | None to task quality: the hidden tests hold the detail | The summary-level rule in both v1 prompts |
| 4 | Handoff file with full lessons | Shortened to pointers (`builder/NEXT-STEPS.md`) | The longer version was stopped mid-write | None: the detail is in the files it points to | `builder/BRIEF-trap-stack.md`, `RESULTS.md`, `research/` |
| 5 | Porting Hadi's weakness report onto new injected bugs (turn 255) | Not done as a separate brief | Stopped | Small: the lesson is already in the builder brief | Hadi's shape, in `builder/BRIEF-trap-stack.md` and in both v1 prompts |
| 6 | Model comparison for the scout (DeepSeek against MiMo) | Moved to the screener | The scout launch was stopped | None: the same comparison applies to the screener | The model comparison protocol in `builder/SCREENER-PROMPT-v1.md` |

Items 5 and 6 come from the history file (turns 255–257 and 309–314). Items 1–4 come from the
assessment (`assessment-2026-10-16.md`).

Not changed by the stops:
- the gate;
- the test rules;
- the acceptance bar (both models fail 3 finished attempts; timeouts never count);
- the fairness checks (blind fix, fairness review);
- the audit of every graded run.
