# FAIRNESS — stk-pyload-ghsa4744

Read: `instruction.md`, every file in `tasks/stk-pyload-ghsa4744/tests/`, `solution/fix.patch`,
`manifest.json`, `notes.md`, all `checks/*.patch`, and the audit brief `AUDIT-FIX-20261024.md`.
Nothing was run for this review; a local venv smoke test of the revised startup suite is recorded
in `notes.md`.

Abbreviations used in the tables:

- **AUTHORITY** — “Only an administrator may change a setting whose value decides what the service
  executes, how it is exposed to others, or what it accepts or presents as proof of identity. A
  change attempted from any other account has no effect: the stored value stays as it was.”
- **AREA** — “The data the service stores for its users must never be stored in the area the
  service reserves for its own temporary work, or anywhere within it. A configuration value that
  would do so does not take effect: the service keeps that data outside the area, and nothing is
  created inside it.”
- **KEEP** — “Everything that works today keeps working. An account without administrator rights
  keeps being able to make the changes it may make today, and an administrator can still change
  any setting.”

Graded set: 19 security tests, 12 functional tests (9 harness functional + 3 pristine project
tests).

## 1. Test-by-test fairness

| test | what it asserts | covering instruction sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `security/test_settings_authority.py::test_non_admin_cannot_change_protected_core_setting[reconnect-script-/bin/true]` | a non-admin settings account writes `reconnect.script`; the value is unchanged | AUTHORITY (“what the service executes”) | **no** — a guard in the API gate, in the request-authority resolver, or a refusal before the write all leave the value untouched | low |
| `...[webui-ssl_certfile-/etc/hostname.crt]` | certificate option unchanged | AUTHORITY (“what it presents as proof of identity”) | **no** — same layers; the option name is the product’s visible `default.cfg` name | low |
| `...[webui-ssl_keyfile-/etc/hostname.key]` | key option unchanged | AUTHORITY | **no** | low |
| `...[webui-use_ssl-true]` | transport option unchanged | AUTHORITY (“how it is exposed to others”) | **no** | low |
| `...[webui-host-0.0.0.0]` | served endpoint unchanged | AUTHORITY | **no** | low |
| `...[proxy-username-attacker]` | proxy credential unchanged | AUTHORITY (“what it presents as proof of identity”) | **no** | low |
| `...[proxy-password-attacker-secret]` | proxy credential unchanged | AUTHORITY | **no** | low |
| `...[AntiVirus-avfile-/bin/sh]` | scanner program unchanged | AUTHORITY (“what the service executes”) | **no** — the plugin branch is part of “any setting”; the option is in the plugin config the product itself writes | low |
| `...[AntiVirus-avargs--c id]` | scanner arguments unchanged | AUTHORITY | **no** | low |
| `security/test_storage_location.py::test_download_folder_cannot_be_the_temporary_area` | the folder value stays as before | AREA (the temporary area itself) | **no** — a guard before the write, or a refusal that leaves the stored value, passes | low |
| `...::test_download_folder_cannot_be_inside_the_temporary_area[flask|jinja|downloads]` | three child paths refused | AREA (“or anywhere within it”) | **no** — resolved containment; the reference and `alternative_fix` both pass | low |
| `...::test_download_folder_cannot_resolve_into_the_temporary_area` | a symlink to the area refused | AREA (a value that “would” put data there) | **no** — the property is about the resolved data location; standard expert knowledge that a path is resolved | low |
| `security/test_startup_location.py::test_startup_does_not_adopt_temporary_area_as_download_folder` | the started service reports a folder outside the area; the supplied folder is not created | AREA | **no** — the check now reads the effective folder the product itself reports and uses | low |
| `...::test_startup_does_not_adopt_saved_temporary_download_folder` | same, with the value saved earlier | AREA (“A configuration value that would do so does not take effect”) | **no** — an in-memory drop and a file rewrite both pass; the saved file is no longer read | low |
| `...::test_startup_does_not_adopt_temporary_area_child[""|flask|jinja]` | the area and children refused at start-up | AREA | **no** | low |
| `functional/test_keep_working.py::test_non_admin_can_change_ordinary_download_setting` | `download.max_speed` changes | KEEP | **no** — not a setting the security rule covers | low |
| `...::test_non_admin_can_change_ordinary_display_setting` | `webui.theme` changes | KEEP | **no** | low |
| `...::test_non_admin_can_change_ordinary_plugin_setting` | `AntiVirus.action` changes | KEEP | **no** — an ordinary add-on option, not a program/credential | low |
| `...::test_admin_can_change_protected_settings` | an admin writes reconnect program, certificate, scanner program | KEEP (“an administrator can still change any setting”) | **no** | low |
| `...::test_download_folder_beside_temporary_area_is_accepted` | a sibling folder is accepted | KEEP + AREA (outside the area) | **no** — not “within” the area | low |
| `...::test_download_folder_with_similar_name_is_accepted` | a name-prefix folder is accepted | KEEP + AREA | **no** — path containment, not string prefix | low |
| `...::test_startup_keeps_legitimate_download_folder` | a CLI-supplied folder outside the area is used | KEEP | **no** | low |
| `...::test_startup_keeps_saved_legitimate_download_folder` | a saved legitimate folder is used and saved | KEEP | **no** | low |
| `...::test_startup_keeps_download_folder_with_similar_name` | a prefix-similar folder is used | KEEP + AREA | **no** | low |
| `functional/pristine/test_skeleton.py::test_fib` | the project’s own test runs | KEEP (public imports unchanged) | **no** | low |
| `.../test_mega_nz_folder.py::test_folder_pattern` | existing decrypter pattern unchanged | KEEP | **no** | low |
| `...::test_subfolder_pattern` | existing subfolder pattern unchanged | KEEP | **no** | low |

No row is “yes”; no row is an unresolved “maybe”.

## 2. Leniency (quality, non-blocking)

**Concepts.** C1 core authority (`[T1,T4]`), C2 download-folder rule (`[T2,T3]`), C3 plugin
authority (`[T5]`).

| trap | most plausible WRONG fix | caught? |
|---|---|---|
| T1 reconnect program | gate only the reported option, leave the rest of the core options open | yes — the other core security cases; `checks/miss_core_settings.patch` (7 security fail) |
| T4 real option names | copy the plausible `ssl_cert`/`ssl_key` spellings | yes — `checks/wrong_option_names.patch` (2 security fail) |
| T2 API folder | validate the text, not the resolved path | yes — `test_download_folder_cannot_resolve_into_the_temporary_area` |
| T2 API folder | over-broad rejection of siblings/prefix names | yes — `checks/overbroad_temp.patch` (5 functional fail) |
| T2/T3 folder | fix only the API call site | yes — `checks/api_only_location.patch` (5 security fail) |
| T2/T3 folder | fix only the `fs` helper, leave both call sites | yes — `checks/miss_storage_location.patch` (10 security fail) |
| T3 start-up | refuse the saved bad value only after it has taken effect | yes — the folder assertions and `checks/check_after_set.patch` (5 security fail) |
| T5 plugin branch | guard only core options | yes — `checks/miss_plugin_settings.patch` (2 security fail) |
| any | refuse every write or crash | yes — `checks/refuse_all.patch` (6 functional fail), `checks/reads_only.patch` (19 security fail) |

**Wrong fixes no test catches**

1. A guard that trusts any out-of-request caller: the API tests always run inside a request; the
   reference itself treats out-of-request calls as trusted, and the CLI path has no administrator
   to consult. No test asserts otherwise.
2. A start-up fix that changes the local folder variable but not the effective configuration: it
   would pass the folder-creation assertion only in cases where the folder already exists; the
   revised test reads the effective value, so this is caught.
3. A case-folding-only refinement (`os.name == "nt"`) is retained by the reference but not
   exercised on Linux.

## 3. Hints (quality, non-blocking)

- “Fix the problem and its close variants.” — states generality without listing a route or a
  count; keep.
- “Both are invariants, not a list of cases. The example above is one instance.” — signals a
  variant list but names nothing; it is the general-property statement and is covered by
  “Fix the problem and its close variants”. Keep (it does not locate a sibling).
- The observed-problem paragraph names the reconnection program only; that is the advisory’s own
  example, not a sibling map. No change.

## 3a. Required: generalize

**none.** No sentence locates a sibling, far site or uncovered route. The instruction names the
settings permission, the settings API and the service’s temporary area, all of which are the
reported entry points or the protected outcome; it names no file, function, option spelling,
transport, plugin or stage. `AUDIT-FIX-20261024.md` requires no instruction change.

## 4. Realism (quality, non-blocking)

T1/T2 are the published advisory routes at the pin. T3 is the same incomplete rule re-implemented
in the start-up path in real, unmodified upstream code (neither published fix touches it). T4
uses the product’s own declared option names; the published fix’s plausible spellings guard
nothing. T5 is the plugin branch of the same write, closed only by the later published commit.
Every concept is driven through a real entry point: the product’s Flask API with its own Basic
authentication, or `python -m pyload --dry-run` with the product’s own flags and a configuration
file the product itself wrote. Nothing looks planted or contrived.

## Stacking checks

`manifest.stacking.concepts` = `[T1,T4] [T2,T3] [T5]` — three independent guards: the core option
list, the shared folder rule (two call sites), and the plugin option list.

**S1 — coupled traps (gate a: no failure)**

| must-keep value (test) | covering clause | security rule forbids it? |
|---|---|---|
| `download.max_speed` (`test_non_admin_can_change_ordinary_download_setting`) | KEEP | no — not a setting the service executes/exposes/uses as identity |
| `webui.theme` (`test_non_admin_can_change_ordinary_display_setting`) | KEEP | no |
| `AntiVirus.action` (`test_non_admin_can_change_ordinary_plugin_setting`) | KEEP | no — ordinary add-on behaviour, not a program or credential |
| reconnect program, `ssl_certfile`, `AntiVirus.avfile` written as admin (`test_admin_can_change_protected_settings`) | KEEP (“an administrator can still change any setting”) | no — AUTHORITY allows an administrator |
| folder beside the area (`test_download_folder_beside_temporary_area_is_accepted`) | KEEP | no — outside the area, so AREA does not apply |
| name-prefix folder (`test_download_folder_with_similar_name_is_accepted`) | KEEP | no — path containment, not string prefix |
| legitimate CLI folder (`test_startup_keeps_legitimate_download_folder`) | KEEP | no |
| legitimate saved folder (`test_startup_keeps_saved_legitimate_download_folder`) | KEEP | no |
| name-prefix start-up folder (`test_startup_keeps_download_folder_with_similar_name`) | KEEP | no |
| pristine project tests | KEEP (public interfaces unchanged) | no |

No contradiction: every coupled value is outside AUTHORITY’s protected classes or outside AREA’s
containment.

**S2 — shape traps (gate a: no failure)**

| refused shape | outside the legitimate set? |
|---|---|
| core option values on protected settings (program, cert/key, TLS, host, proxy credentials) | yes — the instruction names the protected classes in product terms, and KEEP only covers administrative changes to them |
| plugin scanner program/arguments | yes — same protected class (“what the service executes”) |
| folder equal to the temporary area | yes — AREA names the area itself |
| folder inside the area (`flask`, `jinja`, `downloads`) | yes — “anywhere within it” |
| symlink resolving into the area | yes — the property is about where the data would be stored |
| start-up folder equal to/inside the area, supplied or saved | yes — same |
| legitimate control shapes (sibling, name prefix, ordinary options) | not refused; the functional suite requires they keep working |

No stated character set or leading-slash rule exists, so the example traps do not arise.

**S3 — fixtures and harness (gate a: no failure).** Every state set up is one the instruction
treats as legitimate: authenticated accounts (one administrator, one account holding the settings
permission), ordinary settings the account may change, a saved configuration the product itself
writes, and start-up flags the product documents. Each concept is reached through its real entry
point: the product’s HTTP settings API with its own authentication for C1/C3 and C2’s write, and
`python -m pyload --dry-run` for C2’s start-up copy. The revised start-up test reads the folder
the service itself reports and uses, so a guard in the configuration loader, in the core start-up,
or before the write all pass; verified locally with an in-memory-drop variant that leaves the
saved file untouched.

**S4 — concept independence (gate a: no failure).**

| concept | own fix passes its tests alone? | fails on pin through its own route? |
|---|---|---|
| C1 `[T1,T4]` | yes — `miss_core_settings` isolates exactly 7 C1 security failures with C2/C3 fixed | yes — all 9 authority cases fail on the pin |
| C2 `[T2,T3]` | yes — `miss_storage_location` isolates exactly 10 C2 security failures with C1/C3 fixed | yes — all 5 API cases and all 5 start-up cases fail on the pin |
| C3 `[T5]` | yes — `miss_plugin_settings` isolates exactly 2 C3 security failures with C1/C2 fixed | yes — both plugin cases fail on the pin |

No concept masks another: the isolation patches above show each concept’s tests failing alone and
passing when its own guard is present. H3c masking does not apply (no concept is only observable
through another).

**S5 — history (gate a: no failure).** `checks/upstream_first_fix.patch` (published fix A) violates
AUTHORITY and AREA read literally: the certificate options are still writable under the plausible
spellings, the plugin branch is unguarded, and the folder rule is untouched at both call sites
(gate: 14 security failures). `checks/upstream_fix.patch` (A+B) still leaves the folder rule and
the certificate spellings open (gate: 7 security failures). The property is therefore not too
narrow and needs no widening. Dependency-bump (F5): not applicable — the reference proves an
in-repo fix and the instruction never asks for an upgrade.

**S6 — contracts (gate a: no failure).** Tests need no guessed name: the API route, the option
names and the start-up flags all exist in the pinned tree and its visible `default.cfg`; the
accounts are created through the product’s own database API. Wrong-object trap: the protected
object class is named in product terms by AUTHORITY (“what the service executes, how it is exposed
to others, or what it accepts or presents as proof of identity”). Fail-open fallback: the
out-of-request case is not exercised as an authority decision; the start-up path has no account,
and its stated outcome is AREA, which the test checks.

**S7 — decisive tests.** `build/stk-pyload-ghsa4744/trial_summary.md` does not exist. The audit
source records that both reviewed runs failed on the single test
`security/test_startup_location.py::test_startup_does_not_adopt_saved_temporary_download_folder`
because it asserted that the *saved file* was rewritten, which the instruction never requires.
That test has been rewritten to assert the effective folder the started service reports and uses,
while keeping the “nothing created inside the temporary area” check. A single test did decide each
of those runs, so the rewrite is flagged for human confirmation.

## Verdict

**Gate a — READY.** Every one of the 31 graded tests passes for a correct fix that follows the
instruction’s primary mechanism (administrator-only protected settings; a resolving containment
rule for the download folder at the settings write and at start-up). Two structurally different
correct designs score 1.0 (reference; `alternative_fix`), as does `hardening`. The previously
unfair row is gone: the saved-startup test no longer requires the stored file to be rewritten, so
an in-memory drop and a file rewrite both pass, while a fix that lets the saved value take effect
still fails on the pin. No instruction/test contradiction, no assertion outside
AUTHORITY/AREA/KEEP, no guessed name, no harness bypass of a valid layer. No “yes” row.

**Gate b — quality only.** Leniency gaps and wording notes are in §2 and §3; none sets NOT_READY.

**Quality to tighten:** the items in §2 are optional hardening of the existing check matrix; the
matrix already isolates every concept and rejects the named wrong fixes.

**Required: generalize:** none. `AUDIT-FIX-20261024.md` requires no instruction change, and none
was made.

Human review: confirm that
`security/test_startup_location.py::test_startup_does_not_adopt_saved_temporary_download_folder`
— the single decisive test in both reviewed runs — is now fair: it reads the folder the service
reports it uses and no longer requires the saved configuration file to be rewritten, while the
pinned code still fails it and the reference still passes.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
