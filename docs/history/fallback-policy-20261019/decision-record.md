# Decision record: what was dropped or narrowed after the 2026-10-16 stops

| # | What | Decision | Why | Cost |
|---|---|---|---|---|
| 1 | Framework scout: an open-ended search for new weaknesses across large frameworks, with no published advisory as the starting point | Fallback | Stopped by the classifier | Real: a narrower pool of hosts |
| 2 | Second jackson-databind task, on its polymorphic type validator | Paused, to be done later | The builder brief was stopped | One candidate task fewer |
| 3 | Exploit-level detail in briefs, notes and write-ups | Fallback, to be done later | Long exploit-level text was stopped repeatedly | None to task quality: the hidden tests hold the detail |
| 4 | Handoff file with full lessons | Shortened to pointers (`builder/NEXT-STEPS.md`) to be extended later | The longer version was stopped mid-write, Nothing lost: the detail is in the files it points to | `builder/BRIEF-trap-stack.md`, `RESULTS.md`, `research/` |
| 5 | Porting Hadi's weakness report onto new injected bugs (turn 255) | paused as a separate brief, to be done later | Stopped | Large, we lost a useful pattern. Hadi's shape, in `builder/BRIEF-trap-stack.md` and in both v1 prompts |

Not changed by the stops:
- the gate;
- the test rules;
- the acceptance bar (both models fail 3 finished attempts; timeouts never count);
- the fairness checks (blind fix, fairness review);
- the audit of every graded run.
