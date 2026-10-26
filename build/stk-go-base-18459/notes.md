# stk-go-base-18459 — build notes (ABANDONED before build)

- Start (UTC): 2026-10-26T12:19:48Z
- End (UTC):   2026-10-26T12:31:00Z
- Advisory: GHSA-mqq6-462x-jxmm / CVE-2026-48031 / GO-2026-5515 — `dhax/go-base`, CWE-798
  ("Hardcoded JWT Secret \"random\" Allows Token Forgery").
- Pinned: `b726356599e17917d41f1e4f2b2fd9276b2037c2` (first parent of the fix).
  Published fix: `cc82b9740fa6b08e0fad409cd4b418e240dd0e00`.
- Track: stacked H4, slug `stk-go-base-18459` (+ `-control`). Reader record:
  `pipelines/stacking/out/reader-ds/h4-18459.json` (the addendum names
  `pipelines/stacking/out/reader/h4-18459.json`; that path does not exist, the record is under
  `reader-ds/`). Stack score for this candidate: 0.22, flagged `single-trap-carries`.

## Outcome

**STOP — the pinned tree supports only two independent concepts inside this advisory's
protection; a stacked task needs three.** No `tasks/stk-go-base-18459/` tree, no control task, no
check patches, no Pattern-B register rows and no gate stage were produced. The base code was not
modified to manufacture a third lever.

## Verified on the pinned tree (facts, not inferences)

- The flaw reproduces through a real entry point. With `auth_jwt_secret` set to a weak non-sentinel
  value, `pwdless.NewResource` (`auth/pwdless/api.go`) builds, the real `/auth` router mounted by
  `api.New` accepts a refresh JWT signed with that weak value, and `POST /auth/refresh` answers
  200 (`httptest` probe with the in-tree `MockAuthStore`/`MockEmailer`, secret `changeme`).
- `jwt.NewTokenAuth` (`auth/jwt/tokenauth.go:21-31`) special-cases only the exact literal `random`
  (`:23-25`) and passes any other value to `jwtauth.New("HS256", []byte(secret), nil)` (`:28`).
- `gendoc` really does crash on a nil router: `docgen.MarkdownRoutesDoc(nil, …)` panics with a nil
  pointer dereference (run with docgen v1.3.0). `cmd/gendoc.go:50` discards `api.New`'s error and
  hands the nil `*chi.Mux` to `:52`.
- Viper ignores a set-but-empty environment value: with `viper.SetDefault("auth_jwt_secret",
  "random")` and `AUTH_JWT_SECRET=` the resolved value is `"random"` (checked directly). An empty
  *config-file* value does resolve to `""`; only the environment path is absorbed by the default.
- A validation-first guard in the constructor closes the shipped default route **without any edit to
  `cmd/serve.go`**: a process that imports `cmd` (so `init()` registers
  `viper.SetDefault("auth_jwt_secret", "random")`) and configures nothing resolves the secret to
  `"random"`, and `jwt.NewTokenAuth()` returns the weak-secret error. This is the finding that
  settles the concept count (below).
- Upstream history (clone of `dhax/go-base`, read-only): the fix's own follow-up `c55f0df` had to
  change the in-tree harness value at `auth/pwdless/api_test.go:34` from `"random"` to a strong
  string; `84b616a` removed the `cmd/serve.go` default. `cmd/gendoc.go` is still unchanged on
  `master` (the discarded error is genuine, unmodified upstream code).

## Why the stack cannot reach three concepts (build rule 1)

The rule: "If one guard or one fix site would close two traps, they are ONE concept. Count your
reference fix's independent edit sites."

| reader trap | independent security edit site? | why |
|---|---|---|
| T1 weak/blank/short/known secret accepted (`auth/jwt/tokenauth.go:22-28`) | **yes** — the validation | the advisory's own route |
| T2 shipped `random` default (`cmd/serve.go:35`, `dev.env:10`, `Dockerfile:18-26`) | **no** | a validation that rejects `random` (any length rule does) makes zero-config `serve` refuse; verified in-process above. A `cmd/serve.go` edit is behaviourally inert once T1 is fixed. Its only behavioural content is the *shape* "the shipped default literal", covered by T1 |
| T3 harness value `"random"` (`auth/pwdless/api_test.go:34`) | **no** | a coupled must-keep-working value, not a missing protection; its regression is a functional failure (upstream's `c55f0df` is the proof) |
| T4 discarded `api.New` error (`cmd/gendoc.go:50-52`) | **yes** — the call-site error handling | distinct judgement ("gendoc is not the server"); panics once T1 can fail |
| T5 commented compose example (`docker-compose.yml:16`) | **no** | not runtime behaviour; no behavioural test can fail on it |
| T6 silent config-load fallback (`cmd/root.go:48-63`) | **no** | the fallback value is the same shipped default, so T1's guard closes it; with a strong secret configured the load failure has no security effect |
| T7 Postgres DSN default (`database/postgres.go:17`) | out of scope | a different credential property; the advisory is specifically the JWT signing key |
| T8 second signer construction site | **no** | no call site exists in the pinned tree; injecting one would test the same guard |
| T9 login-token length default (`cmd/serve.go:33`) | out of scope | not the JWT signing key; no HTTP path accepts an empty token |

So the reference fix has exactly two independent security edit sites — the constructor guard and the
`gendoc` call site. There is no third place in this repo that (a) issues or verifies a JWT, (b) reads
`auth_jwt_secret`, or (c) consumes the auth resource: `jwtauth.New` is called once, `NewTokenAuth`
has one production consumer (`pwdless.NewResource`), `api.New` has two callers (`serve`, `gendoc`),
and only `gendoc` mishandles the error (`serve` already fails closed via `log.Fatal`).

Emitting three groups to satisfy `check_stack.py` would mean asserting that T1 and T2 are independent
when a single guard closes both — a misstatement of the tree, so the task was not built.

## What would have made it buildable

- A third real, in-scope protection, e.g. a second signer construction path in the pinned tree that
  the shared guard does not reach. The tree has none.
- Or a different advisory on the same repo whose protection spans two credentials/properties (the
  Postgres DSN is a real CWE-798 instance but not this advisory's).

## Alternatives considered and rejected

- **Ship concepts [T1], [T2], [T4] anyway.** Rejected: T2 has no independent edit site and no
  behavioural test that a T1-only fix fails; its `miss_T2` patch would be real but the concept claim
  would not be, and a `miss_T1` patch would fail both T1 and T2 tests.
- **Count T3 as a concept.** Rejected: it is the coupled must-keep-working value next to T1; the
  stacked rules classify such values as functional tests, and a `security_fail` check for it cannot
  exist (the regression is a red project suite, not a security-test failure).
- **Count T7 (Postgres `postgres:postgres`) as the third concept.** Rejected: different credential
  property, outside this advisory; also breaks the documented `docker compose up` workflow.
- **Inject a sibling (screener O8b idea 1/2).** Rejected: a second signer site or a second
  error-discarding command is the same guard / the same consumer concept ("more routes of one
  concept"), and it would fabricate the finding rather than expose one at the pinned commit.
- **Build only the two real concepts.** Rejected: `check_stack.py` requires >= 3 groups; shipping
  a two-concept "stack" is a weaker task by construction.

## Unverified / guesses

- The zero-config `serve` process-level behaviour (listening on :3000) was not run: `api.New` calls
  `database.DBConn()` → `checkConn` first, so it needs a live PostgreSQL. The refusal conclusion is
  from the in-process constructor probe plus the `api.New` error path, not from a running server.
- `go-base gendoc -r` was not run end to end; the nil-router panic was verified directly against
  docgen v1.3.0, and the call path (`api.New` error → discarded → nil router) is read from source.
- Whether `serve` with an empty config-file value and the shipped default behaves as tracked
  (config-file `""` beats the default) was inferred from viper's documented precedence, not run.
- The upstream follow-ups (`84b616a`, `c55f0df`) are on `master`, not part of the advisory's
  referenced fix commit `cc82b97`; which of them the pipeline counts as "published fix commits"
  was not decided because nothing was built.

## Outside scope, one line

`auth/pwdless/logintoken.go` has a login-token concurrency defect fixed later in `45be02c`
(CWE-362), and the later commits are dependency bumps — neither is this advisory's protection.

## Scratch

`~/.tb-graders/cwe/work/stk-go-base-18459/` (clone, pinned worktree, probe programs). Nothing in the
source repository was modified and nothing was committed.
