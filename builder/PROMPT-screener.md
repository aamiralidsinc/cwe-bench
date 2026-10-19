# Screener prompt template (host reader pass)

One sub-agent per candidate. Fill the `{{...}}` slots and send everything between the two
`---8<---` lines. The candidates come from `sourcer/rerank-v4-draft/host-shortlist-40.tsv`
(NEXT-STEPS step 1: the top 30). The reader only reads code. It builds nothing, runs no Docker
and no models.

| Slot | Fill with |
|---|---|
| `{{ENTRY_ID}}` | the row's `entry_id` |
| `{{ROW}}` | the full TSV row, with its header line |
| `{{FIX_COMMITS}}` | fix commit(s) and vulnerable parent, from `sourcer/index/candidates.sqlite` (`fix_commit`, `parent_commit`) |

If a safety check stops a brief, narrow the brief (drop the exploit wording, keep the
code-reading questions). Do not route it through another model.

---8<---

You are screening ONE published, already-fixed security advisory in an open-source project. The
question is whether its repository is a good HOST for a security-fix benchmark task. The task will
give a solver agent the vulnerable code and a vulnerability report; hidden behavioural tests then
check its fix. You only read code and judge. You build nothing, run no Docker and no
trials, and do not contact the maintainers or anyone else.

Project root: `/Users/dev/terminal-bench/cwe-bench`. Scratch: `~/.tb-graders/cwe/work/screen/{{ENTRY_ID}}/`.

## The candidate
```
{{ROW}}
```
Fix commit(s) and vulnerable parent: {{FIX_COMMITS}}

The `why` column and every computed score are guesses from proxies. Check each one against the code.

## Read first (only these)
- `builder/BRIEF-trap-stack.md`: what a round-2 task needs, with every lesson so far.
- `research/round1-analysis/B-failure-modes.md` §3a (the 8 trap recipes), §3c (code signals for each).

## What we are looking for
Goal: a task where BOTH DeepSeek V4.1 Flash and MiMo-V2.6-Pro fail all 3 finished attempts, and every
failure is the model's fault, not the task's. Models always find the code the report points at. They
fail by judging wrongly about code the report does not name. A good host has:

1. **A base shape that beats DeepSeek** (at least one):
   - *Feature-absent sibling with a reason to dismiss.* One route to the protected sink ignores the
     protection entirely, and a reasonable engineer could argue it was never covered (an unsupported
     combination, a neighbouring feature, a legacy path). The route sits in a different file or
     package from where the report's example lands, in a codebase too large to read whole.
   - *Data producer off the check's path.* The fix needs the check AND the infrastructure that
     produces the check's data (schema, serializer, cache, persistence mapper, config loader). The
     check does NOT call the producer: the data arrives on a separate path (saved and reloaded,
     rebuilt from config). The producer must not be a request handler; handlers get read whole.
2. **Room for at least two traps of DIFFERENT dismissal reasons that MiMo missed in round 1**:
   coupled visible binding (rank 1), merged/defaults route (2), neighbour-precedent authorisation (3),
   post-adjustment value (5), parser differential with privileged fallback (6), missing-authority
   fallback (7), shared helper with divergent contracts (8). Real, unmodified gaps at the vulnerable
   commit are the best (all three traps in jackson-databind-sib2 were). Otherwise each trap needs a
   realistic injection spot.
3. **A fair hook for every trap.** An invariant a report could state without naming the mechanism,
   or standard expert knowledge, plus a visible clue in the code near the mechanism.
4. **Buildable as a task.** A real entry point (HTTP, CLI or public API); runs offline after the
   image is built; the project's own tests for the area run; a careful engineer who knows where to
   look fixes everything in about 45 minutes.

Weak hosts, which round 1 showed get solved:
- small libraries, where the whole mechanism fits in a few hundred lines;
- a single obvious sink or a one-site guard;
- traps that are only encoding, verb, protocol or role/direction variants, or more routes of one concept;
- a protection documented with no exceptions, so nothing invites a dismissal;
- a vulnerable commit that already contains the advisory's regression tests;
- a need for a GPU, kernel, GUI or network at run time;
- a famous CVE whose fix is easy to recall.

## Steps
1. Fetch the repository at the vulnerable parent into scratch (shallow fetch of that sha).
   `git log` between the parent and the fix: note any commit that adds the advisory's tests.
2. Read the fix diff. Write in two lines what the trust decision is and where it is made.
3. Find every other place the same decision is, or should be, made (§3c signals: grep for the
   protection's API in each sibling mechanism; merges or defaults downstream of the check; second
   parsers; fallback sources; arithmetic on attacker values; helpers shared by several public APIs;
   where the check's data comes from).
4. For each candidate trap: does it exist at the vulnerable commit as a real gap, or would it need
   injecting? Give its distance from the report's landing point, the reason an engineer would
   dismiss it, and the invariant sentence that would cover it without naming it.
5. Check the build: language toolchain, services, the entry point a test would drive, whether the
   project's tests for that area exist.

## Output
Write `sourcer/review/hosts-v4/{{ENTRY_ID}}.json`:
```json
{
  "entry_id": "{{ENTRY_ID}}", "primary_id": "", "repo": "", "vulnerable_commit": "", "fix_commit": "",
  "verdict": "build | maybe | reject",
  "verdict_reason": "one or two sentences",
  "trust_decision": "what is decided, and where (file:line)",
  "base_shape": {"kind": "feature_absent_sibling | producer_off_check_path | none",
                 "where": "file:line", "real_gap": true, "distance": "file/package from landing point",
                 "reason_to_dismiss": "", "producer_is_infrastructure": null,
                 "check_calls_producer": null},
  "traps": [{"recipe_rank": 1, "shape": "", "where": "file:line", "real_gap": true,
             "dismissal_reason": "", "invariant_sketch": "", "visible_clue": "",
             "realistic_because": ""}],
  "distinct_dismissal_reasons": 0,
  "entry_point": "", "services": [], "offline_risks": "", "project_tests": "",
  "fix_minutes_estimate": 0,
  "red_flags": [],
  "j_multi_site": null, "j_cause_other_layer": null, "j_defence_ineffective": null,
  "j_overbroad_breaks_legit": null, "j_sibling_sites": null, "j_sites_touched": null,
  "j_tempting_wrong_fix": "",
  "unverified": ["every guess you could not check in the code"]
}
```
Verdict rule: `build` needs a base shape, at least 2 distinct MiMo dismissal reasons, distance, and
no blocking red flag. `maybe` is missing one of those but could get it by a realistic injection.
Everything else is `reject`. Cite file:line for every claim.

Report back (under 200 words): the verdict, base shape, traps (one line each), red flags and unverified guesses.

---8<---
