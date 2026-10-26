# FAIRNESS — stk-gitpython-ghsawvpp

Read: `instruction.md`, every test in `tasks/stk-gitpython-ghsawvpp/tests/`, `solution/fix.patch`,
`manifest.json`, `notes.md`, all ten `checks/*.patch`. Nothing was run.

Abbreviations used in the tables:

- **INV** — “No value supplied by a caller among the options that reach git may cause git to run a
  program of the caller’s choosing, or to write to a filesystem path of the caller’s choosing.”
- **REF** — “Refuse by raising the library’s existing error for a disallowed option, before the
  operation has any effect. A refused operation must leave no filesystem change behind.”
- **KEEP** — “Everything that works today keeps working exactly as it does today: ordinary
  operations with legitimate options, the library’s public interfaces, and their documented error
  behaviour.”

Graded set: 8 security, 8 hidden functional, 20 project tests (`-k 'unsafe or option_candidates or
rename'`; the other project tests in those files never run).

## 1. Test-by-test fairness

| test | what it asserts | covering instruction sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `security/test_option_injection.py::test_clone_refuses_dash_prefixed_option_value` | `clone_from(..., n="--upload-pack=<prog>")` raises `UnsafeOptionError`; marker and destination absent | INV (caller value → program) + REF | **no** — screening in the shared candidate builder, in the rendered-token layer, or at the dispatcher all raise before git starts and leave no destination | low |
| `...::test_clone_refuses_dash_prefixed_sequence_value` | same via `n=["--upload-pack=<prog>"]` | INV + “Fix the problem and its close variants” | **no** — same layers; sequences are the same value class | low |
| `...::test_clone_refuses_joined_single_char_value` | `split_single_char_options=False`, `n="u<prog>"` raises; no marker/destination | INV + close variants; `split_single_char_options` is the repo’s public rendering knob | **no** — a guard on the rendered token (existing clustered walk) or a dispatcher guard catches `-nu<prog>` | low |
| `...::test_clone_refuses_joined_single_char_sequence_value` | same with `n=["u<prog>"]` | INV + close variants | **no** — same | low |
| `...::test_archive_refuses_dash_prefixed_option_value` | `archive(stream, "HEAD", v="--output=<path>")` raises; path absent | INV (write to caller’s path) + REF | **no** — archive already routes through the shared builder and its unsafe list already names the output option (proven by the reference passing); builder, handler or dispatcher guard all pass | low |
| `...::test_remote_listing_refuses_program_option_value` | `ls_remote(source, exec=<prog>)` raises; marker absent | INV (caller value → program) + standard expert knowledge: `--exec` is git-ls-remote’s documented backward-compatibility alias of `--upload-pack` (the graded project test also normalizes `exec`→`--exec`, though it could not be confirmed that this test is in the pinned checkout the solver sees) | **no** — adding the alias to the existing remote-listing blocklist, or any token-level guard, passes; the alias is not named in the instruction, so a thorough engineer must know/check git, not the task | medium |
| `...::test_diff_refuses_option_value_writing_a_file` | `commit.diff(other, output=<path>)` raises; path absent | INV (write to caller’s path) + close variants | **no** — screening in `Diffable.diff`, in `_call_process`, or at the dispatcher with the same option list passes | low |
| `...::test_diff_refuses_option_value_writing_a_file_when_short_options_are_joined` | same with `output=` under split rendering | INV + REF | **no** — `output` is multi-character, so the token is unchanged and any of the same layers catches it | low |
| `functional/test_legitimate_use.py::test_clone_with_origin_name` | `clone_from(..., o="upstream")` clones with that remote | KEEP | **no** — plain value, no security rule forbids it | low |
| `...::test_clone_with_joined_safe_short_option` | `multi_options=["-oupstream"]` works | KEEP (the coupled value) | **no** — the short-token walk stops at non-clusterable `o`; the same token rule is exercised by the project tests | low |
| `...::test_option_screening_accepts_attached_safe_short_values` | `Git.check_unsafe_options(["-oupstream","-bcurrent"], [...])` does not raise | KEEP (“public interfaces”; the repo’s own visible tests call this helper) | **no** — keeping the existing helper is required by KEEP; deleting/renaming it is a public-interface break a correct fix does not make | low |
| `...::test_diff_accepts_joined_similarity_value` | `M="75%"` with split rendering gives the rename | KEEP | **no** — `-M75%` is not a refused char/token | low |
| `...::test_diff_accepts_common_options` | `R=True, find_renames=True` returns the expected paths | KEEP | **no** | low |
| `...::test_archive_writes_the_requested_format` | `format="tar"` writes a tar stream | KEEP | **no** | low |
| `...::test_remote_listing_lists_references` | `ls_remote(source)` and `ls_remote("--heads", source)` list refs | KEEP | **no** — `--heads` is neither a program option nor a write option | low |
| `...::test_clone_still_accepts_a_safe_single_char_value` | `b="main"` clones | KEEP | **no** | low |
| `functional/project/test_git.py::test_check_unsafe_options_normalizes_kwargs` | the existing helper rejects the listed name/spelling cases, including `exec`→`--exec` and `--out=`→`--output` | KEEP (public interface, documented error behaviour) | **no** — the reference reuses the helper unchanged | low |
| `...::test_check_unsafe_options_does_not_treat_short_options_as_abbreviations` | short tokens are exact-match only | KEEP | **no** | low |
| `...::test_check_unsafe_options_does_not_treat_option_values_as_abbreviations` | a value equal to an unsafe name is not an option | KEEP | **no** | low |
| `...::test_check_unsafe_options_rejects_joined_unsafe_short_options` | clustered unsafe short chars raise | KEEP | **no** | low |
| `...::test_check_unsafe_options_allows_attached_safe_short_option_values` | `-oupstream`, `-bcurrent` accepted | KEEP (coupled value) | **no** | low |
| `...::test_option_candidates_ignore_untransformed_kwargs` | the private candidate builder ignores None/False/empty values | KEEP (“everything that works today”) | **no** — the reference extends it compatibly; the test is visible in the repo | low |
| `functional/project/test_clone.py::test_clone_unsafe_options` | `multi_options` and kwarg spellings raise `UnsafeOptionError`, no marker | KEEP (documented error behaviour) | **no** | low |
| `...::test_clone_unsafe_options_abbreviated` | abbreviated spellings raise | KEEP | **no** | low |
| `...::test_clone_unsafe_options_are_checked_after_splitting_multi_options` | a payload string with two options is refused | KEEP | **no** | low |
| `...::test_clone_unsafe_options_allowed` | the `allow_unsafe_options=True` bypass still runs the option | KEEP (public interface/error behaviour) | **no** — the reference preserves the bypass | low |
| `...::test_clone_from_unsafe_options` | `Repo.clone_from` kwarg spellings raise | KEEP | **no** | low |
| `...::test_clone_from_unsafe_options_are_checked_after_splitting_multi_options` | split payload refused | KEEP | **no** | low |
| `...::test_clone_from_unsafe_options_allowed` | bypass still works on `clone_from` | KEEP | **no** | low |
| `...::test_clone_from_unsafe_protocol` | protocol refusal unchanged | KEEP (documented error behaviour) | **no** — unrelated to option screening | low |
| `...::test_clone_from_checks_polished_url_for_unsafe_protocol` | polished URL checked, process not called | KEEP | **no** | low |
| `...::test_clone_from_unsafe_protocol_allowed` | protocol bypass still works | KEEP | **no** | low |
| `...::test_clone_from_unsafe_protocol_allowed_and_enabled` | protocol bypass with config option works | KEEP | **no** | low |
| `functional/project/test_diff.py::test_diff_with_rename` | patch/raw rename parsing unchanged | KEEP | **no** — parser-only, no git options | low |
| `...::test_diff_unsafe_paths` | unsafe path parsing unchanged | KEEP | **no** — parser-only | low |
| `...::test_rename_override` | diff rename thresholds, including `split_single_char_options=False, M="75%"`, still behave | KEEP | **no** — the reference allows `-M…` | low |

No row is “yes”; no row is an unresolved “maybe”.

## 2. Leniency (quality, non-blocking)

**Properties.** P1 = no caller value may run a program; P2 = no caller value may write a
caller-chosen path.

| trap | most plausible WRONG fix | caught? |
|---|---|---|
| T1 clone values | screen only the keyword *name* (pinned code) | yes — four clone security tests; `checks/missing_candidate_builder.patch` (5 security fail) |
| T1 clone values | handle scalars, not sequences; or split rendering only, not joined | yes — the sequence and joined tests each fail |
| T1 clone values | check after the clone destination is prepared | yes — destination/marker assertions |
| T2 archive | fix the clone handler only, leave the shared builder | yes — archive test; `missing_candidate_builder.patch` |
| T2 archive | add the `output=` kwarg name to archive’s list only | yes — the test smuggles it as `v="--output=…"` |
| T5 remote alias | block `--upload-pack` spellings only (pin; A alone; A+B) | yes — `test_remote_listing_refuses_program_option_value`; `missing_remote_alias.patch` (0.875) |
| T5 remote alias | value-based screening (dash-prefixed values) without the alias | yes — the program path does not start with `-` |
| T6 diff | no guard / guard only when options are split | yes — both diff tests; `missing_diff_guard.patch` (0.75) |
| T7 coupled values | over-broad character scan of short tokens | yes — `checks/adjacent_api.patch` (3 functional fail) |
| T7 coupled values | refuse the joined rendering outright | yes — `test_diff_accepts_joined_similarity_value` and project `test_rename_override` |
| T7 coupled values | refuse every option (refuse_all) or a bare error (crash_as_refusal) | yes — `checks/refuse_all.patch`, `checks/crash_as_refusal.patch` |

**Wrong fixes no test catches**

1. Screening only the **first element** of a sequence value: every sequence security test passes a
   one-element list, so a `values[0]`-only check scores 1.0.
2. A diff guard that hardcodes the `output` name instead of the token/abbreviation:
   `diff(out=<path>)` (git abbreviates `--out` to `--output`) still writes, and only `output=` is
   tested.
3. Adding `--exec` to the remote-listing blocklist only (which the reference does): `Remote.fetch`
   and `Remote.pull` keep the old blocklist, and no test exercises `fetch/pull(exec=…)`.
   `checks/hardening.patch` closes this but only has to *pass*; nothing requires it.
4. Hand-rolled per-command string matching that misses abbreviations (`--upl=`, `--exe=`) on
   remote listing; only the exact `exec=` kwarg is tested there.
5. Refusing only values that look like absolute paths: the payload program is always the absolute
   `tmp_path/payload.sh`, so a bare command name (PATH lookup) is untested.
6. A blanket refusal of every dash-prefixed caller value: no graded functional test supplies a
   dash-prefixed value of a long option, so an over-broad fix that breaks such legitimate use still
   scores 1.0.
7. Tuple-valued kwargs on the split path are untested (lists only).

## 3. Hints (quality, non-blocking)

- “The example above is an example, not the full set.” — signals a multi-item variant list
  (flaw count > 1). **Delete**; “Fix the problem and its close variants” already states generality.
- “The option dictionary was passed through to the library unchanged, and the library invoked git
  with it.” — paraphrases the sink mechanism (nothing screens it). **Replace** with the effect-only
  sentence already present: keep “With a crafted option, a user made our server run a program of
  their choosing on the host.”
- “for example, a service that lets a user pick clone options for a repository it fetches on their
  behalf” — names the reported entry point. **Neutral:** “for example, a service that lets a user
  pick options for an operation it performs on their behalf.”
- “Do not special-case the example.” — confirms that more than the example exists. **Fold** into
  “Fix the problem and its close variants.”

## 3a. Required: generalize

**none.** No sentence locates a sibling, far site or uncovered route (archive, remote listing,
diff, output options, joined rendering, aliases are all absent), and no general word doubles as the
name of one stage or entry point. The only operation named (“clone”) is the reported route, handled
above as a hint, not a checklist entry.

## 4. Realism (quality, non-blocking)

T1 is the advisory route through `Repo.clone_from`; T2 is the same shared builder one file away;
T5 and T6 are real, unmodified upstream code at the pin (`--exec` accepted by git 2.47.3; diff
forwards `--output`), verified by the build and later closed upstream — realistic by definition.
T7’s coupled values (`-oupstream`, `-bcurrent`, `-M75%`) are upstream public, tested behaviour. The
fixtures build repositories and a harmless marker program with the git CLI/stdlib, and every
concept is driven through its public entry point (`Repo.clone_from`, `Repo.archive`,
`Git.ls_remote`, `Commit.diff`). Nothing looks planted or contrived; the reference’s defensive
`-o` in the diff list is unreachable in git 2.47.3 but harmless.

## Stacking checks

**S1 — coupled traps (gate a: no failure)**

| must-keep value (test) | covering clause | security rule forbids it? |
|---|---|---|
| `o="upstream"` (`test_clone_with_origin_name`) | KEEP | no — plain value; INV is about program runs/path writes |
| `multi_options=["-oupstream"]` (`test_clone_with_joined_safe_short_option`) | KEEP | no |
| `-oupstream`, `-bcurrent` (`test_option_screening_accepts_attached_safe_short_values`) | KEEP | no |
| `-M75%` (`test_diff_accepts_joined_similarity_value`, project `test_rename_override`) | KEEP | no |
| `R=True`, `find_renames=True` (`test_diff_accepts_common_options`) | KEEP | no |
| `format="tar"` (`test_archive_writes_the_requested_format`) | KEEP | no |
| `ls_remote(source)`, `ls_remote("--heads", source)` (`test_remote_listing_lists_references`) | KEEP | no |
| `b="main"` (`test_clone_still_accepts_a_safe_single_char_value`) | KEEP | no |

No contradiction: every value is outside INV’s two protected outcomes.

**S2 — shape traps (gate a: no failure)**

| refused shape | outside the legitimate set? |
|---|---|
| dash-prefixed scalar value of a one-char kwarg | yes — legitimate values shown are plain (`b="main"`, `o="upstream"`, `M="75%"`, `format="tar"`); a value that becomes its own option token is the INV vector |
| dash-prefixed sequence element | yes — same |
| joined `-<char><prog>` token | yes — legitimate joined values are attached safe values (`-oupstream`, `-bcurrent`, `-M75%`); the refused token’s first short char is an unsafe option char |
| archive `v="--output=<path>"` | yes — the legitimate archive value is plain (`format="tar"`) |
| `ls_remote(exec=<prog>)` | yes — caller-chosen program, exactly INV’s first outcome |
| diff `output=<path>` | yes — caller-chosen write path, exactly INV’s second outcome |

No stated character set or leading-slash rule exists, so the two example traps do not arise.

**S3 — fixtures and harness (gate a: no failure).** Every state set up is legitimate: an ordinary
two-commit repository with a rename, and a harmless marker program — no enabled/published/config
state is asserted as legitimate. The harness drives each concept through the real public entry
point, and both the reference (builder-level) and `checks/alternative.patch` (call-site token
screening) score 1.0, so a correct guard at either valid layer passes.

**S4 — concept independence (gate a: no failure).**

| concept | own fix passes its tests alone? | fails on pin through its own route? |
|---|---|---|
| C1 `[T1,T2,T7]` | yes (builder patch; 8/8 with the rest) | yes — 5 security tests fail (`missing_candidate_builder` shows 5 fail with C2/C3 in place) |
| C2 `[T5]` | yes (`missing_remote_alias` isolates exactly 1 failure) | yes — `test_remote_listing_refuses_program_option_value` |
| C3 `[T6]` | yes (`missing_diff_guard` isolates exactly 2 failures) | yes — both diff tests |

T7 is the coupled value inside C1 (no own security test); the joined clone security tests paired
with it fail on the pin, so no masking failure. A fix for one concept does not pass another’s tests.

**S5 — history (gate a: no failure).** `checks/upstream_first_fix.patch` (A alone, split values)
violates INV read literally: the joined `-<char><value>` token still runs a program, and the remote
alias and diff write path stay open (gate: 5 security fail). `checks/upstream_fix.patch` (A+B) also
violates INV literally: remote listing and diff remain (gate: 3 security fail). The property is
therefore not too narrow and needs no widening. Dependency-bump (F5): not applicable — the
reference proves an in-repo fix and the instruction never asks for an upgrade.

**S6 — contracts (gate a: no failure).** Tests need no guessed name: `UnsafeOptionError` is the
library’s existing error, which REF names; `Git.check_unsafe_options` and `_option_candidates`
already exist and are used by the repo’s own visible tests. Wrong-object trap: n/a (the protected
object is the argv tokens). Fail-open fallback: n/a (the decision is from option tokens alone).

**S7 — decisive tests.** `build/stk-gitpython-ghsawvpp/trial_summary.md` does not exist. The
readable `trial_detail_deepseek.json` records three runs, each reward 0.875 with all functional
tests passing — exactly one of the eight security tests failed in every run, so a single test
decided each result. The build artifacts do not record which test; `gate_report.json` shows
`missing_remote_alias` as the only one-test failure configuration at 0.875, i.e. likely
`.htests.security.test_option_injection::test_remote_listing_refuses_program_option_value`.
`NEEDS_HUMAN_REVIEW: YES` for that.

## Verdict

**Gate a — READY.** Every one of the 36 graded tests passes for a correct fix following the
instruction’s primary mechanism: screen the tokens a caller’s options become and raise the existing
`UnsafeOptionError` before git runs. Two independent correct designs score 1.0 (reference builder;
`alternative.patch` call-site token screening). No instruction/test contradiction, no assertion
outside INV/REF/KEEP, no guessed name, no harness bypass of a valid layer. The single judgment call
is T5: `--exec` is git’s documented alias of `--upload-pack` (standard git knowledge; the graded
project test also normalizes it, if that test is in the pinned checkout), so INV read literally
covers the route and the test does not fail a correct fix — but the alias is not named in the
instruction. A model failing that test is a model failure, not gate a. No “yes” row.

**Gate b — quality only.** Leniency gaps and hint wording are listed in §2 and §3; none sets
NOT_READY.

**Quality to tighten** (specific changes):

1. Add a two-element sequence security case (mix a safe value with an unsafe one) so first-element-
   only screening fails.
2. Add a diff abbreviation case (`out=<path>`) or require the token/abbreviation path, so a
   hardcoded `output`-name guard fails.
3. Add `upl=program` / `--upl=` on remote listing and a `Remote.fetch`/`pull` `exec=` security
   test, so the exact-name and reference-level fetch/pull gaps are measured (the fetch/pull fix in
   `hardening.patch` currently has no test requiring it).
4. Add a legitimate dash-prefixed value of a long option to the functional suite so blanket
   refusal of dash-prefixed caller values fails.
5. Add a tuple-valued kwarg security case on the split path.
6. Hints: delete “The example above is an example, not the full set.”; drop the “passed through to
   the library unchanged … invoked git with it” mechanism sentence; drop “clone” from the example;
   fold “Do not special-case the example.” into “Fix the problem and its close variants.”
7. Realism: nothing to change.

**Required: generalize:** none.

Human review: confirm which security test decided the three 0.875 DeepSeek runs (likely
`test_remote_listing_refuses_program_option_value`, the only one-test 0.875 configuration in
`gate_report.json`) and confirm that `git ls-remote --exec` is standard, documented git knowledge a
correct fix would find; also note that the reference itself leaves `fetch`/`pull` `--exec` open.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
