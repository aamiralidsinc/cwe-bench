# Breaker quality review — brief (shared by all reviewers)

You are reviewing **both-model breakers** of CWE-bench, a factory of Harbor security-fix tasks: a real open-source
repository at a vulnerable commit, a vulnerability report (`instruction.md`, the ONLY thing the solver sees besides the
repo), and hidden behavioural tests (security + functional). A breaker = DeepSeek V4.1 Flash and MiMo-V2.6-Pro each
failed 3 of 3 runs, every failing run passed an independent audit. The project is choosing which pipeline to scale
toward 100–200 tasks by **breaker quality**, so your judgements feed a pipeline comparison. Be exact and sceptical; do
not inflate. Cite evidence (file:line or short quotes).

The pipelines differ in how the hidden difficulty is made:
- **injection (sibling)**: the reported flaw plus injected sibling variants at other sites in the same repo
  (`source = "injected"`; manifest traps say which are injected).
- **stacking**: several independent REAL flaws behind one report (each has a `-control` twin with one bug).
- **precision-validation**: built by the same sibling builder in a separate experiment.

## Data (read-only)
Root: a temporary working folder on the Mac (2026-10-25); its data pack is copied here as qa_tasks.tsv/json and the reviews as review/.
- `data/tasks/<slug>/` — instruction.md, task.toml, tests/, solution/fix.patch, environment/ (injection.patch for
  injected tasks = what the builder planted into the real code).
- `data/build/<slug>/` — manifest.json (traps, patch_checks, wrong_fix_catalogue, stacking info), notes.md,
  FAIRNESS.md (+ FAIRNESS-VALIDATION.md if any), listing.json (stacking hint check), gate_verdict.json,
  blind_status.txt, checks/*.patch.
- `qa_runs.json` — per task, every graded run: model, reward, failing test ids, audit verdict + summary.
- `qa_tasks.json` — per task row: verdict, cwe, language, repo, fairness verdict (official reader), gate marker,
  audit confidence counts, repair counts.
- `data/UNCOVERED-UPSTREAM-CLASS.md` — the project's note on the "uncovered upstream" breaker class.
You may use the internet ONLY to read the upstream fix (GitHub advisory / fix commit named in manifest.json or
task.toml) for B6. Do not run task code.

## Metrics to fill, per breaker (from docs/BATCH-METRICS.md)
- **B1 failure type** per failing run: `security-miss` (a hole left open), `keep-working-regression` (broke legitimate
  use), `contract-only` (wrong status code / error form). A run can have several; give the decisive one(s).
- **B2 decisiveness**: the distinct tests that decided the failing runs (a run is decided by every failing test whose
  removal alone would not make it pass... simpler: list the failing tests per run; then n distinct across runs). One
  test deciding every run = fragile.
- **B3 margin**: rewards per run; did any run come close (only one test short of 1.0)?
- **B4 consistency**: same failure in every run, or different failures.
- **B5 audit confidence**: from qa_runs.json (high/medium counts); fairness READY/NOT_READY and any open human-review
  flag in FAIRNESS.md. If the official fairness verdict is NOT_READY, say whether that is stale or live (read the file
  dates/notes and any later test fix).
- **B6 open-internet survival**: is the decisive trap covered by the PUBLIC upstream fix? A trap the upstream fix does
  not cover survives a model that looks the fix up. Answer `uncovered` / `partly` / `covered` with the reason.
  (For injected siblings: the upstream fix never covers an injected site → usually `uncovered`, but say if the
  decisive failure is at the reported/published site instead.)
- **B7 hint exposure**: does the instruction name or paraphrase a trap, a far site, a variant list or the flaw count?
  Quote. `none` / `some` / `leaky`. Did the models fail even with the hints?
- **B8 solvability**: reference fix passes (gate .sound), blind fix status (blind_status.txt), alternatives that pass.
- **C1** cwe, mechanism (path traversal, SSRF, authz, injection, info leak, …), language/ecosystem, repo domain.
- **C2 trap shape**: origin (`uncovered-upstream` / `published-far-site` / `keep-working-value` / `injection`) and a
  SHORT decisive-pattern label (e.g. "missed second copy", "missed alias/encoding", "over-blocked legitimate use",
  "missed indirect route", "over-validated stored data"). Use plain, reusable labels so patterns can be compared.
- **D2 injection realism** (injection / precision-validation only): read environment/injection.patch. Are the injected
  sites plausible code an engineer would write, or obviously planted (odd names, dead code, comments pointing at the
  flaw, unnatural duplication)? `plausible` / `mixed` / `planted`, with evidence.
- **E strong-breaker checks**: e1 both 0/3 (given); e2 every failing run trusted, most high; e3 fairness READY, no
  open human question; e4 at least one decisive failure is a security miss; e5 decisive trap not covered upstream;
  (e6 near-duplicate is judged centrally — skip). Give true/false + one-line reason each.
- **concerns**: anything that weakens the breaker (fragile single test, contract-only decision, leaky hint, test
  weakness noted in audits, stale or open fairness).

## Output
For EACH slug assigned to you write `review/<slug>.json` (create the folder) with keys:
`slug, track, b1 {per_run:[{model,reward,types:[..],decisive_tests:[..]}], summary}, b2 {distinct_decisive_tests:[..],
n, fragile:bool}, b3 {rewards_ds:[..], rewards_mm:[..], near_miss_runs:int}, b4 {consistency:"same|similar|varied",
note}, b5 {trusted_high, trusted_medium, fairness, fairness_live:bool, open_human_question:str}, b6 {verdict, reason},
b7 {verdict, quotes:[..], failed_despite_hints:bool}, b8 {gate, blind, note}, c1 {cwe, mechanism, language, domain},
c2 {origin, pattern, note}, d2 {verdict, evidence} (or null for stacking), e {e1,e2,e3,e4,e5: {ok, why}},
concerns:[..], one_line: str` (one plain sentence a reader can use to remember this breaker).
Validate each file parses. Then reply with a compact table: slug | B1 decisive type | B6 | B7 | C2 pattern | e2-e5
pass/fail | top concern.
