# stk-rancher-15705 build notes

Start (UTC): 2026-10-26T02:23:42Z
End (UTC): pending

## Levers

- **T1** (published fix site; both): the GitHub App provider's team derivation returns every team of every organization the user appears in instead of the team slugs recorded for that user (`pkg/auth/providers/githubapp/github_data.go:119-131`). Reason to dismiss: the org-level filter and the doc comment look like the intended membership boundary, and the pinned test asserts the over-inclusive result.
- **T1b** (shape trap on the same guard; both): after walking the member slice, each slug must resolve against its own organization and an unknown slug must be skipped (`github_data.go:124-125,205-210`). Reason to dismiss: the remaining choices look mechanical.
- **T3** (uncovered upstream; deepseek): a refresh that errors restores the previously stored principal set and writes it back (`pkg/auth/providerrefresh/refresher.go:260-288`). Reason to dismiss: it is deliberate resilience so a transient outage does not lock users out.
- **T4** (uncovered upstream; deepseek): request authorization falls back to the token's persisted group principals when the UserAttribute has no entry for the token's provider (`pkg/auth/requests/authenticate.go:206-226`). Reason to dismiss: it is labelled a legacy fallback and every login normally writes a provider entry.
- **T5** (coupled must-keep-working; mimo): team discovery for granting and the full team list stay membership-blind (`github_data.go:147-159,300-348`); an over-hardening fix fails functionally.

Concepts: C1 = {T1, T1b}; C2 = {T3}; C3 = {T4}. T5 is the coupled functional value next to C1.

## Verified

- Pinned and reference trees both build; project tests for `githubapp`, `providerrefresh`, `requests` pass at the pinned commit and on the reference fix.
- On the pinned tree every hidden security test fails and every hidden functional test passes (local run). On the reference fix all pass.
- Every `checks/*.patch` was applied to a pristine pinned tree and run locally: `miss_c1`, `miss_c2`, `miss_c3`, `shape_wrong`, `upstream_fix` leave a security test failing with all functional tests (including the graded project group) passing; `overhardened` and `refuse_all` leave a functional test failing; `alt` and `hardening` pass everything.
- `upstream_fix.patch` is the final tree of both published commits (feature commit plus its JSON-merge-patch repair). It leaves T3 and T4 failing, so the stack adds beyond upstream.
- Current `origin/main` was read only: the T1 derivation is fixed there, while the T3 retention branch and the T4 token fallback are still present (checked 2026-10-26).

## Not verified / unknowns

- The reader's startup stored-state migration (T2) is not graded: its protection is new code whose name a solver would have to guess, and no pinned exported entry point exposes it. The gradeable request-time counterpart is T4.
- Whether the two target models actually fail all three attempts is a trial question, not a gate question.
- The reader's T4 "reachable in production" claim is a code-shape judgement: a token with an empty provider field, or a UserAttribute created before the provider's first login, reaches the fallback. Both are legitimate persisted states; no pinned request handler was driven end to end.
- The pinned `githubapp` data test encodes the pre-fix expectation, so it is not part of the graded project group (the reference patch corrects it, as upstream did).

## Scope note

Only the GitHub App team/group membership path in `rancher/rancher` at the pinned commit was built on. The non-App `github` provider (`getTeams` uses the membership-scoped `/user/teams` endpoint) was examined as a possible second implementation and left alone: it has no equivalent defect at the pinned commit, and turning it into one would be a planted bug outside the advisory.
