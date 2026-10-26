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

Project root: `/home/mara/cwe-bench`. Task: `stk-git-js-14793`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 14793; incomplete denylist (CWE-184) in an unsafe-argv guard leading to OS co
- Pinned (vulnerable) commit: 76f308ed445013d8dd973bc515e7815b59426e3e. Published fix: d762810c13b331ff1e5eb24c0b434646d2a8d1b3.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-14793",
 "pattern": "H4",
 "repo": "steveukx/git-js",
 "pinned_commit": "76f308ed445013d8dd973bc515e7815b59426e3e",
 "protections": [
  "Config-write key denylist: every key collected from `git config` positionals, inline `-c`/`--config`/`--config-env` and GIT_CONFIG_COUNT env is matched against preventUnsafeConfig before any child process is spawned (packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:4-15,39-72; packages/argv-parser/src/config/analyse-config.ts:52-85; packages/argv-parser/src/env/parse-env.ts:31-41).",
  "Command-line flag denylist: every parsed global/task flag name is matched against preventUnsafeFlags and reported with the unsafe category the caller must opt into (packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:4-16,65-79).",
  "Tokeniser option schema: which short clusters expand into individual switches and which long switches consume the next token is declared per command in flag-specs.ts, so a switch the table does not know reaches the flag denylist only as one opaque token or with no value attached (packages/argv-parser/src/tokens/flag-specs.ts:43-102; packages/argv-parser/src/tokens/token-expander.ts:23-65; packages/argv-parser/src/flags/parse-task-flags.ts:48).",
  "Single enforcement point: simple-git's spawn.args plugin throws for every produced vulnerability unless the matching unsafe category is enabled, and every typed task and raw() route funnels through it (simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts:11-21; simple-git/src/git.mjs:189-193)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:39",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:70",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:72",
    "packages/argv-parser/src/config/analyse-config.ts:52",
    "packages/argv-parser/src/env/parse-env.ts:31"
   ],
   "reason_to_dismiss": "The docs call the blocks a non-exhaustive safety net that does not protect against every injection or misuse (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12), and trailer.<token>.command is a per-token formatting feature rather than one of the documented command-binary rows, so the key can be argued out of the list.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:39-72",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:34-37",
    "packages/argv-parser/src/vulnerabilities/vulnerability.types.ts:19-23",
    "packages/argv-parser/src/config/analyse-config.ts:57-63",
    "packages/argv-parser/src/env/parse-env.ts:37-39"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:65",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:71",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:79",
    "simple-git/src/git.mjs:189"
   ],
   "reason_to_dismiss": "The rebase -x/--exec half is a separately credited report bundled in the same commit, so it can be dismissed as a different vulnerability than the trailer config key, and the docs only promise known high-risk patterns (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:65-79",
    "simple-git/src/git.mjs:189-193",
    "packages/argv-parser/src/args/parse-argv.ts:14-20"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M6",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/argv-parser/src/tokens/flag-specs.ts:43",
    "packages/argv-parser/src/tokens/flag-specs.ts:93",
    "packages/argv-parser/src/tokens/token-expander.ts:44",
    "packages/argv-parser/src/flags/parse-task-flags.ts:48"
   ],
   "reason_to_dismiss": "The option table is a lower-level parsing schema rather than a security check, so a single denylist row is argued to be the whole fix; the report does not mention clustered (-qx/-ix) or value-embedded (-xcmd) switch shapes.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "packages/argv-parser/src/tokens/token-expander.ts:44-47",
    "packages/argv-parser/src/tokens/flag-specs.ts:87-90",
    "packages/argv-parser/test/parse-flags.spec.ts:33-37",
    "packages/argv-parser/test/attack-vectors.spec.ts:63-67"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/argv-parser/src/config/detect-config-action.ts:43",
    "packages/argv-parser/src/config/detect-config-action.ts:49",
    "packages/argv-parser/src/config/config-operands.ts:6",
    "packages/argv-parser/src/config/analyse-config.ts:96"
   ],
   "reason_to_dismiss": "A section rename is a structural edit, not a trailer.<token>.cmd write; the report only shows plain key/value writes and the docs cover known patterns only (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "packages/argv-parser/src/config/detect-config-action.ts:42-55",
    "packages/argv-parser/test/parse-config-write.spec.ts:55-59",
    "packages/argv-parser/src/config/config-operands.ts:2-11"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:71",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:73",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:63",
    "packages/argv-parser/src/tokens/flag-specs.ts:43"
   ],
   "reason_to_dismiss": "A broad /--exec/ or /-x/ matcher appears to cover the push and rebase spellings at once, and a duplicate category or a task-agnostic short-switch rule looks like harmless over-approximation.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "packages/argv-parser/test/vulnerability-analysis.spec.ts:135-144",
    "packages/argv-parser/test/vulnerability-analysis.spec.ts:218-223",
    "simple-git/test/unit/clean.spec.ts:110-112",
    "simple-git/test/unit/clean.spec.ts:191-193",
    "packages/argv-parser/src/tokens/flag-specs.ts:43-91"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/argv-parser/src/flags/parse-task-flags.ts:34",
    "packages/argv-parser/src/flags/parse-task-flags.ts:35",
    "packages/argv-parser/src/config/detect-config-action.ts:21",
    "packages/argv-parser/src/args/parse-argv.types.ts:62"
   ],
   "reason_to_dismiss": "`--` is the documented separator for path-like arguments and everything after it is deliberately treated as a path (packages/argv-parser/src/args/parse-argv.types.ts:62-65), which looks outside a config-key denylist; the report is about key classification, not argument separation.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "packages/argv-parser/test/parse-paths.spec.ts:45-49",
    "packages/argv-parser/src/config/detect-config-action.ts:35-39",
    "simple-git/src/lib/plugins/suffix-paths.plugin.ts:23-33"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:39",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:47",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:70"
   ],
   "reason_to_dismiss": "core.alternateRefsCommand is not named by the advisory and only runs when an alternate object store is advertised, so it can be written off as outside the trailer/rebase reports (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:41-47",
    "packages/argv-parser/src/vulnerabilities/vulnerability.types.ts:19-23"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M1",
   "origin": "injection_room",
   "locations": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:65",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:71"
   ],
   "reason_to_dismiss": "The config-side difftool.<tool>.cmd key is already blocked, so the command-line -x/--extcmd spelling of the same difftool feature looks covered; difftool is also a display command rather than a repository operation.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:65-79",
    "packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:51"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T7"
  ],
  [
   "T2",
   "T5",
   "T8"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T6"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T2",
   "b": "T5",
   "what": "A task-agnostic /--exec/ or /^-?x/ row added for rebase also fires for push --exec (already allowUnsafePack), for the --exec-path getter that must stay silent, and for git clean -x / git.clean('dfx'), so the natural broad fix breaks existing behaviour."
  },
  {
   "a": "T3",
   "b": "T5",
   "what": "To make -x visible inside -qx/-ix clusters the rebase option table must declare the benign sibling switches and keep -s/-X as value-takers; a case-insensitive matcher would turn the legitimate -X <option> into -x."
  },
  {
   "a": "T1",
   "b": "T7",
   "what": "Both are closed from the same flat array; a coarse row such as preventConfigBuilder('trailer') or a bare 'core' prefix would close them but refuse legitimate trailer.<token>.key/trailer.separators writes and most core.* writes."
  }
 ],
 "fairness_risks": [
  "git clean -x and git.clean('dfx') must keep working (simple-git/test/unit/clean.spec.ts:110-112,191-193); a task-agnostic -x rule contradicts it.",
  "git rev-parse --exec-path used as a getter must stay unflagged (packages/argv-parser/test/vulnerability-analysis.spec.ts:218-223; detect-vulnerable-flags.ts:63); a broad /--exec/ rule contradicts it.",
  "git push --exec=<pack> must keep yielding exactly allowUnsafePack (detect-vulnerable-flags.ts:71; vulnerability-analysis.spec.ts:135-144); a second global row produces two vulnerabilities.",
  "git rebase -s <strategy> and -X <option> are legitimate neighbours of -x; the short-option maps are case-sensitive (packages/argv-parser/src/tokens/flag-specs.ts:43-91), so -X must not be treated as -x.",
  "Legitimate trailer.<token>.key/.where/.ifExists/.ifMissing/.layout and trailer.separators writes share the trailer section with the command keys, so the fix must target .cmd/.command only and not the whole trailer namespace.",
  "git config -- <key> <value> is legitimate (it is how names beginning with '-' are written); the separator fix must re-admit positionals after '--' for the config task, not refuse '--' outright.",
  "git clone --config key=value is a legitimate clone option already parsed through the same inline-write path (packages/argv-parser/test/parse-config-inline.spec.ts:45-50; packages/argv-parser/src/tokens/flag-specs.ts:55) and must not be refused wholesale."
 ],
 "effort_minutes": 70,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T6"
  ],
  "why": "It pairs the one report-described anchor (T1: trailer.<token>.cmd/.command, with the injection-room sibling T7 in the same list) with four hidden judgements in three layers: the separately credited rebase half (T2, carrying T5's coupling and T8's sibling option), the tokeniser schema that only emits -x from clusters (T3), the rename-section operand that records the source section instead of the destination (T4), and the '--' separator that drops config positionals entirely (T6). The reasons to dismiss are all different (non-exhaustive docs, different advisory, lower-level parsing schema, structural edit, path separator), T2/T4/T6 give the deepseek absent-protection-plus-dismissal shape and T3/T5 give the mimo how-type/coupled shape, and T2/T5/T8 force the fix to stay task- and case-specific so git clean -x, push --exec, the --exec-path getter and rebase -X keep working. A design built only from the two published halves is one judgement (append rows to two lists) and is fully derivable from the fix commit; this one also requires reading the parser's separator, operand and tokeniser behaviour."
 },
 "unverified": [
  "The fix commit d762810c13b331ff1e5eb24c0b434646d2a8d1b3 is not present in the pinned worktree; fix_sites and the claim that the fix leaves the rename/separator routes untouched come from the screener lead rather than the patch itself.",
  "Pinned code omits 'config' from the GLOBAL long-option set (packages/argv-parser/src/tokens/flag-specs.ts:31-40) while analyse-config.ts:39 treats '--config' as a write source, so a space-separated global `--config <k=v>` is never collected; whether git accepts that exact global form cannot be checked from the pinned tree, so it is not scored as a trap.",
  "core.alternateRefsCommand's shell-execution semantics are external git behaviour; pinned evidence is only that no row or other guard names it (detect-vulnerable-config-writes.ts:39-72).",
  "git difftool -x/--extcmd and git grep -O/--open-files-in-pager were noticed as further unguarded command-naming options; only difftool -x is recorded as a trap and grep -O was not verified.",
  "No latest release tree was supplied, so present_in_latest/latest_where for T4, T6, T7 and T8 are unknown.",
  "Whether the hidden behavioural tests require a real git binary at runtime; the project's own unit tests drive fixture child-process streams."
 ]
}
  ```
- Published fix sites:   - packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:39 — T1 M4 (reason to dismiss: The docs call the blocks a non-exhaustive safety net that does not protect against every injection or misuse (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12), and trailer.<token>.command is a per-token formatting feature rather than one of the documented command-binary rows, so the key can be argued out of the list.)
  - packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:70 — T1 M4 (reason to dismiss: The docs call the blocks a non-exhaustive safety net that does not protect against every injection or misuse (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12), and trailer.<token>.command is a per-token formatting feature rather than one of the documented command-binary rows, so the key can be argued out of the list.)
  - packages/argv-parser/src/vulnerabilities/detect-vulnerable-config-writes.ts:72 — T1 M4 (reason to dismiss: The docs call the blocks a non-exhaustive safety net that does not protect against every injection or misuse (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12), and trailer.<token>.command is a per-token formatting feature rather than one of the documented command-binary rows, so the key can be argued out of the list.)
  - packages/argv-parser/src/config/analyse-config.ts:52 — T1 M4 (reason to dismiss: The docs call the blocks a non-exhaustive safety net that does not protect against every injection or misuse (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12), and trailer.<token>.command is a per-token formatting feature rather than one of the documented command-binary rows, so the key can be argued out of the list.)
  - packages/argv-parser/src/env/parse-env.ts:31 — T1 M4 (reason to dismiss: The docs call the blocks a non-exhaustive safety net that does not protect against every injection or misuse (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12), and trailer.<token>.command is a per-token formatting feature rather than one of the documented command-binary rows, so the key can be argued out of the list.)
  - packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:65 — T2 M4 (reason to dismiss: The rebase -x/--exec half is a separately credited report bundled in the same commit, so it can be dismissed as a different vulnerability than the trailer config key, and the docs only promise known high-risk patterns (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).)
  - packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:71 — T2 M4 (reason to dismiss: The rebase -x/--exec half is a separately credited report bundled in the same commit, so it can be dismissed as a different vulnerability than the trailer config key, and the docs only promise known high-risk patterns (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).)
  - packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:79 — T2 M4 (reason to dismiss: The rebase -x/--exec half is a separately credited report bundled in the same commit, so it can be dismissed as a different vulnerability than the trailer config key, and the docs only promise known high-risk patterns (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).)
  - simple-git/src/git.mjs:189 — T2 M4 (reason to dismiss: The rebase -x/--exec half is a separately credited report bundled in the same commit, so it can be dismissed as a different vulnerability than the trailer config key, and the docs only promise known high-risk patterns (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).)
  - packages/argv-parser/src/tokens/flag-specs.ts:43 — T3 M6 (reason to dismiss: The option table is a lower-level parsing schema rather than a security check, so a single denylist row is argued to be the whole fix; the report does not mention clustered (-qx/-ix) or value-embedded (-xcmd) switch shapes.)
  - packages/argv-parser/src/tokens/flag-specs.ts:93 — T3 M6 (reason to dismiss: The option table is a lower-level parsing schema rather than a security check, so a single denylist row is argued to be the whole fix; the report does not mention clustered (-qx/-ix) or value-embedded (-xcmd) switch shapes.)
  - packages/argv-parser/src/tokens/token-expander.ts:44 — T3 M6 (reason to dismiss: The option table is a lower-level parsing schema rather than a security check, so a single denylist row is argued to be the whole fix; the report does not mention clustered (-qx/-ix) or value-embedded (-xcmd) switch shapes.)
  - packages/argv-parser/src/flags/parse-task-flags.ts:48 — T3 M6 (reason to dismiss: The option table is a lower-level parsing schema rather than a security check, so a single denylist row is argued to be the whole fix; the report does not mention clustered (-qx/-ix) or value-embedded (-xcmd) switch shapes.)
  - packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:71 — T5 M11 (reason to dismiss: A broad /--exec/ or /-x/ matcher appears to cover the push and rebase spellings at once, and a duplicate category or a task-agnostic short-switch rule looks like harmless over-approximation.)
  - packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:73 — T5 M11 (reason to dismiss: A broad /--exec/ or /-x/ matcher appears to cover the push and rebase spellings at once, and a duplicate category or a task-agnostic short-switch rule looks like harmless over-approximation.)
  - packages/argv-parser/src/vulnerabilities/detect-vulnerable-flags.ts:63 — T5 M11 (reason to dismiss: A broad /--exec/ or /-x/ matcher appears to cover the push and rebase spellings at once, and a duplicate category or a task-agnostic short-switch rule looks like harmless over-approximation.)
  - packages/argv-parser/src/tokens/flag-specs.ts:43 — T5 M11 (reason to dismiss: A broad /--exec/ or /-x/ matcher appears to cover the push and rebase spellings at once, and a duplicate category or a task-agnostic short-switch rule looks like harmless over-approximation.)
- Uncovered routes to confirm (pattern B):   - packages/argv-parser/src/config/detect-config-action.ts:43 — T4 M10 (reason to dismiss: A section rename is a structural edit, not a trailer.<token>.cmd write; the report only shows plain key/value writes and the docs cover known patterns only (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).)
  - packages/argv-parser/src/config/detect-config-action.ts:49 — T4 M10 (reason to dismiss: A section rename is a structural edit, not a trailer.<token>.cmd write; the report only shows plain key/value writes and the docs cover known patterns only (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).)
  - packages/argv-parser/src/config/config-operands.ts:6 — T4 M10 (reason to dismiss: A section rename is a structural edit, not a trailer.<token>.cmd write; the report only shows plain key/value writes and the docs cover known patterns only (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).)
  - packages/argv-parser/src/config/analyse-config.ts:96 — T4 M10 (reason to dismiss: A section rename is a structural edit, not a trailer.<token>.cmd write; the report only shows plain key/value writes and the docs cover known patterns only (docs/PLUGIN-UNSAFE-ACTIONS.md:11-12).)
  - packages/argv-parser/src/flags/parse-task-flags.ts:34 — T6 M8 (reason to dismiss: `--` is the documented separator for path-like arguments and everything after it is deliberately treated as a path (packages/argv-parser/src/args/parse-argv.types.ts:62-65), which looks outside a config-key denylist; the report is about key classification, not argument separation.)
  - packages/argv-parser/src/flags/parse-task-flags.ts:35 — T6 M8 (reason to dismiss: `--` is the documented separator for path-like arguments and everything after it is deliberately treated as a path (packages/argv-parser/src/args/parse-argv.types.ts:62-65), which looks outside a config-key denylist; the report is about key classification, not argument separation.)
  - packages/argv-parser/src/config/detect-config-action.ts:21 — T6 M8 (reason to dismiss: `--` is the documented separator for path-like arguments and everything after it is deliberately treated as a path (packages/argv-parser/src/args/parse-argv.types.ts:62-65), which looks outside a config-key denylist; the report is about key classification, not argument separation.)
  - packages/argv-parser/src/args/parse-argv.types.ts:62 — T6 M8 (reason to dismiss: `--` is the documented separator for path-like arguments and everything after it is deliberately treated as a path (packages/argv-parser/src/args/parse-argv.types.ts:62-65), which looks outside a config-key denylist; the report is about key classification, not argument separation.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4, T6. Why: It pairs the one report-described anchor (T1: trailer.<token>.cmd/.command, with the injection-room sibling T7 in the same list) with four hidden judgements in three layers: the separately credited rebase half (T2, carrying T5's coupling and T8's sibling option), the tokeniser schema that only emits -x from clusters (T3), the rename-section operand that records the source section instead of the destination (T4), and the '--' separator that drops config positionals entirely (T6). The reasons to dismiss are all different (non-exhaustive docs, different advisory, lower-level parsing schema, structural edit, path separator), T2/T4/T6 give the deepseek absent-protection-plus-dismissal shape and T3/T5 give the mimo how-type/coupled shape, and T2/T5/T8 force the fix to stay task- and case-specific so git clean -x, push --exec, the --exec-path getter and rebase -X keep working. A design built only from the two published halves is one judgement (append rows to two lists) and is fully derivable from the fix commit; this one also requires reading the parser's separator, operand and tokeniser behaviour. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): git clean -x and git.clean('dfx') must keep working (simple-git/test/unit/clean.spec.ts:110-112,191-193); a task-agnostic -x rule contradicts it. | git rev-parse --exec-path used as a getter must stay unflagged (packages/argv-parser/test/vulnerability-analysis.spec.ts:218-223; detect-vulnerable-flags.ts:63); a broad /--exec/ rule contradicts it. | git push --exec=<pack> must keep yielding exactly allowUnsafePack (detect-vulnerable-flags.ts:71; vulnerability-analysis.spec.ts:135-144); a second global row produces two vulnerabilities. | git rebase -s <strategy> and -X <option> are legitimate neighbours of -x; the short-option maps are case-sensitive (packages/argv-parser/src/tokens/flag-specs.ts:43-91), so -X must not be treated as -x. | Legitimate trailer.<token>.key/.where/.ifExists/.ifMissing/.layout and trailer.separators writes share the trailer section with the command keys, so the fix must target .cmd/.command only and not the whole trailer namespace. | git config -- <key> <value> is legitimate (it is how names beginning with '-' are written); the separator fix must re-admit positionals after '--' for the config task, not refuse '--' outright. | git clone --config key=value is a legitimate clone option already parsed through the same inline-write path (packages/argv-parser/test/parse-config-inline.spec.ts:45-50; packages/argv-parser/src/tokens/flag-specs.ts:55) and must not be refused wholesale.. Conflicts the reader found: A task-agnostic /--exec/ or /^-?x/ row added for rebase also fires for push --exec (already allowUnsafePack), for the --exec-path getter that must stay silent, and for git clean -x / git.clean('dfx'), so the natural broad fix breaks existing behaviour. | To make -x visible inside -qx/-ix clusters the rebase option table must declare the benign sibling switches and keep -s/-X as value-takers; a case-insensitive matcher would turn the legitimate -X <option> into -x. | Both are closed from the same flat array; a coarse row such as preventConfigBuilder('trailer') or a bare 'core' prefix would close them but refuse legitimate trailer.<token>.key/trailer.separators writes and most core.* writes.

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

## Environment (`tasks/stk-git-js-14793/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-git-js-14793/instruction.md`)
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

## Tests (`tasks/stk-git-js-14793/tests/`)
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
- **Wrong-fix patches** go in `build/stk-git-js-14793/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-git-js-14793/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-git-js-14793/manifest.json`:**
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

**Also in `build/stk-git-js-14793/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-git-js-14793 --only static
python3 -I common/gate/gate.py stk-git-js-14793 --only nop
python3 -I common/gate/gate.py stk-git-js-14793 --only oracle
python3 -I common/gate/gate.py stk-git-js-14793 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-git-js-14793/`;
  - edit only `tasks/stk-git-js-14793/`, `build/stk-git-js-14793/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-14793.json`. Verify each trap on the
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

Stacked task slug: `stk-git-js-14793`. Control task slug: `stk-git-js-14793-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-14793.json`.
