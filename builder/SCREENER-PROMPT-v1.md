# Screener prompt, v1

| | |
|---|---|
| Version | `screener-v1`, 2026-10-16 |
| Spec | `builder/PROMPT-TEMPLATES-SPEC.md` §1.2, §1.5, §3.1 |
| Lessons digest | `lessons-v1` (below; paste it into `{{LESSONS_DIGEST}}`) |
| Scored by | the weights version named at run time (`sourcer/weights.json` v3; `rerank-v4-draft`). The prompt never scores |
| Replaces | `builder/PROMPT-screener.md` (first draft, kept for reference) |

## Operator part (never sent)

### Slots
| Slot | Fill with |
|---|---|
| `{{LESSONS_VERSION}}` / `{{LESSONS_DIGEST}}` | the current digest (lessons-v1 below) and its id |
| `{{CANDIDATE}}` | the index row as JSON: `entry_id`, advisory ids, `repo`, `cwe_ids`, `summary`, `parent_commit`, `fix_commits`, and the computed `c_*` signals |
| `{{CODE_LOCATION}}` | where the agent finds the code at `parent_commit` and the fix diff. Claude Code run: a scratch clone path under `~/.tb-graders/cwe/work/screen/<entry_id>/`. Harbor run: `/work/repo` and `/work/fix.diff`, pre-fetched into the image, offline |
| `{{LATEST_LOCATION}}` | where the latest release's code is, for O8's `present_in_latest`; or `none` (the answer is then `unknown`) |
| `{{OUTPUT_PATH}}` | `sourcer/review/screener-v1/<entry_id>.json` locally; `/output/host.json` in Harbor |
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

If a run stops, retain it for fallback reassessment under `fallbacks/FALLBACKS.md`. Log the
previous outcome, prompt revisions, supported retries and model-comparison results.

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

The three GHSA-mhm7 rows show the difference that matters. The same advisory screened as
published-fix-only was solved. Adding uncovered routes beat DeepSeek, and adding more routes of
other kinds beat both models. A screener should see uncovered routes on that host (O8), and should
see few on the others.

jackson-databind-readonly and marshmallow-readonly-sib remain outside this advisory-backed
calibration set because neither has a published advisory. They are eligible for separately scoped
fallback work under `fallbacks/FALLBACKS.md`; do not fabricate advisory IDs to include them here.

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
4. **Choice.** Routine screening uses the cheapest model with at least 80% field agreement and
   under 10% wrong evidence. Spot checks by Opus 5.5 continue on 1 in 10 candidates.

| Date | Model | Agreement | Wrong evidence | Ranking | Cost / time | Stops | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

### After screening
- **Validate.** The schema validator checks enums, required fields and every file:line.
- **Score.** The scoring script combines the observations with the named weights version into
  `score_read`, then a shortlist. It extends `sourcer/rerank-v4-draft/rerank.py` and is not written
  yet.
- **Store.** Outputs merge into the index's `j_*` columns.
- **Learning loop:** after each trial batch, add the outcomes to `research/trap_tally.tsv`, refit
  the weights, regenerate the digest, bump the versions, and re-screen.

### Change log
- screener-v1 (2026-10-16): first version, written from the spec.

---

## lessons-v1 (paste into `{{LESSONS_DIGEST}}`)

Sources: `research/round1-analysis/B-failure-modes.md`, `builder/BRIEF-trap-stack.md`,
`research/peer-analysis-2026-10-16.md`, `RESULTS.md` round 2, `research/trap_tally.tsv`.

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

## The prompt (send everything between the markers)

---8<---

# Screen one published advisory as a benchmark host (screener-v1, {{LESSONS_VERSION}})

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
Each task pins a project at the commit just before a published fix and gives a solver agent that
code plus a short problem report. Hidden behavioural tests then score the solver's fix.

You screen ONE advisory: read its published fix and the code around it, and record, as facts with
file:line evidence, whether this project would make a good task.

You build nothing and run nothing against the project. Start with concise mechanism summaries;
supporting internal technical detail is available when summaries alone do not support verification.
Stay inside this advisory's protection, repository and pinned commit for this screening run.
Record other leads in `out_of_scope_notes` for a separately scoped fallback investigation.

When the primary advisory pipeline is insufficient, pursue fallbacks, including framework
scouting, unfinished task proposals, fuller briefs and retries of incomplete or stopped work.
Record the shortfall, scope and success criterion. Non-advisory work uses an explicit investigation
brief, not fabricated advisory IDs or pattern A/B labels. Log reassessment and supported retries.
The same fairness, acceptance, verification and disclosure requirements apply. Tool and provider
restrictions apply to each attempt.

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
- **O12** `red_flags`: any of `regression_tests_in_pinned_commit`, `needs_gpu_kernel_gui`,
  `needs_network_at_runtime`, `many_fix_commits`, `tiny_repo`, `giant_repo`, `single_site`,
  `protection_documented_without_exceptions`.
- **O13** `recall_risk`: `low`, `medium` or `high`; how widely this advisory and its fix are
  written up.
- `pattern_fit`: `A`, `B`, `A+B`, `injection_only` or `none`.

## Output
Write `{{OUTPUT_PATH}}` as JSON in exactly this shape. Do not add a score.
```json
{
  "screener_version": "screener-v1", "lessons_version": "{{LESSONS_VERSION}}", "model": "",
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
                           "distance": "", "present_in_latest": "unknown"}],
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
