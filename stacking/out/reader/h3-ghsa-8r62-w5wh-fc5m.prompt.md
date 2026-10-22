

# Read one stacking candidate (stacking-reader-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
A task pins the project before the published fix and gives a solver agent the code plus a short
report. Hidden behavioural tests then check the fix.

This study is about **stacked** tasks: one checkout holding several real, independent places where
a protection is missing, so that a correct fix needs several independent judgements.

You read ONE candidate and record, as facts with `path:line` evidence from the pinned code, what
stacking it supports. Describe each mechanism in one line, never as exploitation steps. Stay inside
the candidate's own advisories and repository.

## Inputs
- Candidate: {
 "b": "GHSA-8r62-w5wh-fc5m",
 "link": "regression",
 "a_ref": "CVE-2026-22689",
 "a": "GHSA-524m-q5m7-79mm",
 "status": "ready",
 "ecosystem": "Go",
 "package": "github.com/axllent/mailpit",
 "cwes": "CWE-177,CWE-200,CWE-346",
 "repo": "axllent/mailpit",
 "a_fix": "6f1f4f34c989",
 "b_fix": "fbe5e006c3f1",
 "a_published": "2026-01-13",
 "b_published": "2026-08-20",
 "summary": "Mailpit: WebSocket origin check bypass via percent-encoded path (regression of CVE-2026-22689)",
 "szz_status": "H3b-elsewhere"
}
- Screener record (a lead to verify, not a fact): none
- Pinned code: /Users/dev/.tb-graders/cwe/stacking/worktrees/h3-ghsa-8r62-w5wh-fc5m
- Difficulty priors per mechanism and model: ### 2.2 Proposed tiers (to be refitted from `research/trap_tally.tsv`)

The rates in the "Data" column count a trap as missed when it was missed in at least one run.
Per-run rates should replace them once the tally is filled.

| Tier | Per-run miss rate (target definition) | Kinds and cases in this tier today | Data |
|---|---|---|---|
| easy | under 10% | M12 spelling/encoding/verb variants; any trap whose surface the report describes; more routes of an accepted concept; planted M1/M2 under surface-describing reports | M12 0 misses; planted siblings 5/98 |
| medium | 10-25% | M1 parallel entry, M2 second implementation, M5 merged/defaults, M10 wrong object (under a general report) | M1 12/99, M2 14/73, M5 2/14, M10 2/11 |
| hard | 25-50% | M4 protection absent, M6 producer off path, M8 shape a check mishandles, M11 coupled value | M4 7/22, M6 5/17; airflow T10; sib2 C1 4/6 |
| xhard | at least 2/3 of a model's runs on that instance | M4 with a strong reason to dismiss; a deep how-type mechanism | sib catch-all DS 6/6; electron-builder-ds T4 DS 9/9; siyuan T6 DS 3/3; sib2 catch-all 6/6 both |

### 2.3 The two models miss different things

| Model | What it misses | Examples |
|---|---|---|
| DeepSeek | a route where the protection is absent and there is a reason to dismiss it | sib catch-all; siyuan T6; electron-builder-ds T4 |
| MiMo | coupled values (it over-hardens) and how-type mechanisms | sib2 C1 and the record id; airflow's over-broad zeros |

A trap's tier must therefore be recorded for each model separately.

## Mechanism codes (use exactly these)

| Code | Mechanism |
|---|---|
| M1 | another entry point reaching the same sink without the guard |
| M2 | a second, separate implementation of the guarded operation |
| M3 | the fix belongs in a shared lower layer; the symptom shows above it |
| M4 | a route where the protection never existed |
| M5 | the value arrives through defaults, merge, inheritance, patch or stored config |
| M6 | a data producer (schema, serializer, loader, table builder) feeding the check through a path the check never calls |
| M7 | ordering: the check runs after an adjustment, or after a side effect has already happened |
| M8 | a shape a plausible check mishandles (separator split, resolved vs lexical path, rename after the check, nested form) |
| M10 | wrong object: the check decides on a neighbouring or proxy object, or on an identity field the caller supplies |
| M11 | a coupled must-keep-working value next to a hidden one |

Pure spelling, encoding, verb, protocol or role variants are NOT traps. Do not record them.

## Steps
1. **State the protection(s).** Write one line per distinct protection. Bugs closed by the same guard
   are ONE protection.
2. **List every candidate trap:** each real place in the pinned code where a protection is missing.
   Do not stop at the first few. For each, record:
   - `mechanism` (code above) and `origin`: `advisory_route`, `published_fix_far_site`,
     `uncovered_upstream` or `injection_room`;
   - `locations`: path:line for each site (D3);
   - `reason_to_dismiss`: the one-line argument a solver could make for leaving it alone, or empty;
   - `distance`: files and packages from where a report would lead;
   - `protection_state`: `absent` (never existed), `weak` (exists, mishandles a case) or `bypassed`;
   - `tier_deepseek` and `tier_mimo`: easy, medium, hard or xhard, from the priors, adjusted for this
     instance (a strong reason to dismiss raises it; a route the report would have to point at lowers
     it);
   - `type`: `deepseek` (protection absent plus a reason to dismiss), `mimo` (a coupled value or a
     how-type mechanism), `both` or `neither`.
3. **Shared-guard check.** Group traps that one guard or one fix site would close. Each group counts
   as ONE trap. Report the number of independent groups.
4. **History** (H3 and H1/H2 candidates):
   - For H3: does the code of the earlier fix (A) leave the later bug (B) open? Does B live in code A
     wrote (regression) or elsewhere (incomplete)? Does fixing one bug uncover another (masking)?
   - For every candidate: was any bug fixed upstream by upgrading a dependency rather than in this
     repository? If so, can it be fixed in-repo?
5. **Interactions:**
   - **Conflicting fixes:** a pair where the natural fix for one trap breaks a must-keep-working value
     another needs.
   - **Masking:** a trap that only becomes reachable or visible once another is fixed.
6. **Fairness risks.** Name any must-keep-working behaviour that a security rule for these traps
   would contradict. Name any refused input shape that a legitimate use also needs.
7. **Effort:** minutes for a careful engineer who knows where to look to fix every independent trap.
8. **Verdict:**
   - `usable`: yes or no;
   - the best stacked design, meaning 3-5 independent traps with different reasons to dismiss,
     including at least one `deepseek`-type and one `mimo`-type;
   - why that design beats the others.

## Output (JSON only, to the output path)
```
{"candidate_id": "", "pattern": "H4|H3a|H3b|H3c|H1|H2", "repo": "", "pinned_commit": "",
 "protections": [""],
 "traps": [{"id": "T1", "mechanism": "M4", "origin": "", "locations": ["path:line"], "reason_to_dismiss": "",
            "distance": {"files": 0, "packages": 0}, "protection_state": "absent|weak|bypassed",
            "tier_deepseek": "", "tier_mimo": "", "type": "deepseek|mimo|both|neither", "evidence": ["path:line"]}],
 "independent_groups": [["T1"], ["T2", "T3"]],
 "history": {"a_fix_leaves_b_open": null, "b_in_code_a_wrote": null, "masking": [], "dependency_bump_fix": false, "in_repo_fix_possible": null},
 "conflicts": [{"a": "T1", "b": "T2", "what": ""}],
 "fairness_risks": [""],
 "effort_minutes": 0,
 "usable": true, "design": {"traps": ["T1", "T2", "T3"], "why": ""},
 "unverified": [""]}
```
Every claim needs `path:line` evidence from the pinned code, or goes in `unverified`.


## This run
- candidate_id: `h3-ghsa-8r62-w5wh-fc5m`; pattern: `H3b`; repo: `axllent/mailpit`; pinned_commit: `877a9159ceeaf380d5bb0e1d84017b24d2e7b361`.
- Read only under `/Users/dev/.tb-graders/cwe/stacking/worktrees/h3-ghsa-8r62-w5wh-fc5m`. Write exactly one file: `/Users/dev/terminal-bench/cwe-bench/stacking/out/reader/h3-ghsa-8r62-w5wh-fc5m.json` (valid JSON matching the Output schema). Do not write anywhere else.
