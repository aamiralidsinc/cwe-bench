# stk-n8n-node-sqlite3-13223 — build notes

Start: 2026-10-26T12:17:00Z
End:   (updated at the end of this session)

Stacked H4 task on dangerblack/n8n-node-sqlite3. Pinned
8a3493f19a426bd99ea91b2c337978e0488cc1c9 is the first parent of the published fix
145a8876ff12375813bdcd4ae4fe78f460c53a98 ("fix(v1): prevent path traversal via expression
injection on db_path", one line: `noDataExpression: true` on the v1 Database Path property).
The pinned tree already contains the v2 implementation (refactor 0ba678e) and its credential, so
the advisory's own fix leaves the sibling implementation untouched.

The reader record named by the pipeline is `pipelines/stacking/out/reader-ds/h4-13223.json`; the
prompt's `pipelines/stacking/out/reader/h4-13223.json` does not exist in this checkout. The
screener record is `pipelines/stacking/out/screener/13223.json`.

## Levers (one line each)

- **T1 (A, advisory route, both)** — the v1 Database Path is resolved per item and opened; its
  descriptor has no expression rule. nodes/SqliteNode/v1/SqliteV1.node.ts:110-118,193,224.
  Reason to dismiss: none; this is the reported site.
- **T5 (A, same concept, MiMo-type)** — the handler creates the parent directory of the supplied
  path before opening it, so a rejected value still leaves a directory. :208-222. Reason to
  dismiss: relative/absolute literal paths and auto-created parents are ordinary tested behaviour.
  The fix must act before that side effect and keep creating parents for literal values.
- **T2 (A, injection room, DeepSeek-type)** — a second filesystem path nested in the
  `additionalOptions` collection selects the native module better-sqlite3 loads, and its option
  has no expression rule. :176-182,198,62-71,224. Reason to dismiss: it is the bindings binary,
  not the database file, and the only check is existence.
- **T3 (B, uncovered upstream, DeepSeek-type)** — the v2 implementation takes the database path
  from `sqliteCredentials.databasePath`, whose property has no expression rule; the same value is
  opened by execution, the connection check, the table search and the column lookup.
  credentials/SqliteCredentials.credentials.ts:11-19, nodes/SqliteNode/v2/transport/index.ts:15,35,
  v2/actions/router.ts:14-16, v2/methods/{credentialTest,loadOptions,listSearch}.ts. Reason to
  dismiss: an administrator-set credential, not a node parameter; the published fix was fix(v1).

Concepts (manifest.stacking.concepts): `[T1,T5]` (one edit site: the v1 path value must stop
being expression-driven before the open), `[T2]` (the collection option), `[T3]` (the stored
credential plus the four v2 entry points that share it).

## How the protection is behavioural, not metadata-only

`noDataExpression` is not a UI-only flag in the pinned peer. n8n-workflow 2.10.1
(`getNodeParameters`, reached from `Workflow` construction and from the credentials helper) strips
the leading `=` from a value written as an expression when its property declares
`noDataExpression`. The expression engine then requires a leading `=` (`isExpression`), so the
value is never evaluated. This was verified with the real n8n-workflow 2.10.1 package for node
properties, for a collection sub-option, and for credential properties.

The hidden harness therefore uses the real `getNodeParameters` for n8n's load-time handling and a
small expression evaluator only for the run-time forms the suites use (`$json`, `$env`, `$vars`).
It honours `rawExpressions`, so a runtime guard that inspects the stored value is also accepted
(the `alt_correct_fix.patch` proves it).

## Verified in this session

- Pinned tree, locally with the project's own toolchain: security 0/9 pass, functional 58/58 pass.
- Every check variant re-run locally against the hidden suites:
  - `upstream_fix` (published fix alone): security 4/9 (T2 and T3 still open), functional 58/58.
  - `miss_db_path` (T2+T3 fixed): security 5/9, functional 58/58.
  - `miss_custom_bindings` (T1/T5+T3 fixed): security 8/9, functional 58/58.
  - `miss_credential` (T1/T5+T2 fixed): security 5/9, functional 58/58.
  - `check_after_mkdir` (guard after the directory side effect): security 6/9, functional 58/58.
  - `refuse_all` (refuses every database path): security 9/9, functional 42/58.
  - `alt_correct_fix` (runtime raw-expression guard at a different layer): security 9/9,
    functional 58/58.
  - `hardening` (oracle plus expression rules on the v1 query and args fields): security 9/9,
    functional 58/58.
- Project tests at pinned and after the oracle: 53/53 pass (3 suites).
- `check_stack.py`: conforming (3 concepts, H4).
- Static gate: PASSED for the stacked task and the control.

## Could not verify / guesses

- The listing check and the fairness review are model-run pipeline stages; not run here.
- The exact n8n release the advisory shipped against is unknown. The pinned lockfile uses
  n8n-workflow 2.10.1, and the behaviour above was verified against that version; a much older
  n8n-workflow might not strip the prefix. The task's own verifier does not need n8n itself: it
  uses the package from the pinned lockfile.
- Credential expressions are resolved by n8n without item data (empty connection input), so the
  credential route can only be driven by `$env`/`$vars`, not `$json`. The security case for T3
  therefore uses `$env`. This is the narrowest of the four levers: a credential author can already
  choose an absolute literal path, so the expression adds reach rather than a new capability. It
  is kept because the required property is stated over values supplied through an expression and
  the record's hardest trap is this route; the fairness risk is recorded below.
- The verifier's image build (`npm ci` in node:22-bookworm-slim) and the full container gate were
  not run before the first gate invocation; the first gate result is in the final report.
- The `native/node-v127-linux-musl-x64` prebuilt binding is irrelevant to grading: the suites map
  `better-sqlite3` to a recording double, and the project's own test mocks it too.

## Scope note

- The v1 custom-bindings path (T2) selects a native shared object, so its impact includes loading
  arbitrary native code (CWE-426/CWE-94) beyond the advisory's path traversal. It is included only
  because the advisory's protection — no expression-supplied value may become a filesystem path —
  covers it; nothing else outside that protection is built on.

## Fairness notes

- The reported example is one expression on the v1 Database Path. The property is stated over any
  value supplied through an expression that becomes a filesystem path the product opens, creates
  or uses, in every part of the product. Read literally it covers the collection option and the
  stored credential without naming either.
- The natural runtime path predicate (resolve, reject `..`, reject absolute values, allowlist a
  root) breaks literal paths: the project's own suite uses a relative `test.sqlite` and an
  absolute custom-bindings path, and the handler deliberately creates missing parents. The
  functional group tests those values without the report naming them.
- T3 is the route most likely to be judged out of scope: a credential is administrator-set and a
  credential author can already choose an absolute literal path. The report does not mention it,
  and the property is worded over expression-supplied values so it covers the route literally.
  If a later fairness review rejects it, the concept can be dropped with no change to the report,
  leaving two concepts (T1/T5 and T2).

## Container gate

(filled in below)
