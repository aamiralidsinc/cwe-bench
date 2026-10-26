# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-go-base-18459`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: 18459; CWE-798 use of hard-coded credentials / weak default secret in JWT sig
- Pinned (vulnerable) commit: b726356599e17917d41f1e4f2b2fd9276b2037c2. Published fix: cc82b9740fa6b08e0fad409cd4b418e240dd0e00.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-18459",
 "pattern": "H4",
 "repo": "dhax/go-base",
 "pinned_commit": "b726356599e17917d41f1e4f2b2fd9276b2037c2",
 "protections": [
  "The HS256 JWT signing key must be strong, non-empty and not a known/default value before jwtauth.New uses it (auth/jwt.NewTokenAuth, auth/jwt/tokenauth.go:21-31).",
  "Every shipped source of auth_jwt_secret (dev.env:10, the cobra viper default cmd/serve.go:35, the compose example docker-compose.yml:16) must not hand out a fixed weak value.",
  "Every caller of jwt.NewTokenAuth must fail closed on its error instead of continuing with a nil/partial auth resource (cmd/gendoc.go:50 vs cmd/serve.go:17-20).",
  "A configuration file the operator explicitly asked for must not fail to load silently into defaults (cmd/root.go:48-63)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "auth/jwt/tokenauth.go:22",
    "auth/jwt/tokenauth.go:23-25",
    "auth/jwt/tokenauth.go:28",
    "auth/jwt/errors.go:11-16"
   ],
   "reason_to_dismiss": "The 'random' sentinel at auth/jwt/tokenauth.go:23-25 already replaces the shipped default with an ephemeral 32-char key, so no default deployment signs with a fixed secret; only an operator who explicitly configures a weak or blank value is exposed.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "auth/jwt/tokenauth.go:22 (viper.GetString(\"auth_jwt_secret\") with no validation)",
    "auth/jwt/tokenauth.go:23-25 (only the exact literal \"random\" is special-cased)",
    "auth/jwt/tokenauth.go:28 (jwtauth.New(\"HS256\", []byte(secret), nil) accepts the empty string and any short value)",
    "auth/jwt/errors.go:11-16 (no weak-secret / too-short error exists)",
    "dev.env:10 (AUTH_JWT_SECRET=random is the only shipped value)"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M5",
   "origin": "advisory_route",
   "locations": [
    "cmd/serve.go:35",
    "Dockerfile:18-26",
    "dev.env:10"
   ],
   "reason_to_dismiss": "The cobra viper default only applies when no dev.env and no env var are present, so it can be argued to be a zero-config development convenience rather than a production route.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "cmd/serve.go:35 (viper.SetDefault(\"auth_jwt_secret\", \"random\"))",
    "cmd/root.go:48-63 (initConfig: config file is optional, env via AutomaticEnv at :58, defaults otherwise)",
    "Dockerfile:18-26 (production stage copies only the binary, templates and public; dev.env is never copied, and CMD is ./main serve at :26, so the viper default is the only source inside the shipped image)",
    "dev.env:10 (the twin value in the shipped config file)"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M11",
   "origin": "uncovered_upstream",
   "locations": [
    "auth/pwdless/api_test.go:34",
    "auth/pwdless/api_test.go:40-44",
    ".github/workflows/test.yml:15"
   ],
   "reason_to_dismiss": "It is test scaffolding rather than an application route, so it can be argued out of an advisory about production signing keys.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "auth/pwdless/api_test.go:34 (viper.SetDefault(\"auth_jwt_secret\", \"random\") is the must-keep-working value)",
    "auth/pwdless/api_test.go:40-44 (NewResource error => fmt.Println + os.Exit(1), so TestMain bails)",
    "auth/jwt/tokenauth.go:23-25 (the sentinel branch is what makes the harness value work)",
    ".github/workflows/test.yml:15 (go test -v ./...), .github/workflows/main.yml:30-32 (test job gates build/deploy)"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "cmd/gendoc.go:50",
    "cmd/gendoc.go:52",
    "api/api.go:41-45"
   ],
   "reason_to_dismiss": "gendoc only writes routes.md; it is not the HTTP server and never issues or verifies tokens, so its configuration was never a runtime route and the published fix left it alone.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "cmd/gendoc.go:50 (api, _ := api.New(false) discards the error)",
    "cmd/gendoc.go:52 (the possibly-nil router is passed to docgen.MarkdownRoutesDoc)",
    "api/api.go:41-45 (pwdless.NewResource error is returned from api.New)",
    "cmd/serve.go:17-20 (the serve path does log.Fatal on the same error, so the two callers disagree)"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M5",
   "origin": "uncovered_upstream",
   "locations": [
    "docker-compose.yml:16"
   ],
   "reason_to_dismiss": "The line is commented out; it is an example placeholder, not a live configuration route.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "easy",
   "type": "deepseek",
   "evidence": [
    "docker-compose.yml:16 (#AUTH_JWT_SECRET: my secret - an 8-char example value of the same property)",
    "cmd/serve.go:35 (the same artefact family: another shipped source of the value)",
    "dev.env:10 (the third shipped source)"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M6",
   "origin": "uncovered_upstream",
   "locations": [
    "cmd/root.go:61",
    "cmd/root.go:48-58"
   ],
   "reason_to_dismiss": "A failed ReadInConfig only suppresses the 'Using config file' banner; viper's defaults are a complete configuration and the constructor still receives whatever value viper resolves.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "cmd/root.go:61 (if err := viper.ReadInConfig(); err == nil { print } - no else, the error is dropped)",
    "cmd/root.go:58 (viper.AutomaticEnv is the only non-file source)",
    "cmd/serve.go:35 (what the loader falls back to)",
    "auth/jwt/tokenauth.go:22 (the check sees the merged value, never the failed load)"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M5",
   "origin": "uncovered_upstream",
   "locations": [
    "database/postgres.go:17",
    "dev.env:5",
    "docker-compose.yml:13",
    "docker-compose.yml:33"
   ],
   "reason_to_dismiss": "The advisory is about the JWT signing key; the Postgres DSN is a local-development convenience, docker-compose sets its own POSTGRES_PASSWORD, so it is a different credential property of the same CWE class.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "database/postgres.go:17 (viper.SetDefault(\"db_dsn\", \"postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable\"))",
    "dev.env:5 (same postgres:postgres credential in the shipped config)",
    "docker-compose.yml:13 (server DSN), docker-compose.yml:33 (POSTGRES_PASSWORD: postgres)"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M1",
   "origin": "injection_room",
   "locations": [
    "auth/jwt/tokenauth.go:15",
    "auth/jwt/tokenauth.go:28"
   ],
   "reason_to_dismiss": "There is no second construction site in the pinned tree; jwtauth.New is called only inside NewTokenAuth, so any bypass is hypothetical.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "auth/jwt/tokenauth.go:15 (JwtAuth *jwtauth.JWTAuth is an exported field)",
    "auth/jwt/tokenauth.go:28 (the only jwtauth.New call, which also passes nil as the verify key)"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M5",
   "origin": "injection_room",
   "locations": [
    "cmd/serve.go:33",
    "auth/pwdless/logintoken.go:35",
    "auth/pwdless/logintoken.go:92-101"
   ],
   "reason_to_dismiss": "The login token length is not the JWT signing key, and no HTTP path accepts an empty token (auth/pwdless/api.go:154-156 requires a non-empty alphanumeric token), so the default of 8 is not a missing secret check.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "cmd/serve.go:33 (viper.SetDefault(\"auth_login_token_length\", 8) sits on the line before the secret default)",
    "dev.env:8 (AUTH_LOGIN_TOKEN_LENGTH=8)",
    "auth/pwdless/logintoken.go:35 (viper.GetInt with no minimum)",
    "auth/pwdless/logintoken.go:92-101 (randStringBytes(n) yields an empty token for n=0 and panics for n<0)"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1"
  ],
  [
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ],
  [
   "T9"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": true,
  "masking": [
   "The sentinel branch at auth/jwt/tokenauth.go:23-25 masks T1: with the shipped default the key is an ephemeral 32-char value, so nothing observable is wrong until a non-default weak, short or blank value is configured.",
   "T4 is masked by T1/T2: cmd/gendoc.go:50's discarded error is harmless while jwt.NewTokenAuth can never fail; once a weak-secret error exists, gendoc feeds a nil router to docgen.MarkdownRoutesDoc at :52.",
   "Emptying dev.env:10 without adding validation would be masked-then-worse: the empty string has no sentinel branch (auth/jwt/tokenauth.go:23 only matches the literal \"random\") and reaches jwtauth.New with a zero-length key at :28.",
   "T6 becomes visible only after T2: while the fallback default is \"random\" the fallback is merely an ephemeral key; if a fix replaces it with a fixed 32-char placeholder, a mistyped --config (cmd/root.go:61) silently serves with a known key."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T3",
   "what": "A strength rule that rejects the literal \"random\" (6 chars) or that runs before the sentinel substitution breaks the must-keep-working harness value at auth/pwdless/api_test.go:34 and TestMain exits at :40-44, failing CI (test.yml:15); the same rule placed after substitution lets the shipped default through unvalidated."
  },
  {
   "a": "T1",
   "b": "T2",
   "what": "Rejecting the default inside NewTokenAuth while cmd/serve.go:35 still supplies \"random\" makes `go-base serve` and the Dockerfile CMD (Dockerfile:26) fail to start with no config; changing the default to a fixed literal instead re-introduces a known signing key."
  },
  {
   "a": "T1",
   "b": "T5",
   "what": "A 32-byte minimum rejects the documented copy-paste value `my secret` at docker-compose.yml:16 and every legacy secret shorter than 32 chars, which is a legitimate existing configuration shape."
  }
 ],
 "fairness_risks": [
  "The must-keep-working value `auth_jwt_secret=random` is seeded in auth/pwdless/api_test.go:34 and is exactly what a naive weak-secret rule rejects; the rule must run after the sentinel substitution or the harness must be updated, and either choice is observable.",
  "A 32-char minimum contradicts the shipped example at docker-compose.yml:16 and dev.env:10 as written, so the rule changes an input shape that the project itself documented as valid.",
  "An operator expressing 'no JWT secret configured' as AUTH_JWT_SECRET= (empty) is currently accepted and produces a zero-length HS256 key at auth/jwt/tokenauth.go:28; refusing it is the right move but changes the accepted input shape.",
  "The local workflow in README.md:37-39 depends on the postgres:postgres default (docker-compose.yml:13,33); any rule that bans hardcoded credentials repo-wide breaks `docker compose up`.",
  "`go-base gendoc -r` is a documented workflow (README.md:64, routes.md) and api.New requires a live DB (api/api.go:28) before the auth resource is built, so a fail-closed secret rule must not turn documentation generation into a startup failure."
 ],
 "effort_minutes": 45,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4"
  ],
  "why": "Four independent judgements at four different files/packages, each with a different dismissal a solver can honestly make: T1 'the random sentinel already makes the default ephemeral', T2 'the viper default is a dev-only convenience' (falsified only by Dockerfile:18-26, which never copies dev.env and runs ./main serve), T3 'it is just test scaffolding', T4 'gendoc is not the server'. T1 is the DeepSeek-shaped trap (absent protection plus a strong dismissal); T3 is the MiMo-shaped coupled value that punishes over-hardening (a rule that rejects 'random' before substitution breaks TestMain and CI, test.yml:15); T2 and T4 are further absent-protection routes the report would not point at. The set also forces the two interactions that make the fix non-mechanical: T1+T2 must land together or serve stops booting, and T1+T3 must be reconciled or the suite goes red. T5 is a reasonable fifth (a commented example that a 32-char rule would reject) but is weaker because it is not testable behaviour; T6/T7/T8/T9 are left out because they are either a different credential property (T7), a hypothetical construction path with no call site (T8), a parameter that no HTTP route can exploit (T9), or a loader nit whose impact depends on the fix chosen for T2 (T6)."
 },
 "unverified": [
  "The published fix commit cc82b9740fa6b08e0fad409cd4b418e240dd0e00 is not present in this worktree; everything said about what the fix changed or left alone comes from the screener record, not from the pinned tree.",
  "viper's handling of an empty env var / an empty config-file value versus a SetDefault value (cmd/root.go:58, auth/jwt/tokenauth.go:22) was not executed; the 'blank value reaches jwtauth.New as an empty key' shape is inferred from the absence of any emptiness check at tokenauth.go:22-28, not run.",
  "Whether docgen.MarkdownRoutesDoc panics on a nil *chi.Mux (cmd/gendoc.go:50-52) is library behaviour and was not run; only the discarded error and the nil hand-off are visible in the pinned code.",
  "Whether the in-tree sentinel branch (auth/jwt/tokenauth.go:23-25) was itself an earlier security fix is unknown; the H3 answers treat it as the earlier mitigation because it is the only pre-existing defence for this property.",
  "api.New calls database.DBConn() (api/api.go:28) before pwdless.NewResource (:41), so any behavioural test of gendoc or serve needs a live PostgreSQL; the auth package tests do not (auth/pwdless/api_test.go:40).",
  ".tool-versions:1 still pins golang 1.18 while go.mod:3-5 declares go 1.24.0 with toolchain go1.24.1; the pinned tree was not built, so buildability under the declared toolchain is unverified.",
  "No shell was available, so repository size and the existence of a later release were not checked; the screener reports repo_mb null and no latest release.",
  "T7 (Postgres DSN credential) is outside the named advisory's credential property and is probably not reachable by hidden behavioural tests; it is recorded as a candidate only and is not part of the recommended design."
 ]
}
  ```
- Published fix sites:   - auth/jwt/tokenauth.go:22 — T1 M4 (reason to dismiss: The 'random' sentinel at auth/jwt/tokenauth.go:23-25 already replaces the shipped default with an ephemeral 32-char key, so no default deployment signs with a fixed secret; only an operator who explicitly configures a weak or blank value is exposed.)
  - auth/jwt/tokenauth.go:23-25 — T1 M4 (reason to dismiss: The 'random' sentinel at auth/jwt/tokenauth.go:23-25 already replaces the shipped default with an ephemeral 32-char key, so no default deployment signs with a fixed secret; only an operator who explicitly configures a weak or blank value is exposed.)
  - auth/jwt/tokenauth.go:28 — T1 M4 (reason to dismiss: The 'random' sentinel at auth/jwt/tokenauth.go:23-25 already replaces the shipped default with an ephemeral 32-char key, so no default deployment signs with a fixed secret; only an operator who explicitly configures a weak or blank value is exposed.)
  - auth/jwt/errors.go:11-16 — T1 M4 (reason to dismiss: The 'random' sentinel at auth/jwt/tokenauth.go:23-25 already replaces the shipped default with an ephemeral 32-char key, so no default deployment signs with a fixed secret; only an operator who explicitly configures a weak or blank value is exposed.)
  - cmd/serve.go:35 — T2 M5 (reason to dismiss: The cobra viper default only applies when no dev.env and no env var are present, so it can be argued to be a zero-config development convenience rather than a production route.)
  - Dockerfile:18-26 — T2 M5 (reason to dismiss: The cobra viper default only applies when no dev.env and no env var are present, so it can be argued to be a zero-config development convenience rather than a production route.)
  - dev.env:10 — T2 M5 (reason to dismiss: The cobra viper default only applies when no dev.env and no env var are present, so it can be argued to be a zero-config development convenience rather than a production route.)
- Uncovered routes to confirm (pattern B):   - auth/pwdless/api_test.go:34 — T3 M11 (reason to dismiss: It is test scaffolding rather than an application route, so it can be argued out of an advisory about production signing keys.)
  - auth/pwdless/api_test.go:40-44 — T3 M11 (reason to dismiss: It is test scaffolding rather than an application route, so it can be argued out of an advisory about production signing keys.)
  - .github/workflows/test.yml:15 — T3 M11 (reason to dismiss: It is test scaffolding rather than an application route, so it can be argued out of an advisory about production signing keys.)
  - cmd/gendoc.go:50 — T4 M1 (reason to dismiss: gendoc only writes routes.md; it is not the HTTP server and never issues or verifies tokens, so its configuration was never a runtime route and the published fix left it alone.)
  - cmd/gendoc.go:52 — T4 M1 (reason to dismiss: gendoc only writes routes.md; it is not the HTTP server and never issues or verifies tokens, so its configuration was never a runtime route and the published fix left it alone.)
  - api/api.go:41-45 — T4 M1 (reason to dismiss: gendoc only writes routes.md; it is not the HTTP server and never issues or verifies tokens, so its configuration was never a runtime route and the published fix left it alone.)
  - docker-compose.yml:16 — T5 M5 (reason to dismiss: The line is commented out; it is an example placeholder, not a live configuration route.)
  - cmd/root.go:61 — T6 M6 (reason to dismiss: A failed ReadInConfig only suppresses the 'Using config file' banner; viper's defaults are a complete configuration and the constructor still receives whatever value viper resolves.)
  - cmd/root.go:48-58 — T6 M6 (reason to dismiss: A failed ReadInConfig only suppresses the 'Using config file' banner; viper's defaults are a complete configuration and the constructor still receives whatever value viper resolves.)
  - database/postgres.go:17 — T7 M5 (reason to dismiss: The advisory is about the JWT signing key; the Postgres DSN is a local-development convenience, docker-compose sets its own POSTGRES_PASSWORD, so it is a different credential property of the same CWE class.)
  - dev.env:5 — T7 M5 (reason to dismiss: The advisory is about the JWT signing key; the Postgres DSN is a local-development convenience, docker-compose sets its own POSTGRES_PASSWORD, so it is a different credential property of the same CWE class.)
  - docker-compose.yml:13 — T7 M5 (reason to dismiss: The advisory is about the JWT signing key; the Postgres DSN is a local-development convenience, docker-compose sets its own POSTGRES_PASSWORD, so it is a different credential property of the same CWE class.)
  - docker-compose.yml:33 — T7 M5 (reason to dismiss: The advisory is about the JWT signing key; the Postgres DSN is a local-development convenience, docker-compose sets its own POSTGRES_PASSWORD, so it is a different credential property of the same CWE class.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4. Why: Four independent judgements at four different files/packages, each with a different dismissal a solver can honestly make: T1 'the random sentinel already makes the default ephemeral', T2 'the viper default is a dev-only convenience' (falsified only by Dockerfile:18-26, which never copies dev.env and runs ./main serve), T3 'it is just test scaffolding', T4 'gendoc is not the server'. T1 is the DeepSeek-shaped trap (absent protection plus a strong dismissal); T3 is the MiMo-shaped coupled value that punishes over-hardening (a rule that rejects 'random' before substitution breaks TestMain and CI, test.yml:15); T2 and T4 are further absent-protection routes the report would not point at. The set also forces the two interactions that make the fix non-mechanical: T1+T2 must land together or serve stops booting, and T1+T3 must be reconciled or the suite goes red. T5 is a reasonable fifth (a commented example that a 32-char rule would reject) but is weaker because it is not testable behaviour; T6/T7/T8/T9 are left out because they are either a different credential property (T7), a hypothetical construction path with no call site (T8), a parameter that no HTTP route can exploit (T9), or a loader nit whose impact depends on the fix chosen for T2 (T6). Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): The must-keep-working value `auth_jwt_secret=random` is seeded in auth/pwdless/api_test.go:34 and is exactly what a naive weak-secret rule rejects; the rule must run after the sentinel substitution or the harness must be updated, and either choice is observable. | A 32-char minimum contradicts the shipped example at docker-compose.yml:16 and dev.env:10 as written, so the rule changes an input shape that the project itself documented as valid. | An operator expressing 'no JWT secret configured' as AUTH_JWT_SECRET= (empty) is currently accepted and produces a zero-length HS256 key at auth/jwt/tokenauth.go:28; refusing it is the right move but changes the accepted input shape. | The local workflow in README.md:37-39 depends on the postgres:postgres default (docker-compose.yml:13,33); any rule that bans hardcoded credentials repo-wide breaks `docker compose up`. | `go-base gendoc -r` is a documented workflow (README.md:64, routes.md) and api.New requires a live DB (api/api.go:28) before the auth resource is built, so a fail-closed secret rule must not turn documentation generation into a startup failure.. Conflicts the reader found: A strength rule that rejects the literal "random" (6 chars) or that runs before the sentinel substitution breaks the must-keep-working harness value at auth/pwdless/api_test.go:34 and TestMain exits at :40-44, failing CI (test.yml:15); the same rule placed after substitution lets the shipped default through unvalidated. | Rejecting the default inside NewTokenAuth while cmd/serve.go:35 still supplies "random" makes `go-base serve` and the Dockerfile CMD (Dockerfile:26) fail to start with no config; changing the default to a fixed literal instead re-introduces a known signing key. | A 32-byte minimum rejects the documented copy-paste value `my secret` at docker-compose.yml:16 and every legacy secret shorter than 32 chars, which is a legitimate existing configuration shape.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-go-base-18459/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-go-base-18459/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-go-base-18459/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-go-base-18459/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-go-base-18459/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-go-base-18459/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-go-base-18459/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-go-base-18459 --only static
python3 -I common/gate/gate.py stk-go-base-18459 --only nop
python3 -I common/gate/gate.py stk-go-base-18459 --only oracle
python3 -I common/gate/gate.py stk-go-base-18459 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-go-base-18459/`;
  - edit only `tasks/stk-go-base-18459/`, `build/stk-go-base-18459/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-18459.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-go-base-18459`. Control task slug: `stk-go-base-18459-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-18459.json`.
