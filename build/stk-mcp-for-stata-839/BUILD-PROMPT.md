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

Project root: `/home/mara/cwe-bench`. Task: `stk-mcp-for-stata-839`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 839; CWE-77 / CWE-78 command injection: caller-controlled string interpolat
- Pinned (vulnerable) commit: 3553a42677855f99514392eaf3a90d56d27a2037. Published fix: e6f945941ae0c7cf5e74a428e0b3dc82b396382f.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-839",
 "pattern": "H4",
 "repo": "sepinetam/mcp-for-stata",
 "pinned_commit": "3553a42677855f99514392eaf3a90d56d27a2037",
 "protections": [
  "Do-file content guard: GuardValidator runs the command/pattern blacklist over the text of the do-file before execution (src/stata_mcp/api/stata_do.py:78-96, src/stata_mcp/mcp_servers.py:211-240, src/stata_mcp/guard/validator.py:105-149); it never inspects the command script StataDo builds, nor the log name, nor the dofile path.",
  "Do-file path boundary: the requested dofile path is resolve()d and must be relative_to STATA_MCP_FOLDER.DO or WORKING_DIR (src/stata_mcp/api/stata_do.py:22-30 and :51-76, src/stata_mcp/mcp_servers.py:183-208 and :532-540).",
  "No OS shell on Unix: the Stata process is spawned with shell=False on Unix-like systems (src/stata_mcp/stata/stata_do/do.py:162-171 and :278-287); the Windows transport still uses shell=True with a hand-built batch path (do.py:225-232 and :360-368).",
  "Log-name validation: none at the pinned commit - log_file_name is used verbatim as the log base name and interpolated into the `log using \"...\"` command text (do.py:81-82, :127-129, :175-181).",
  "read_log directory boundary (src/stata_mcp/mcp_servers.py:471-489) exists but is a file-read control, not a command-construction control."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/stata_mcp/stata/stata_do/do.py:81",
    "src/stata_mcp/stata/stata_do/do.py:82",
    "src/stata_mcp/stata/stata_do/do.py:127-129",
    "src/stata_mcp/stata/stata_do/do.py:175-181",
    "src/stata_mcp/stata/stata_do/do.py:291-297",
    "src/stata_mcp/api/stata_do.py:113-118",
    "src/stata_mcp/mcp_servers.py:268-271"
   ],
   "reason_to_dismiss": "None on the merits: this is the route the report names. A solver can only claim the do-file guard covers it, but the log name never appears in the do-file content that guard reads (api/stata_do.py:80-84).",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "do.py:81 - `log_name = log_file_name or nowtime` is the parameter's only consumer",
    "do.py:82 - the name is then joined into a filesystem path, so `/` and `..` also move the log outside log_file_path",
    "do.py:129 - `log_cmd = f'log using \"{log_file.as_posix()}\", ...'` interpolates the resulting path into the Stata command text",
    "do.py:178-186 - that command text is piped to the Stata CLI's stdin",
    "do.py:291-297 - the monitor twin builds the same string",
    "docs/api/overview.md:428 documents `log_file_name=f\"analysis_{dataset}\"`, and src/stata_mcp/utils/__init__.py:11-12 the default `%Y%m%d%H%M%S` name - both must keep working"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "src/stata_mcp/stata/stata_do/do.py:182",
    "src/stata_mcp/stata/stata_do/do.py:298",
    "src/stata_mcp/mcp_servers.py:270",
    "src/stata_mcp/mcp_servers.py:183-208",
    "src/stata_mcp/api/stata_do.py:51-66"
   ],
   "reason_to_dismiss": "The path is resolve()d, existence-checked and confined to the allowed roots by `_is_within_allowed_directories`, so a solver reads it as a trusted path rather than caller-controlled text and leaves it alone.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "do.py:182 - `do \"{dofile_path}\"` is interpolated into the same piped command script, three lines below the fixed line",
    "do.py:298 - identical twin in the monitor path",
    "mcp_servers.py:270 passes the *raw* `dofile_path` to execute_dofile while the boundary check at mcp_servers.py:183-197 was done on `dofile_path_resolved` - the checked object and the interpolated object are different (resolved vs lexical shape)",
    "the boundary check answers 'may I execute this file', never 'what text reaches Stata'; a file whose own name contains a quote or newline still resolves inside an allowed root"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "src/stata_mcp/stata/stata_do/do.py:213",
    "src/stata_mcp/stata/stata_do/do.py:219-220",
    "src/stata_mcp/stata/stata_do/do.py:225-232",
    "src/stata_mcp/stata/stata_do/do.py:346",
    "src/stata_mcp/stata/stata_do/do.py:353-354",
    "src/stata_mcp/stata/stata_do/do.py:360-368"
   ],
   "reason_to_dismiss": "The branch is declared untested and unsupported ('As I do not have a Windows device... Windows is not supported yet', do.py:91-92) and the changelog states Windows 'correctly uses shell=True' (CHANGELOG.md:575); the published fix only touches comments on these lines.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "do.py:219 / do.py:353 - a second, hand-written `log using \"{log_file}\"` builder that does not go through generate_log_command",
    "do.py:220 / do.py:354 - a second, hand-written `do \"{dofile_path}\"` line",
    "do.py:213 / do.py:346 - the temp batch file name is built from `dofile_path.stem` and then placed on a shell command line",
    "do.py:225-232 / do.py:360-368 - the batch file is run through subprocess with shell=True, the one place a value can reach an OS shell"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/stata_mcp/stata/builtin_tools/help/stata_help.py:106",
    "src/stata_mcp/stata/builtin_tools/help/stata_help.py:119",
    "src/stata_mcp/stata/stata_controller/controller.py:99",
    "src/stata_mcp/stata/builtin_tools/help/stata_help.py:70",
    "src/stata_mcp/stata/builtin_tools/help/stata_help.py:76",
    "src/stata_mcp/stata/builtin_tools/help/stata_help.py:91",
    "src/stata_mcp/stata/builtin_tools/help/stata_help.py:97",
    "src/stata_mcp/mcp_servers.py:119-135",
    "src/stata_mcp/api/stata_help.py:16-30"
   ],
   "reason_to_dismiss": "Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.",
   "distance": {
    "files": 3,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "stata_help.py:106 - `self.controller.run(f\"help {cmd}\")` builds a Stata command from the tool argument with no validation",
    "controller.py:99 - `self.child.sendline(command)` writes it to a live pexpect Stata session",
    "stata_help.py:119 - the same construction for `check_command_exist_with_help`",
    "stata_help.py:70 and :76 - `help__{cmd}.txt` is joined as a file name, so the same argument also chooses a write path outside the cache directory via separators or `..`",
    "stata_help.py:91 and :97 - the same join on the read side",
    "mcp_servers.py:119-135 - the MCP `help` tool passes `cmd` straight through"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/stata_mcp/stata/builtin_tools/ado_install/ssc_install.py:15",
    "src/stata_mcp/stata/builtin_tools/ado_install/github_install.py:16",
    "src/stata_mcp/stata/builtin_tools/ado_install/net_install.py:18",
    "src/stata_mcp/stata/builtin_tools/ado_install/base.py:43-45",
    "src/stata_mcp/mcp_servers.py:348-349",
    "src/stata_mcp/api/ado_install.py:36-39"
   ],
   "reason_to_dismiss": "Package installation is a separate MCP tool with its own argument surface; package names read as identifiers rather than free text, and the advisory is about log_file_name.",
   "distance": {
    "files": 5,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "ssc_install.py:15 - `f\"ssc install {package}{self.REPLACE_MESSAGE}\"`",
    "github_install.py:16 - `f\"github install {package}{self.REPLACE_MESSAGE}\"`",
    "net_install.py:16-18 - `f\"{ex_from} from({directory_or_url})\"` puts the caller URL inside `from(...)` with no quoting",
    "base.py:43-45 - every install builds a fresh StataController and sends the string to the session",
    "mcp_servers.py:328 documents the legitimate `package=\"SepineTam/TexIV\"` form, i.e. `/` is a required, coupled value",
    "mcp_servers.py:371 shows a `from(...)` URL being written by the maintainer, so URLs with `:` and `/` are a supported shape"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M2",
   "origin": "injection_room",
   "locations": [
    "src/stata_mcp/mcp_servers.py:369-372",
    "src/stata_mcp/api/ado_install.py:61-65"
   ],
   "reason_to_dismiss": "The string is written to a do-file and then executed through stata_do, so the GuardValidator content blacklist runs over it (IS_GUARD defaults to True, config.py:377-385); and the whole branch is Windows-only.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "mcp_servers.py:371 - `write_dofile(f\"{source} install {package}, {replace_str} {from_message}\")` is a second implementation of the installer command text, bypassing the installer classes",
    "mcp_servers.py:372 - the written do-file is then executed via stata_do",
    "mcp_servers.py:211-240 - the only thing that inspects it is the first-word blacklist (guard/blacklist.py:41-56, :64-83), which leaves non-blacklisted Stata commands free",
    "api/ado_install.py:61-65 - the same second implementation in the Python API"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M3",
   "origin": "injection_room",
   "locations": [
    "src/stata_mcp/stata/stata_do/do.py:126-130",
    "src/stata_mcp/stata/stata_do/do.py:132-133"
   ],
   "reason_to_dismiss": "It is public internal API with no caller that passes untrusted text today; the only in-repo callers are execute_dofile's own paths, so a solver can reasonably say the check belongs where the name enters, not in the builder.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "do.py:126-130 - the public static `generate_log_command` is the only string builder used by both Unix paths and leaves the quoted literal unescaped",
    "do.py:132-133 - the public `generate_log_file` composes a path from a caller string and is not gated by the new execute_dofile validation",
    "the published fix puts the check in execute_dofile, so the shared builder stays unguarded for any future log-export/cleanup caller"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1"
  ],
  [
   "T2",
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5",
   "T6"
  ],
  [
   "T7"
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
   "a": "T4",
   "b": "T5",
   "what": "A strict identifier rule for `help cmd` breaks a documented flow: on a successful install `_load_help_cls().help(package, replace=True)` is called with the package string (api/ado_install.py:54-58), and the documented GitHub form is `SepineTam/TexIV` (mcp_servers.py:328) - so the help validator must accept `/` to keep T5's own route working."
  },
  {
   "a": "T1",
   "b": "T5",
   "what": "One shared allow-list cannot serve both parameters: log names must keep the all-digit `%Y%m%d%H%M%S` default (utils/__init__.py:11-12) and the dotted `analysis_wave1.dta` example (docs/api/overview.md:428), while package names need `/` and net sources need `:`/`/` inside `from(...)` (net_install.py:16-18, mcp_servers.py:371). A solver who refactors both through one validator breaks one of the two routes."
  },
  {
   "a": "T2",
   "b": "T3",
   "what": "The natural Unix fix for the `do \"...\"` interpolation (shell-quote the path, reject backslashes/spaces) is wrong for the Windows transport, which interpolates a native `C:\\...` path into the same quoted literal (do.py:220, :354); a fix that satisfies one transport changes behaviour on the other."
  }
 ],
 "fairness_risks": [
  "The documented default log name is the `%Y%m%d%H%M%S` timestamp (utils/__init__.py:11-12): it starts with a digit, is all digits and is 14 characters. Any rule requiring a letter first, or forbidding all-digit names, breaks the default path.",
  "The documented custom-name example is `log_file_name=f\"analysis_{dataset}\"` with dataset like `wave1.dta` (docs/api/overview.md:428), so dots must be allowed; the same string is returned to the caller as the log path, so a fix must not silently rewrite it.",
  "Non-ASCII log names have no documented prohibition and the project ships Chinese docs (docs/api/overview.zh.md:128); rejecting non-ASCII would be an over-broad refusal of a legitimate shape.",
  "Ado package installs legitimately use `user/repo` (mcp_servers.py:328) and `from(https://...)` URLs (github_install.py:30, mcp_servers.py:371), so a `no slashes/colons` rule for T5 refuses a documented input.",
  "Absolute do-file paths with spaces are explicitly supported ('Paths with spaces now work correctly on Unix-like systems', CHANGELOG.md:572); a fix for T2 that rejects spaces or requires bare file names refuses a legitimate path shape.",
  "Refusing over-long names (>128) has no documented support and no advisory basis; it is a plausible but arbitrary refusal."
 ],
 "effort_minutes": 60,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T4",
   "T5"
  ],
  "why": "Four independent judgements, each with a different reason to dismiss, spanning three packages. T1 is the report's own route and the cheap point, but it forces the fix-site decision: a regex added at one wrapper (api/stata_do.py:33 or mcp_servers.py:138) leaves the other two entry points and both transports open, while a check at do.py:81 closes the whole log-name group. T2 is the same function three lines below and looks already defended by the boundary check - the classic deepseek shape (protection appears to exist, a plausible dismissal exists) - and it survives any log-name-only fix. T4 is a second command-construction path one package away with a 'read-only documentation' alibi. T5 is a third, and it carries the coupled value (user/repo, from(URL)) that makes an over-broad shared validator break documented installs, i.e. the mimo failure. This beats designs built only on the do.py siblings: T1/T2/T3 all collapse if a solver validates both caller strings once at the top of execute_dofile, whereas the help and installer routes need separate decisions in separate modules. T3, T6 and T7 are kept as sub-routes of their groups (Windows transport, Windows installer branch, public builders) rather than separate judgements; T7 in particular is a lower-value injection room because no current entry point feeds it untrusted text."
 },
 "unverified": [
  "No shell was available, so nothing was executed; every claim is a line-level reading of the pinned tree.",
  "No published fix diff or latest-release tree was available in this worktree, so every `present_in_latest` is unknown and the claim that the fix touches only do.py comes from the screener record, not from the patch itself.",
  "The advisory text (GHSA-4P62-HQP5-G644 / CVE-2026-47708 / PYSEC-2026-544) was not read; the screener summary is treated as a lead.",
  "Whether a behavioural hidden test can drive the pexpect routes (help, installers) on this host without a real Stata binary is untested; controller.py:99 is a plain sendline, so stubbing StataController and capturing the sent string looks feasible but was not run.",
  "Whether the MCP `help` and `ado_package_install` tools are in the graded profile matters for reachability: both are registered in the 'all' profile and help is unix_only (mcp_servers.py:607-633).",
  "Out-of-family sites deliberately excluded from the trap list: src/stata_mcp/api/read_log.py:26-32 has no directory boundary although mcp_servers.py:471-489 does, and get_data_info resolves arbitrary paths; both are file-read issues, not command construction.",
  "repo_mb was not measured; the <5 MB tiny_repo flag is taken from the screener."
 ]
}
  ```
- Published fix sites:   - src/stata_mcp/stata/stata_do/do.py:81 — T1 M4 (reason to dismiss: None on the merits: this is the route the report names. A solver can only claim the do-file guard covers it, but the log name never appears in the do-file content that guard reads (api/stata_do.py:80-84).)
  - src/stata_mcp/stata/stata_do/do.py:82 — T1 M4 (reason to dismiss: None on the merits: this is the route the report names. A solver can only claim the do-file guard covers it, but the log name never appears in the do-file content that guard reads (api/stata_do.py:80-84).)
  - src/stata_mcp/stata/stata_do/do.py:127-129 — T1 M4 (reason to dismiss: None on the merits: this is the route the report names. A solver can only claim the do-file guard covers it, but the log name never appears in the do-file content that guard reads (api/stata_do.py:80-84).)
  - src/stata_mcp/stata/stata_do/do.py:175-181 — T1 M4 (reason to dismiss: None on the merits: this is the route the report names. A solver can only claim the do-file guard covers it, but the log name never appears in the do-file content that guard reads (api/stata_do.py:80-84).)
  - src/stata_mcp/stata/stata_do/do.py:291-297 — T1 M4 (reason to dismiss: None on the merits: this is the route the report names. A solver can only claim the do-file guard covers it, but the log name never appears in the do-file content that guard reads (api/stata_do.py:80-84).)
  - src/stata_mcp/api/stata_do.py:113-118 — T1 M4 (reason to dismiss: None on the merits: this is the route the report names. A solver can only claim the do-file guard covers it, but the log name never appears in the do-file content that guard reads (api/stata_do.py:80-84).)
  - src/stata_mcp/mcp_servers.py:268-271 — T1 M4 (reason to dismiss: None on the merits: this is the route the report names. A solver can only claim the do-file guard covers it, but the log name never appears in the do-file content that guard reads (api/stata_do.py:80-84).)
- Uncovered routes to confirm (pattern B):   - src/stata_mcp/stata/stata_do/do.py:182 — T2 M8 (reason to dismiss: The path is resolve()d, existence-checked and confined to the allowed roots by `_is_within_allowed_directories`, so a solver reads it as a trusted path rather than caller-controlled text and leaves it alone.)
  - src/stata_mcp/stata/stata_do/do.py:298 — T2 M8 (reason to dismiss: The path is resolve()d, existence-checked and confined to the allowed roots by `_is_within_allowed_directories`, so a solver reads it as a trusted path rather than caller-controlled text and leaves it alone.)
  - src/stata_mcp/mcp_servers.py:270 — T2 M8 (reason to dismiss: The path is resolve()d, existence-checked and confined to the allowed roots by `_is_within_allowed_directories`, so a solver reads it as a trusted path rather than caller-controlled text and leaves it alone.)
  - src/stata_mcp/mcp_servers.py:183-208 — T2 M8 (reason to dismiss: The path is resolve()d, existence-checked and confined to the allowed roots by `_is_within_allowed_directories`, so a solver reads it as a trusted path rather than caller-controlled text and leaves it alone.)
  - src/stata_mcp/api/stata_do.py:51-66 — T2 M8 (reason to dismiss: The path is resolve()d, existence-checked and confined to the allowed roots by `_is_within_allowed_directories`, so a solver reads it as a trusted path rather than caller-controlled text and leaves it alone.)
  - src/stata_mcp/stata/stata_do/do.py:213 — T3 M2 (reason to dismiss: The branch is declared untested and unsupported ('As I do not have a Windows device... Windows is not supported yet', do.py:91-92) and the changelog states Windows 'correctly uses shell=True' (CHANGELOG.md:575); the published fix only touches comments on these lines.)
  - src/stata_mcp/stata/stata_do/do.py:219-220 — T3 M2 (reason to dismiss: The branch is declared untested and unsupported ('As I do not have a Windows device... Windows is not supported yet', do.py:91-92) and the changelog states Windows 'correctly uses shell=True' (CHANGELOG.md:575); the published fix only touches comments on these lines.)
  - src/stata_mcp/stata/stata_do/do.py:225-232 — T3 M2 (reason to dismiss: The branch is declared untested and unsupported ('As I do not have a Windows device... Windows is not supported yet', do.py:91-92) and the changelog states Windows 'correctly uses shell=True' (CHANGELOG.md:575); the published fix only touches comments on these lines.)
  - src/stata_mcp/stata/stata_do/do.py:346 — T3 M2 (reason to dismiss: The branch is declared untested and unsupported ('As I do not have a Windows device... Windows is not supported yet', do.py:91-92) and the changelog states Windows 'correctly uses shell=True' (CHANGELOG.md:575); the published fix only touches comments on these lines.)
  - src/stata_mcp/stata/stata_do/do.py:353-354 — T3 M2 (reason to dismiss: The branch is declared untested and unsupported ('As I do not have a Windows device... Windows is not supported yet', do.py:91-92) and the changelog states Windows 'correctly uses shell=True' (CHANGELOG.md:575); the published fix only touches comments on these lines.)
  - src/stata_mcp/stata/stata_do/do.py:360-368 — T3 M2 (reason to dismiss: The branch is declared untested and unsupported ('As I do not have a Windows device... Windows is not supported yet', do.py:91-92) and the changelog states Windows 'correctly uses shell=True' (CHANGELOG.md:575); the published fix only touches comments on these lines.)
  - src/stata_mcp/stata/builtin_tools/help/stata_help.py:106 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/stata/builtin_tools/help/stata_help.py:119 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/stata/stata_controller/controller.py:99 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/stata/builtin_tools/help/stata_help.py:70 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/stata/builtin_tools/help/stata_help.py:76 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/stata/builtin_tools/help/stata_help.py:91 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/stata/builtin_tools/help/stata_help.py:97 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/mcp_servers.py:119-135 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/api/stata_help.py:16-30 — T4 M4 (reason to dismiss: Help is a read-only documentation lookup in a different MCP tool and a different package, not the do-file log wrapper the advisory names; a solver has no reason to treat the command name as attacker text.)
  - src/stata_mcp/stata/builtin_tools/ado_install/ssc_install.py:15 — T5 M4 (reason to dismiss: Package installation is a separate MCP tool with its own argument surface; package names read as identifiers rather than free text, and the advisory is about log_file_name.)
  - src/stata_mcp/stata/builtin_tools/ado_install/github_install.py:16 — T5 M4 (reason to dismiss: Package installation is a separate MCP tool with its own argument surface; package names read as identifiers rather than free text, and the advisory is about log_file_name.)
  - src/stata_mcp/stata/builtin_tools/ado_install/net_install.py:18 — T5 M4 (reason to dismiss: Package installation is a separate MCP tool with its own argument surface; package names read as identifiers rather than free text, and the advisory is about log_file_name.)
  - src/stata_mcp/stata/builtin_tools/ado_install/base.py:43-45 — T5 M4 (reason to dismiss: Package installation is a separate MCP tool with its own argument surface; package names read as identifiers rather than free text, and the advisory is about log_file_name.)
  - src/stata_mcp/mcp_servers.py:348-349 — T5 M4 (reason to dismiss: Package installation is a separate MCP tool with its own argument surface; package names read as identifiers rather than free text, and the advisory is about log_file_name.)
  - src/stata_mcp/api/ado_install.py:36-39 — T5 M4 (reason to dismiss: Package installation is a separate MCP tool with its own argument surface; package names read as identifiers rather than free text, and the advisory is about log_file_name.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T4, T5. Why: Four independent judgements, each with a different reason to dismiss, spanning three packages. T1 is the report's own route and the cheap point, but it forces the fix-site decision: a regex added at one wrapper (api/stata_do.py:33 or mcp_servers.py:138) leaves the other two entry points and both transports open, while a check at do.py:81 closes the whole log-name group. T2 is the same function three lines below and looks already defended by the boundary check - the classic deepseek shape (protection appears to exist, a plausible dismissal exists) - and it survives any log-name-only fix. T4 is a second command-construction path one package away with a 'read-only documentation' alibi. T5 is a third, and it carries the coupled value (user/repo, from(URL)) that makes an over-broad shared validator break documented installs, i.e. the mimo failure. This beats designs built only on the do.py siblings: T1/T2/T3 all collapse if a solver validates both caller strings once at the top of execute_dofile, whereas the help and installer routes need separate decisions in separate modules. T3, T6 and T7 are kept as sub-routes of their groups (Windows transport, Windows installer branch, public builders) rather than separate judgements; T7 in particular is a lower-value injection room because no current entry point feeds it untrusted text. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): The documented default log name is the `%Y%m%d%H%M%S` timestamp (utils/__init__.py:11-12): it starts with a digit, is all digits and is 14 characters. Any rule requiring a letter first, or forbidding all-digit names, breaks the default path. | The documented custom-name example is `log_file_name=f"analysis_{dataset}"` with dataset like `wave1.dta` (docs/api/overview.md:428), so dots must be allowed; the same string is returned to the caller as the log path, so a fix must not silently rewrite it. | Non-ASCII log names have no documented prohibition and the project ships Chinese docs (docs/api/overview.zh.md:128); rejecting non-ASCII would be an over-broad refusal of a legitimate shape. | Ado package installs legitimately use `user/repo` (mcp_servers.py:328) and `from(https://...)` URLs (github_install.py:30, mcp_servers.py:371), so a `no slashes/colons` rule for T5 refuses a documented input. | Absolute do-file paths with spaces are explicitly supported ('Paths with spaces now work correctly on Unix-like systems', CHANGELOG.md:572); a fix for T2 that rejects spaces or requires bare file names refuses a legitimate path shape. | Refusing over-long names (>128) has no documented support and no advisory basis; it is a plausible but arbitrary refusal.. Conflicts the reader found: A strict identifier rule for `help cmd` breaks a documented flow: on a successful install `_load_help_cls().help(package, replace=True)` is called with the package string (api/ado_install.py:54-58), and the documented GitHub form is `SepineTam/TexIV` (mcp_servers.py:328) - so the help validator must accept `/` to keep T5's own route working. | One shared allow-list cannot serve both parameters: log names must keep the all-digit `%Y%m%d%H%M%S` default (utils/__init__.py:11-12) and the dotted `analysis_wave1.dta` example (docs/api/overview.md:428), while package names need `/` and net sources need `:`/`/` inside `from(...)` (net_install.py:16-18, mcp_servers.py:371). A solver who refactors both through one validator breaks one of the two routes. | The natural Unix fix for the `do "..."` interpolation (shell-quote the path, reject backslashes/spaces) is wrong for the Windows transport, which interpolates a native `C:\...` path into the same quoted literal (do.py:220, :354); a fix that satisfies one transport changes behaviour on the other.

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

## Environment (`tasks/stk-mcp-for-stata-839/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-mcp-for-stata-839/instruction.md`)
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

## Tests (`tasks/stk-mcp-for-stata-839/tests/`)
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
- **Wrong-fix patches** go in `build/stk-mcp-for-stata-839/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-mcp-for-stata-839/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-mcp-for-stata-839/manifest.json`:**
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

**Also in `build/stk-mcp-for-stata-839/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-mcp-for-stata-839 --only static
python3 -I common/gate/gate.py stk-mcp-for-stata-839 --only nop
python3 -I common/gate/gate.py stk-mcp-for-stata-839 --only oracle
python3 -I common/gate/gate.py stk-mcp-for-stata-839 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-mcp-for-stata-839/`;
  - edit only `tasks/stk-mcp-for-stata-839/`, `build/stk-mcp-for-stata-839/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-839.json`. Verify each trap on the
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

Stacked task slug: `stk-mcp-for-stata-839`. Control task slug: `stk-mcp-for-stata-839-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-839.json`.
