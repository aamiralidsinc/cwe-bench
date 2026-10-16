## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 4 of 25 tagged tasks broke at least one model (16%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 7 | 1 | 1 | 1 | 4 | USE: 43% break rate vs 16% baseline (hono, @modelcontextprotocol/sdk, undici) |
| 2 | Already-protected-looking code | 3 | 0 | 1 | 0 | 2 | USE: 33% break rate vs 16% baseline (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 2 | 0 | 1 | 0 | 1 | too few uses to judge (@modelcontextprotocol/sdk) |
| 4 | One test per variant | 25 | 1 | 2 | 1 | 21 | BASELINE (in 25/25 tasks): necessary, not sufficient (hono, @modelcontextprotocol/sdk, nltk, undici) |
| 5 | Boundary-hugging functional tests | 23 | 1 | 2 | 1 | 19 | BASELINE (in 23/25 tasks): necessary, not sufficient (hono, @modelcontextprotocol/sdk, nltk, undici) |
| 6 | Behavioural report, no localization | 25 | 1 | 2 | 1 | 21 | BASELINE (in 25/25 tasks): necessary, not sufficient (hono, @modelcontextprotocol/sdk, nltk, undici) |
| 7 | Parallel implementation | 5 | 1 | 0 | 1 | 3 | USE: 40% break rate vs 16% baseline (hono, undici) |
| 8 | Second public API / input-shape variants | 20 | 1 | 1 | 1 | 17 | BASELINE (in 20/25 tasks): necessary, not sufficient (hono, nltk, undici) |
| 9 | A "must keep working" clause that argues against the fix | 9 | 1 | 1 | 0 | 7 | neutral: 22% break rate (hono, @modelcontextprotocol/sdk) |
| 10 | Prefer big fixes | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._
