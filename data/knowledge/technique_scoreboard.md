## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 7 of 41 tagged tasks broke at least one model (17%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 21 | 3 | 2 | 1 | 15 | USE: 29% break rate vs 17% baseline (apprise, hono, gitpython, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 6 | 1 | 1 | 0 | 4 | USE: 33% break rate vs 17% baseline (gitpython, @modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/41 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 39 | 3 | 3 | 1 | 32 | BASELINE (in 39/41 tasks): necessary, not sufficient (apprise, hono, gitpython, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/41 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 10 | 3 | 0 | 1 | 6 | USE: 40% break rate vs 17% baseline (apprise, hono, gitpython, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/41 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 17 | 3 | 2 | 0 | 12 | USE: 29% break rate vs 17% baseline (apprise, hono, gitpython, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 1 | 1 | 0 | 0 | 0 | too few uses to judge (but broke both models) (gitpython) |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._
