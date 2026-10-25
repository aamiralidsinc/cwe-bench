You are selecting candidates for a security-fix benchmark whose goal is that BOTH target models
(DeepSeek V4.1 Flash and MiMo-V2.6-Pro) fail all three attempts on each task. You will be given a
pool of candidate open-source advisories, one JSON object per line. Score every candidate for
**breaker potential** and return the best 50.

## What makes a strong breaker candidate (score each 0–10)
Models find the code the report points to and diagnose it correctly. They fail on **scope** and on
**over-hardening**. Reward candidates that give room for that:
- **how-type room in the real code** — the strongest lever. Siblings whose fix needs the mechanism understood, not just found: a **producer** (schema, serializer, table builder, config loader) the check never calls, deep in internal machinery; a parser differential on the protected item's identity; a **coupled_behaviour** right next to the hidden value; a route where the protection never existed. These held even when a report stated them.
- **both models covered** — a bonus. The two target models miss different kinds of trap: DeepSeek misses a route where the protection never existed when there is a plausible reason to dismiss it; MiMo over-hardens (it breaks a **coupled_behaviour**) and misses how-type mechanisms. A host whose real code offers at least one trap of each kind scores higher than one that offers only one kind.
- **uncovered_routes** into the same protected sink that the published fix did not touch, especially a real **second implementation** of the same operation in another package or transport, with a believable reason to dismiss.
- **injection_room** (sibling gaps a maintainer could plausibly leave) — an extra only. Planted siblings that are just another entry point or copy were fixed together and rarely missed (5 of 98); never let route count alone raise a score.
- an **out_of_scope_site** that is a second implementation / lower-level API / wrapper / save-reload / defaults-merge route, with real **distance** (another file or package) from the landing point.
- a **coupled_behaviour** that must keep working next to the sink (an over-broad fix then fails — MiMo over-hardens).
- multiple **entry_points** and varied **input_shapes** the general rule covers but a one-case fix misses (minor: pure spelling or encoding variants never made a task hard; a shape counts only when a plausible check mishandles it).

## What lowers a candidate
- **dos** / resource-exhaustion flaws (score ≤ 2).
- **red_flags** such as single_site or tiny_repo.
- a flaw with no uncovered routes and no injection room (one obvious site only) — easy to fix, both models will solve it.
- **fix_minutes** very large (> ~120) or needs services that cannot run offline, a GPU, a kernel or a GUI (buildability risk) — lower the score.
- a candidate that looks already-covered or trivial.

## Output — STRICT
Return ONLY a JSON array (no prose before or after) of the **50 highest-scoring** candidates,
sorted by score descending:
```
[{"entry_id": "1234", "score": 8, "reason": "two sibling gaps at the authz check + coupled list-read; multi-site"}, ...]
```
Each `reason` is one line. Use entry_id values exactly as given. Pick exactly 50 (or all of them if
fewer than 50 are provided). Do not include any candidate you scored ≤ 2.

The candidate pool follows.
