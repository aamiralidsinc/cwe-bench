# Breaker class: real bug, outside the advisory and outside the upstream fix (origin `uncovered_upstream`)

Recorded 2026-10-25 at the user's request. A trap with manifest origin `uncovered_upstream` is a real,
reachable defect of the same kind as the reported one, which the advisory does not mention and the
upstream fix does not close (checked against the published fix; we cannot prove nobody ever reported
it privately). The instruction covers it only through its general property.

## Where this class decides the result (audited runs, 2026-10-23 .. 10-25)

| Task | Trap | The bug | Decided |
|---|---|---|---|
| stk-dagu-ghsaph8x | T6 | git-sync pull URL-decodes a repository entry name (`%2E%2E%2Fevil.yaml`) and writes it outside the DAGs directory (internal/gitsync/service.go) | both models, all 6 runs |
| stk-filebrowser-ghsa8wc8 | T4 | recursive copy builds each child destination lexically; a child link escaping the scope is overwritten (fileutils/dir.go, file.go) | both models, all 6 runs (5 of 6 blocked the write but returned 500) |
| stk-gitpython-ghsawvpp | T5 | the ls-remote blocklist omits `--exec`, git's documented alias of `--upload-pack` (git/cmd.py) | DeepSeek, all 3 runs (MiMo failed earlier traps T1/T2) |
| stk-senaite-core-4280 | T9 | the read route calls any zero-argument method the caller names (`load_method_values`), bypassing Zope security; real writers include Client.remove_group / create_group, Worksheet.workflow_script_reject | both models, all 6 runs (test fixture uses an invented `refreshTotals`; user reviewing) |
| stk-avideo-ghsawc3f | T5 | a client identifier goes unquoted into the restream log path appended to the executed command (restreamer.json.php) | MiMo, all 3 runs (DeepSeek solved) |
| stk-uri-js-ghsagcv8 | T5 | the parser classifies the scheme before dropping the leading C0/space characters a browser drops | MiMo, all 3 runs (DeepSeek solved) |

Not in this class: stk-mistral-rs-21576 (decided by T5_trusted_local_loaders, a keep-working value,
origin published_fix_far_site).

## Why it matters
4 of the 5 both-model breaker candidates are decided by this class. The models fix the reported route
and its published siblings, then stop; an unreported route reachable from the same property is what
they miss. Fairness question for each: does the general property, read literally, cover the route,
and does the test accept every refusal the instruction allows (dagu's sync test did not; fixed
2026-10-25)?
