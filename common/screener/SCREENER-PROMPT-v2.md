# Screener prompt, v2

| | |
|---|---|
| Version | `screener-v2`, 2026-10-16 (copied from v1, then edited; see the change log) |
| Spec | `common/builder/PROMPT-TEMPLATES-SPEC.md` §1.2, §1.5, §3.1 |
| Lessons digest | `lessons-v1` (below; paste it into `{{LESSONS_DIGEST}}`) |
| Scored by | the weights version named at run time (`sourcer/weights.json` v3; `rerank-v4-draft`). The prompt never scores |
| Replaces | `common/archive/old-prompts/SCREENER-PROMPT-v1.md` (kept, with its calibration results) |

## Operator part (never sent)

### Slots
| Slot | Fill with |
|---|---|
| `{{LESSONS_VERSION}}` / `{{LESSONS_DIGEST}}` | the current digest (lessons-v1 below) and its id |
| `{{CANDIDATE}}` | the index row as JSON: `entry_id`, advisory ids, `repo`, `cwe_ids`, `summary`, `parent_commit`, `fix_commits`, and the computed `c_*` signals |
| `{{CODE_LOCATION}}` | where the agent finds the code at `parent_commit` and the fix diff. Claude Code run: a scratch clone path under `~/.tb-graders/cwe/work/screen/<entry_id>/`. Harbor run: `/work/repo` and `/work/fix.diff`, pre-fetched into the image, offline |
| `{{LATEST_LOCATION}}` | where the latest release's code is, for O8's `present_in_latest`; or `none` (the answer is then `unknown`) |
| `{{OUTPUT_PATH}}` | `common/screener/records/<entry_id>.json` locally; `/output/host.json` in Harbor |
| `{{TIME_BOX_MIN}}` | 20 by default |

### Launch modes
- **Claude Code sub-agent.** Send the prompt with the slots filled.
- **Harbor job** (DeepSeek, MiMo or another model with Claude Code as the harness):
  - one task folder per candidate;
  - `instruction.md` = the filled prompt;
  - the environment holds the pre-fetched code;
  - network limited to the model API;
  - the output is checked by the schema validator.
- **Fresh chat.** Paste the filled prompt.

If a run is stopped by a safety check, narrow the prompt and log the change below. Never re-run a
stopped prompt on another model.

### Calibration set (hosts with known, audited outcomes)
| Host | Advisory | Pattern | Outcome |
|---|---|---|---|
| jackson-databind-sib2 | GHSA-mhm7-754m-9p8w | B | both models 0/3 |
| hono (peer) | GHSA-hxh3-vqpv-xpqv | A | both models 0/3 |
| jackson-databind-sib | GHSA-mhm7-754m-9p8w | B | DeepSeek 0/6, MiMo solved |
| nltk (peer) | GHSA-p4rw-rvv2-7xwr | A | DeepSeek 0/3, MiMo solved |
| MCP TypeScript SDK (Hadi; peer) | GHSA-6qxp-vccf-f47h | A | DeepSeek 0/3; MiMo solved (Hadi) |
| jackson-databind (mined) | GHSA-mhm7-754m-9p8w | published fix only | both solved |
| better-auth-sso-endpoints | GHSA-5rr4-8452-hf4v | A | DeepSeek solved |
| async-http-client | GHSA-2jwh-9rmr-j4xf | mined | both solved |
| webob | GHSA-6hx8-3wjj-gr8g | mined | both solved |
| pyload-ng (peer) | GHSA-68w4-83fh-f2w8 | single site | DeepSeek solved |
| GitPython (peer) | GHSA-3wxw-xv34-2frg | mined | DeepSeek solved |
| undici (peer) | GHSA-vp8m-p9jh-q5pm | A | MiMo 0/1, DeepSeek solved (weak label) |
| hickory-dns | GHSA-5j98-2g5x-46v6 | mined | both solved |
| py-shiny | GHSA-47c3-hpmg-7j6p | mined | both solved |
| rclone | GHSA-xwwr-4h3p-r22c | mined | both solved |
| russh | GHSA-p8qx-h547-fjw9 | mined | both solved |
| argo-workflows (stack) | GHSA-48p8-g2fx-3wwm | stacking | both solved |
| asyncssh (stack) | GHSA-2wxc-x7rj-hg8f | stacking | both solved |
| cloudreve (stack) | GHSA-49h3-cwhj-4737 | stacking | both solved |
| filament (stack) | GHSA-52xp-w8hr-xv3c | stacking | both solved |
| stigmem (stack) | GHSA-5p3m-vhh6-9236 | stacking | both solved |
| trigger-dev (stack) | GHSA-59h8-w5q6-mfmp | stacking | both solved |
| msgpack5 (peer) | GHSA-24ch-f2g6-9hhh | mined | DeepSeek solved |
| typespec openapi3 (peer) | GHSA-2q42-4q24-7rgv | mined | DeepSeek solved |
| datamodel-code-generator (peer) | GHSA-77xj-x4rm-935c | mined | DeepSeek solved |
| pymongo (peer) | GHSA-8fvv-fgr5-f8ch | mined | DeepSeek solved |
| httpx2 (peer) | GHSA-8xx6-hgc6-gc2m | mined | DeepSeek solved |
| pyload-ng 9q47 (peer) | GHSA-9q47-3cm2-2rp8 | mined | DeepSeek solved |
| banks (peer) | GHSA-hmq2-7hp6-7crh | mined | DeepSeek solved |
| stream-json (peer) | GHSA-hqr4-qq8f-hg3x | mined | DeepSeek solved |
| devalue j22f (peer) | GHSA-j22f-vq7h-c4qm | mined | DeepSeek solved |
| ip-address (peer) | GHSA-j6r3-76f7-8jcv | mined | both solved |
| pyload-ng jq7h (peer) | GHSA-jq7h-wrvp-3rgx | mined | DeepSeek solved |
| devalue mcm9 (peer) | GHSA-mcm9-63f2-9j32 | mined | DeepSeek solved |
| adm-zip (peer) | GHSA-p634-w6r4-rjp2 | mined | both solved |
| pydantic-ai (peer) | GHSA-q2xc-rrxj-58x9 | mined | DeepSeek solved |
| payload plugin-import-export (peer) | GHSA-qf28-8hc6-vwrp | mined | DeepSeek solved |
| pypdf v247 (peer) | GHSA-v247-6f48-mgcj | mined | DeepSeek solved |
| nltk w3v8 (peer) | GHSA-w3v8-gmh9-3wv7 | mined | DeepSeek solved |

Added in v2 (2026-10-16): our remaining audited hosts and the peer team's 24 (5 were already
listed). Stacking hosts are screened on one advisory of the stack (the first one the index can
use); both models solved the whole stack, so the single advisory is labelled solved. Left out: the
actualbudget and ruby-saml stacks (no advisory of theirs is in the index window) and pypdf
GHSA-5jq2 (fix commit not fetchable). 37 hosts: 2 both failed (jackson GHSA-mhm7, labelled by its
best outcome, and hono), 3 one model failed (nltk, MCP SDK, undici), 32 solved.

The three GHSA-mhm7 rows show the difference that matters. The same advisory screened as
published-fix-only was solved. Adding uncovered routes beat DeepSeek, and adding more routes of
other kinds beat both models. A screener should see uncovered routes on that host (O8), and should
see few on the others.

jackson-databind-readonly and marshmallow-readonly-sib are left out: neither has a published
advisory, so they are outside both patterns.

### Model comparison protocol
1. **Reference.** Opus 5.5 screens every calibration host once; the lead checks each reading.
2. **Candidates.** Each model screens the same hosts with the same prompt, once:
   - Fable 5.1, Opus 4.8;
   - DeepSeek V4.1 Flash and MiMo-V2.6-Pro (through Harbor);
   - any other available model.
3. **Metrics, per model:**
   - field agreement with the reference (O1–O8, `pattern_fit`);
   - share of file:line claims that do not hold (checked by script);
   - whether hosts that broke a model rank above solved hosts once scored;
   - cost; wall time; stops.
4. **Choice (screener-v2, fixed before the run; replaces v1's 80%-agreement rule).**
   1. Gates, all required: at least 95% valid records; under 5% wrong evidence (a citation of a
      file the screener wrote itself counts as wrong); no safety stops.
   2. Main measure, fact precision: on 10 hosts (the 5 that beat a model and 5 solved, drawn at
      random with seed 20261017), every O2 site and O8 route each model claims is checked against the pinned code,
      with model names hidden. Precision = claims that hold / claims made.
   3. Ranking, with a bootstrap 90% interval: concordance of `score_read` with the outcomes, and
      the false-hard rate (solved hosts scoring above the median of the hosts that beat a model).
   4. Pick the passing model with the highest fact precision. Within 10 points of it, prefer the
      better ranking; when the ranking intervals overlap, prefer the cheaper and faster model,
      and a model that is not a target model (DeepSeek and MiMo would be picking their own test
      hosts). Agreement with Opus 5.5 is reported, not used.
   Spot checks by Opus 5.5 continue on 1 in 10 candidates.

| Date | Model | Agreement | Wrong evidence | Ranking | Cost / time | Stops | Notes |
|---|---|---|---|---|---|---|---|
| 2026-10-17 | GPT-6.1-Sol (xhigh) | 69%* | 0.0% | 0.77 (0.64-0.89) | ChatGPT plan; median 5.8 min, ~1.2M tokens/run | 0 | 37/37 valid; fact precision 89% (16/18); false-hard 0.18. **Chosen** (see below) |
| 2026-10-17 | GPT-6-Astra (xhigh) | * | 0.0% | 0.79 (0.63-0.96) | ChatGPT plan; median 6.2 min, ~1.2M tokens/run | 0 | 36/37 valid; fact precision 90% (18/20); false-hard 0.04 |
| 2026-10-17 | Opus 5.5 | ref. | 0.1% | 0.75 (0.58-0.90) | Claude plan; median 2.0 min | 0 | 37/37 valid; fact precision 78% (14/18); false-hard 0.07 |
| 2026-10-17 | DeepSeek V4.1 Flash | * | 0.1% | 0.60 (0.39-0.81) | API; median 4.5 min | 0 | 37/37 valid; fact precision 53% (18/34; uncovered routes 8/24); false-hard 0.32 |
| 2026-10-17 | MiMo-V2.6-Pro | * | 0.4% | 0.84 (0.70-0.97) | API; median 17.0 min, 2 runs hit 30 min | 0 | **gate failed**: 33/37 valid (2 empty `model`, 1 malformed JSON, 1 timeout); fact precision 59% (17/29) |

\* Agreement with Opus is reported only, not used (rule step 4); not recomputed for v2.
Ranking columns: concordance (90% bootstrap interval) on the 33 hosts every model returned valid,
5 of which beat a model. Fact precision: 119 claims (O2 sites, O8 routes) on 10 hosts, judged
against the pinned code by 10 Opus 5.5 checkers with model names hidden
(`fact-check/verdicts.tsv`). Applying the rule: gates pass for all but MiMo; Astra has the
highest precision (90%) and Sol is within 10 points (89%); their ranking intervals overlap, so
the faster one wins: Sol (median 5.8 vs 6.2 min, p90 6.9 vs 8.7; tokens within 3%). Astra is a
near tie and has the lower false-hard rate; either is defensible. Neither is a target model.
Caveats: 18-34 claims per model; the checkers are Opus 5.5, itself a candidate (it scored third).
Run set: `~/.tb-graders/cwe/work/screen/calib-v2-20261017T0001Z/` (`choice.md`, `fact-check/`).

v1 results: `common/archive/old-prompts/SCREENER-PROMPT-v1.md`.

### After screening
- **Validate.** The schema validator checks enums, required fields and every file:line.
- **Score.** The scoring script combines the observations with the named weights version into
  `score_read`, then a shortlist. It extends `pipelines/sibling/3-rank/rerank.py` and is not written
  yet.
- **Store.** Outputs merge into the index's `j_*` columns.
- **Learning loop:** after each trial batch, add the outcomes to `docs/research/trap_tally.tsv`, refit
  the weights, regenerate the digest, bump the versions, and re-screen.

### Change log
- screener-v1 (2026-10-16): first version, written from the spec.
- screener-v2 (2026-10-16), from the v1 calibration (`common/archive/old-prompts/SCREENER-PROMPT-v1.md`):
  - O12 red flags defined one by one (Opus raised `regression_tests_in_pinned_commit` on 3 hosts
    where only older tests for the area existed);
  - enum fields hold exactly one listed value, no added text (prose in `present_in_latest`
    invalidated 2 records); O8 routes get a `latest_where` field for that evidence;
  - evidence only from the pinned code or the fix diff, with paths from the repository root; never
    a file the screener wrote (self-citation was 16% of one model's evidence);
  - calibration set grown from 9 to 37 hosts; choice rule replaced (see "Choice").
- lessons-v2 (2026-10-19): digest only, prompt unchanged; adds the where-vs-how lessons from the
  93-task sibling analysis (`docs/BETTER-PATTERNS.md` §5).

---

## lessons-v1 (paste into `{{LESSONS_DIGEST}}`)

Sources: `docs/research/round1-analysis/B-failure-modes.md`, `common/builder/BRIEF-trap-stack.md`,
`docs/research/peer-analysis-2026-10-16.md`, `docs/RESULTS.md` round 2, `docs/research/trap_tally.tsv`.

```
How the target models fail (audited runs, ours and a peer team's):
- They find the vulnerable code and diagnose the root cause correctly. They fail on SCOPE.
- They treat the report's example as the full list of affected paths.
- They fix only the input shape they reproduced (a plain string, not an array).
- They verify through the same path as their own fix, then stop ("fully validated").
- They read a "must keep working" requirement as permission to leave a sink open.
- They miss state that crosses a save/reload or serialization boundary when the check never calls
  the code that produces that state (a schema, serializer, cache or config loader, not a handler).
- They miss a second implementation, a lower-level public API or a wrapper that reaches the sink.
- They see a route and argue it out of scope when there is a plausible reason: an unsupported
  combination, a neighbouring feature, a legacy path. This "reason to dismiss" is the strongest
  single lever found so far.
- Distance helps: the overlooked route sits in another file or package from where the report leads,
  in a codebase too large to read whole.
Model profiles: DeepSeek V4.1 Flash is fast (median about 15 min) and talks itself out of fixing
what it found. MiMo-V2.6-Pro is slower, probes candidate paths, explores narrowly and tends to
over-harden, breaking legitimate behaviour.
What never made a task hard: encoding, verb, protocol or role/direction variants; more routes of one
concept (they fall together); single-location fixes; resource exhaustion (0 of 7); small libraries;
a protection documented with no exceptions; instruction wording alone.
Both patterns that produced failures:
- A, published scope: the published fix spans several entry points, one in a module that looks out
  of scope, plus input-shape variants and a must-keep-working behaviour.
- B, uncovered routes: the advisory's own protection is also missing, at the pinned commit, on
  routes into the same sink that the published fix did not touch.
```

---

## lessons-v2 (2026-10-19; paste into `{{LESSONS_DIGEST}}` instead of lessons-v1)

Sources: everything in lessons-v1, plus `reports/SIBLING-INJECTION-PATTERNS.md` (93 tasks, 609
traps) and `docs/BETTER-PATTERNS.md` §5-§8. It is lessons-v1 with the last block added.

```
How the target models fail (audited runs, ours and a peer team's):
- They find the vulnerable code and diagnose the root cause correctly. They fail on SCOPE.
- They treat the report's example as the full list of affected paths.
- They fix only the input shape they reproduced (a plain string, not an array).
- They verify through the same path as their own fix, then stop ("fully validated").
- They read a "must keep working" requirement as permission to leave a sink open.
- They miss state that crosses a save/reload or serialization boundary when the check never calls
  the code that produces that state (a schema, serializer, cache or config loader, not a handler).
- They miss a second implementation, a lower-level public API or a wrapper that reaches the sink.
- They see a route and argue it out of scope when there is a plausible reason: an unsupported
  combination, a neighbouring feature, a legacy path. This "reason to dismiss" is the strongest
  single lever found so far.
- Distance helps: the overlooked route sits in another file or package from where the report leads,
  in a codebase too large to read whole.
Model profiles: DeepSeek V4.1 Flash is fast (median about 15 min) and talks itself out of fixing
what it found. MiMo-V2.6-Pro is slower, probes candidate paths, explores narrowly and tends to
over-harden, breaking legitimate behaviour.
What never made a task hard: encoding, verb, protocol or role/direction variants; more routes of one
concept (they fall together); single-location fixes; resource exhaustion (0 of 7); small libraries;
a protection documented with no exceptions; instruction wording alone.
Both patterns that produced failures:
- A, published scope: the published fix spans several entry points, one in a module that looks out
  of scope, plus input-shape variants and a must-keep-working behaviour.
- B, uncovered routes: the advisory's own protection is also missing, at the pinned commit, on
  routes into the same sink that the published fix did not touch.
Where vs how (2026-10-19, 93 tasks):
- WHERE-type siblings (another entry point into the same code; a planted copy) only cost the model
  a search. Once a report describes their surface they are fixed together: 5 of 98 planted
  siblings were ever missed. They count only as extras.
- HOW-type siblings, whose fix needs the mechanism understood, held even when the report stated
  them: a data producer deep in internal machinery (a table or schema builder the check never
  calls), a parser differential on the protected item's identity (a separator split, a rename after
  the check), a coupled legitimate value next to the hidden one. Rate a host by the how-type room in
  its real code, not by its route count.
- A real second implementation at distance (separate code doing the same job in another package or
  transport) was missed by both models when the report did not describe it. To find one, search the
  pinned tree for the low-level primitive the protected operation uses (redirect following, header
  copying, file writes, message construction) across packages, fallbacks, transports and legacy
  versions; record it as O2 `second_implementation` or as an O8 route.
- A route where the protection never existed counts as an uncovered route when the advisory's
  property covers it; leaving it open is a model failure, not out of scope.
```

---

## The prompt (send everything between the markers)

---8<---

# Screen one published advisory as a benchmark host (screener-v2, {{LESSONS_VERSION}})

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
Each task pins a project at the commit just before a published fix and gives a solver agent that
code plus a short problem report. Hidden behavioural tests then score the solver's fix.

You screen ONE advisory: read its published fix and the code around it, and record, as facts with
file:line evidence, whether this project would make a good task.

You build nothing and run nothing against the project. Describe each mechanism in one line, never
as exploitation steps. Stay inside this advisory's own protection, in this repository, at the
pinned commit. If you notice anything outside that scope, give it one line in `out_of_scope_notes`
and do not pursue it.

## What a good task needs
Two target models must each fail all 3 finished attempts through their own judgement, while the
task stays fair: a careful engineer can find everything from the report and the code, and fix it in
about 45 minutes. Two patterns have produced such tasks:
- **Pattern A, published scope.** The published fix spans several entry points, at least one in a
  module that looks out of scope (a second implementation, a lower-level API, a wrapper, a
  save/reload path, a defaults or merge route). Add input-shape variants, and a legitimate
  behaviour next to the sink that an over-broad fix breaks.
- **Pattern B, uncovered routes.** At the pinned commit, the same protection is also missing on
  other routes into the same protected sink, which the published fix did not touch, and a solver
  could plausibly argue those routes were never covered.

A host may support both. We may also add siblings to our own copy, so note where one would be
realistic.

## Lessons ({{LESSONS_VERSION}})
{{LESSONS_DIGEST}}

## Inputs
Candidate:
```json
{{CANDIDATE}}
```
Code at the pinned commit and the fix diff: {{CODE_LOCATION}}
Latest release, for O8 only: {{LATEST_LOCATION}}

## Steps
1. Read the advisory text and the fix diff. Count source changes only; ignore tests, docs and
   changelogs.
2. Write the trust decision in one line: what is decided, and where.
3. Name the **landing point**: where an engineer who read only the advisory summary would look
   first.
4. For each changed source site, name the public entry point that reaches it (HTTP route, CLI
   command or public API call). Mark the module kind.
5. List the routes into the same protected sink at the pinned commit. For each, say whether the
   protection is applied. Routes without it that the fix did not change go in O8. Use
   `{{LATEST_LOCATION}}` to say whether each is still present today; if it is `none`, answer
   `unknown`.
6. Fill every observation below. A value without file:line evidence must be `unknown`.
7. Check buildability.
8. Write the output, then re-open each file:line you cite and confirm it says what you claim.

## Evidence and format rules
- Cite only the code at the pinned commit, as `path:line` or `path:start-end` with the path from
  the repository root (never a bare file name), or the fix diff as `fix.diff:line`. Cite the latest
  code only in `latest_where`, as `latest/path:line`.
- Never cite a file you wrote yourself (notes, scratch files). Write only the output file.
- Every enum field holds exactly one of its listed values and nothing else. Put explanations in
  the neighbouring free-text field or in `unverified`.

## Observations
- **O1** `entry_points`: the number of distinct public entry points that reach the flaw the
  published fix closes.
- **O2** `out_of_scope_site`: the kind is one of `second_implementation`, `lower_level_api`,
  `wrapper_or_composition`, `save_reload_or_serialization`, `defaults_or_merge_route`,
  `legacy_path` or `none`; give its location.
- **O3** `reason_to_dismiss`: the one-line argument a solver could make for leaving the O2 site or
  an O8 route alone.
- **O4** `distance`: files and packages between the landing point and the farthest site; repo size
  in MB if known.
- **O5** `coupled_behaviour`: a legitimate behaviour next to the sink that an over-broad fix would
  break.
- **O6** `input_shapes`: the input-shape variants the published fix handles.
- **O7** `producer`: the kind is one of `schema`, `serializer`, `cache`, `mapper`, `config_loader`,
  `handler` or `none`; give its location, and whether the check calls it.
- **O8** `uncovered_routes`: Pattern B. Within the scope above only.
- **O8b** `injection_room`: places in our copy where a sibling of the same mechanism would be
  realistic, and why a maintainer could have written it.
- **O9** `family`: the weakness family, plus a `dos` flag.
- **O10** `build`: language, toolchain, services, whether it runs offline after the build, and the
  project's own tests for this area.
- **O11** `fix_minutes`: the estimated minutes for a careful engineer who knows where to look to
  fix every site and route.
- **O12** `red_flags`: any of these, each only when its definition holds:
  - `regression_tests_in_pinned_commit`: the tests that the fix diff adds or changes are already
    present at the pinned commit (compare the diff's test files with the pinned tree). Older tests
    for the same area do not count.
  - `needs_gpu_kernel_gui`: the affected code cannot run without a GPU, a kernel module or a GUI.
  - `needs_network_at_runtime`: the affected behaviour cannot be exercised offline after the build.
  - `many_fix_commits`: the published fix spans more than 4 commits.
  - `tiny_repo`: under 5 MB of source; `giant_repo`: over 1.5 GB.
  - `single_site`: the published fix changes one function at one place, and no O2 site or O8 route
    exists.
  - `protection_documented_without_exceptions`: the project documents the protection as applying
    everywhere, with no exceptions, so no route can plausibly be argued out of scope.
- **O13** `recall_risk`: `low`, `medium` or `high`; how widely this advisory and its fix are
  written up.
- `pattern_fit`: `A`, `B`, `A+B`, `injection_only` or `none`.

## Output
Write `{{OUTPUT_PATH}}` as JSON in exactly this shape. Do not add a score.
```json
{
  "screener_version": "screener-v2", "lessons_version": "{{LESSONS_VERSION}}", "model": "",
  "entry_id": "", "advisory_ids": [], "repo": "", "pinned_commit": "", "fix_commits": [],
  "trust_decision": {"summary": "", "evidence": ["path:line"]},
  "landing_point": {"where": "path:line", "why": ""},
  "fix_sites": [{"where": "path:line", "entry_point": "", "module_kind": ""}],
  "O1_entry_points": 0,
  "O2_out_of_scope_site": {"kind": "none", "where": ""},
  "O3_reason_to_dismiss": "",
  "O4_distance": {"files": 0, "packages": 0, "repo_mb": null},
  "O5_coupled_behaviour": {"what": "", "where": ""},
  "O6_input_shapes": [],
  "O7_producer": {"kind": "none", "where": "", "check_calls_producer": null},
  "O8_uncovered_routes": [{"route": "one line", "where": "path:line", "reason_to_dismiss": "",
                           "distance": "", "present_in_latest": "unknown", "latest_where": ""}],
  "O8b_injection_room": [{"where": "path:line", "sibling": "one line", "why_realistic": ""}],
  "O9_family": "", "O9_dos": false,
  "O10_build": {"language": "", "toolchain": "", "services": [], "offline_after_build": null,
                "project_tests": ""},
  "O11_fix_minutes": 0,
  "O12_red_flags": [],
  "O13_recall_risk": "low",
  "pattern_fit": "none",
  "j": {"j_multi_site": 0, "j_sites_touched": "", "j_sibling_sites": "unknown",
        "j_cause_other_layer": 0, "j_defence_ineffective": 0, "j_overbroad_breaks_legit": 0,
        "j_tempting_wrong_fix": ""},
  "out_of_scope_notes": [],
  "unverified": []
}
```
How to fill the `j` block:
- `j_multi_site` = 1 when the same check must hold at several sites (O1 ≥ 2, or O8 is not empty).
- `j_sites_touched`: the fix's source files.
- `j_sibling_sites`: `yes`, `no` or `unknown`, for O8.
- `j_cause_other_layer` = 1 when O2 or O7 places the cause in another layer from the landing point.
- `j_defence_ineffective` = 1 when a defence was present and did not work.
- `j_overbroad_breaks_legit` = 1 when O5 is filled.
- `j_tempting_wrong_fix`: the fix an engineer would try first, in one line.

## Limits
- At most {{TIME_BOX_MIN}} minutes.
- No Docker, and no running of the project's code; reading and searching only.
- No network beyond the code locations above. No other repositories.
- If something cannot be checked in the time, mark it `unknown` and list it in `unverified`.

When done, reply in 5 lines or fewer:
- the output path;
- the trust decision;
- `pattern_fit`;
- the strongest lever;
- the biggest red flag.

---8<---
