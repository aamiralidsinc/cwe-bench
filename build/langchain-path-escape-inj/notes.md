# Build notes — langchain-path-escape-inj

- Start (UTC): 2026-10-18T04:43:44Z
- End (UTC): 2026-10-18T05:11Z (see end_utc.txt for final)

## Task
langchain-ai/langchain, GHSA-GR75-JV2W-4656 / CVE-2026-55443 (CWE-22 / CWE-59):
model-supplied glob/grep patterns and file-tool paths escape the configured
workspace root or an allowed-directory restriction (upward pattern, in-workspace
symlink, or a same-prefix sibling). Pattern A + injected siblings; track
INJECTED. Pinned 0392b6b (verified parent of fix dcaf779). Python runtime +
anthropic partner package.

Shipped `/app` = pinned vulnerable commit + injection.patch (two same-class
siblings in the anthropic file-tool command handlers). Oracle = fix.patch
(published source changes + fixes for both injected siblings).

## Levers (each a different reason to dismiss)
- **T1 base glob (pattern A, report target).** glob pattern + per-match symlink
  with no containment. Reason to dismiss: none; the obvious site. Lever: a
  base-path-only fix misses the pattern and symlink shapes.
- **T2 grep Python fallback (pattern A, 2nd implementation, same file).** symlink
  file content read. Dismiss: "fallback that only runs when ripgrep is missing."
- **T3 filesystem allowed-prefix (pattern A, different package).** raw startswith
  prefix test; `/memories` sibling escape. Dismiss: "partner package, base path
  already root-resolved, so prefix looks cosmetic."
- **T4 state allowed-prefix (pattern A, state-backed variant).** same raw
  startswith in the in-memory store. Dismiss: "in-memory, can't reach disk."
- **S1 injected copy command (filesystem file tool).** new command reads its
  source without containment; in-workspace symlink source leaks an outside file
  into an in-bounds destination. Dismiss: "new convenience command; the write
  destination is validated, so the source read looks internal."
- **S2 injected glob/list command (state file tool).** new listing command filters
  state entries with raw startswith; listing the allowed dir enumerates a
  same-prefix sibling. Dismiss: "a listing convenience over the agent's own state,
  not a security boundary."

## Coupled must-keep-working (over-hardening traps)
In-workspace use preserved: `*.py` / `**/...` globs, regex content search (python
AND default backends), a filename containing a dotted substring (only whole `..`
segments are rejected), in-workspace symlinks whose target is inside root, the
allowed directory itself and nested descendants, in-workspace copy, and the
"nothing found"/"no match" contract. `ff-overbroad` (drops all symlinks) is
caught functionally.

## Verified (offline, no model/network)
- Base flaw and both siblings reproduce through the real public tool interfaces
  at the pinned+inject commit; all 7 security tests fail on inject, pass on oracle.
- All 14 functional tests pass on both inject and oracle trees.
- Project area tests pass on both trees (file_search 32, anthropic_tools 20);
  shipped pristine, run from package roots (mixed-package pytest confuses rootdir).
- All 9 local check patches behave as declared (6 security_fail, 1 functional_fail,
  2 pass incl. project tests); blind.patch + FAIRNESS.md left for downstream.

## Could not verify / guesses / scope
- ripgrep backend containment is a published-fix site but NOT reachable at the
  pinned commit (ripgrep does not follow symlinks by default; base path already
  validated). Its fix is kept in the oracle as harmless defense-in-depth and is
  NOT tested. Noted, not a lever.
- `StateFileSearchMiddleware` grep raw-startswith (screener O8 B lead) over-scopes
  a state search but has no configured root/allowed-prefix boundary, so it
  violates no invariant; confirmed and dismissed, not built (present_in_latest no
  per screener, not re-checked).
- Absolute glob patterns raise on this Python (not a leak) rather than enumerate;
  not used as a security shape.
- The TypeScript/other runtimes are out of scope (Python only).
- `present_in_latest` values taken from the screener, not independently re-checked.
