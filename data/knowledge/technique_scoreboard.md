## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 4 of 24 tagged tasks broke at least one model (17%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 6 | 1 | 1 | 1 | 3 | USE: 50% break rate vs 17% baseline (hono, @modelcontextprotocol/sdk, undici) |
| 2 | Already-protected-looking code | 2 | 0 | 1 | 0 | 1 | too few uses to judge (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 2 | 0 | 1 | 0 | 1 | too few uses to judge (@modelcontextprotocol/sdk) |
| 4 | One test per variant | 24 | 1 | 2 | 1 | 20 | BASELINE (in 24/24 tasks): necessary, not sufficient (hono, @modelcontextprotocol/sdk, nltk, undici) |
| 5 | Boundary-hugging functional tests | 22 | 1 | 2 | 1 | 18 | BASELINE (in 22/24 tasks): necessary, not sufficient (hono, @modelcontextprotocol/sdk, nltk, undici) |
| 6 | Behavioural report, no localization | 24 | 1 | 2 | 1 | 20 | BASELINE (in 24/24 tasks): necessary, not sufficient (hono, @modelcontextprotocol/sdk, nltk, undici) |
| 7 | Parallel implementation | 5 | 1 | 0 | 1 | 3 | USE: 40% break rate vs 17% baseline (hono, undici) |
| 8 | Second public API / input-shape variants | 19 | 1 | 1 | 1 | 16 | neutral: 16% break rate (hono, nltk, undici) |
| 9 | A "must keep working" clause that argues against the fix | 8 | 1 | 1 | 0 | 6 | USE: 25% break rate vs 17% baseline (hono, @modelcontextprotocol/sdk) |
| 10 | Prefer big fixes | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._
