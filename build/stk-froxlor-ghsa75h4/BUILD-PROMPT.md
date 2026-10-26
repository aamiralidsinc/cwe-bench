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

Project root: `/home/mara/cwe-bench`. Task: `stk-froxlor-ghsa75h4`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-4jch-8qq5-hqg6; GHSA-75h4-c557-j89r
- Pinned (vulnerable) commit: a7b66227e6a41978ff7591eea8e82c48b6bedda1. Published fix: 9e8f32f1e860, 2987b0e8806e.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-75h4-c557-j89r",
 "pattern": "H3b2",
 "repo": "froxlor/froxlor",
 "pinned_commit": "a7b66227e6a41978ff7591eea8e82c48b6bedda1",
 "protections": [
  "P1: DataDump.add() must confine the requested dump path to the customer's documentroot on the filesystem (DataDump.php:86-93) - the guard present is lexical only.",
  "P2: The root export consumer must re-establish that a queued destdir is a real directory inside the customer's documentroot before it creates, chowns or removes anything (ExportCron.php:64-74, ExportCron.php:215-216).",
  "P3: Export sub-directories (.tmp/mysql/mail/web) must be created, chowned and removed without traversing symlinks planted in the customer-writable destination (ExportCron.php:98-101, ExportCron.php:192, ExportCron.php:213).",
  "P4: Root-side directory creation and chown for customer-supplied subpaths (directory-options path, domain documentroot) must stay inside the customer root and must not traverse symlinks (FileDir.php:51-107 via Apache.php:1199, Nginx.php:596).",
  "P5: Root-side chown of the stats directory built from the customer documentroot must not traverse a customer-planted symlink (Statistics.php:156-161)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "lib/Froxlor/Api/Commands/DataDump.php:86",
    "lib/Froxlor/Api/Commands/DataDump.php:88",
    "lib/Froxlor/Api/Commands/DataDump.php:91",
    "lib/Froxlor/FileDir.php:118",
    "lib/Froxlor/FileDir.php:140",
    "lib/Froxlor/Cron/System/ExportCron.php:216"
   ],
   "reason_to_dismiss": "makeCorrectDir/makeSecurePath normalize the value and the documentroot is prepended, so the path is already forced under the customer's home directory.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "lib/Froxlor/Api/Commands/DataDump.php:74",
    "lib/Froxlor/Api/Commands/DataDump.php:86",
    "lib/Froxlor/Api/Commands/DataDump.php:88",
    "lib/Froxlor/Api/Commands/DataDump.php:91",
    "lib/Froxlor/Api/Commands/DataDump.php:125",
    "lib/Froxlor/FileDir.php:118",
    "lib/Froxlor/FileDir.php:140",
    "lib/Froxlor/FileDir.php:163",
    "lib/Froxlor/Cron/System/ExportCron.php:65",
    "lib/Froxlor/Cron/System/ExportCron.php:71",
    "lib/Froxlor/Cron/System/ExportCron.php:216"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "lib/Froxlor/Api/Commands/DataDump.php:91",
    "lib/Froxlor/FileDir.php:168",
    "lib/Froxlor/FileDir.php:174"
   ],
   "reason_to_dismiss": "makeSecurePath already collapses every run of dots to one dot, so '..' traversal is impossible and a lone '.' component is harmless.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "mimo",
   "evidence": [
    "lib/Froxlor/Api/Commands/DataDump.php:86",
    "lib/Froxlor/Api/Commands/DataDump.php:88",
    "lib/Froxlor/Api/Commands/DataDump.php:91",
    "lib/Froxlor/FileDir.php:166",
    "lib/Froxlor/FileDir.php:168",
    "lib/Froxlor/FileDir.php:174",
    "lib/Froxlor/Cron/System/ExportCron.php:65"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "lib/Froxlor/Api/Commands/DataDump.php:86-93",
    "tests/Backup/DataDumpTest.php:92-100",
    "lib/Froxlor/Cron/System/ExportCron.php:69-71"
   ],
   "reason_to_dismiss": "a symlink check can simply resolve the full target path; nobody needs a data-dump folder that does not exist yet.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "tests/Backup/DataDumpTest.php:92",
    "tests/Backup/DataDumpTest.php:98",
    "tests/Backup/DataDumpTest.php:100",
    "lib/Froxlor/Cron/System/ExportCron.php:68",
    "lib/Froxlor/Cron/System/ExportCron.php:69",
    "lib/Froxlor/Cron/System/ExportCron.php:71"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/Froxlor/Cron/System/ExportCron.php:64-74",
    "lib/Froxlor/Cron/System/ExportCron.php:215-216"
   ],
   "reason_to_dismiss": "DataDump.add() validates the path (DataDump.php:86-93) and is the only producer of type-20 tasks (DataDump.php:133), so the root cron can trust the stored row.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "lib/Froxlor/Api/Commands/DataDump.php:133",
    "lib/Froxlor/Cron/System/ExportCron.php:64",
    "lib/Froxlor/Cron/System/ExportCron.php:65",
    "lib/Froxlor/Cron/System/ExportCron.php:69",
    "lib/Froxlor/Cron/System/ExportCron.php:71",
    "lib/Froxlor/Cron/System/ExportCron.php:192",
    "lib/Froxlor/Cron/System/ExportCron.php:213",
    "lib/Froxlor/Cron/System/ExportCron.php:216"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M5",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/Froxlor/Cron/System/ExportCron.php:65",
    "lib/Froxlor/Cron/System/ExportCron.php:69"
   ],
   "reason_to_dismiss": "the extra equality tests on line 69 already stop the cron from touching the customers root.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "lib/Froxlor/Cron/System/ExportCron.php:65",
    "lib/Froxlor/Cron/System/ExportCron.php:66",
    "lib/Froxlor/Cron/System/ExportCron.php:69",
    "install/froxlor.sql.php:539"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M10",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/Froxlor/Cron/System/ExportCron.php:66",
    "lib/Froxlor/Cron/System/ExportCron.php:184"
   ],
   "reason_to_dismiss": "$customerdocroot is computed right before it is used and looks like the customer's documentroot, so it is the natural base for any containment check.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "lib/Froxlor/Cron/System/ExportCron.php:66",
    "lib/Froxlor/Cron/System/ExportCron.php:69",
    "lib/Froxlor/Cron/System/ExportCron.php:184",
    "lib/Froxlor/Cron/System/ExportCron.php:185",
    "lib/Froxlor/Cron/System/TasksCron.php:204"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/Froxlor/Cron/System/ExportCron.php:98-101",
    "lib/Froxlor/Cron/System/ExportCron.php:192",
    "lib/Froxlor/Cron/System/ExportCron.php:210",
    "lib/Froxlor/Cron/System/ExportCron.php:213"
   ],
   "reason_to_dismiss": "the destination is inside the customer's own documentroot, so everything below it already belongs to the customer and chowning it to them changes nothing.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "both",
   "evidence": [
    "lib/Froxlor/Cron/System/ExportCron.php:98",
    "lib/Froxlor/Cron/System/ExportCron.php:100",
    "lib/Froxlor/Cron/System/ExportCron.php:101",
    "lib/Froxlor/Cron/System/ExportCron.php:108",
    "lib/Froxlor/Cron/System/ExportCron.php:158",
    "lib/Froxlor/Cron/System/ExportCron.php:183",
    "lib/Froxlor/Cron/System/ExportCron.php:192",
    "lib/Froxlor/Cron/System/ExportCron.php:210",
    "lib/Froxlor/Cron/System/ExportCron.php:213"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/Froxlor/Api/Commands/DirOptions.php:94-96",
    "lib/Froxlor/Cron/Http/Apache.php:1198-1199",
    "lib/Froxlor/FileDir.php:63",
    "lib/Froxlor/FileDir.php:101"
   ],
   "reason_to_dismiss": "the report is about the data-export feature; directory options use their own validation (Validate::REGEX_DIR) and the stored path is prefixed with the customer root again.",
   "distance": {
    "files": 3,
    "packages": 3
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "lib/Froxlor/Api/Commands/DirOptions.php:94",
    "lib/Froxlor/Api/Commands/DirOptions.php:96",
    "lib/Froxlor/Api/Commands/DirOptions.php:138",
    "lib/Froxlor/Validate/Validate.php:38",
    "lib/Froxlor/Cron/Http/Apache.php:1198",
    "lib/Froxlor/Cron/Http/Apache.php:1199",
    "lib/Froxlor/FileDir.php:63",
    "lib/Froxlor/FileDir.php:91",
    "lib/Froxlor/FileDir.php:93",
    "lib/Froxlor/FileDir.php:101"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/Froxlor/Api/Commands/Domains.php:392-398",
    "lib/Froxlor/Cron/Http/Nginx.php:596",
    "lib/Froxlor/Cron/Http/Apache.php:850",
    "lib/Froxlor/FileDir.php:63"
   ],
   "reason_to_dismiss": "a customer cannot choose an absolute documentroot (Domains.php:399) and the relative value is appended to the customer's own documentroot, so it stays in their tree.",
   "distance": {
    "files": 3,
    "packages": 3
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "lib/Froxlor/Api/Commands/Domains.php:392",
    "lib/Froxlor/Api/Commands/Domains.php:398",
    "lib/Froxlor/Api/Commands/Domains.php:399",
    "lib/Froxlor/Api/Commands/Domains.php:595",
    "lib/Froxlor/Cron/Http/Nginx.php:596",
    "lib/Froxlor/Cron/Http/Apache.php:850",
    "lib/Froxlor/FileDir.php:63",
    "lib/Froxlor/FileDir.php:93",
    "lib/Froxlor/FileDir.php:101"
   ]
  },
  {
   "id": "T10",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/Froxlor/Http/Statistics.php:156-161",
    "lib/Froxlor/Cron/Traffic/TrafficCron.php:215"
   ],
   "reason_to_dismiss": "the sub-directory name is a fixed setting and the path is built from the customer's own documentroot, so the customer can only affect their own tree.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "lib/Froxlor/Http/Statistics.php:156",
    "lib/Froxlor/Http/Statistics.php:159",
    "lib/Froxlor/Http/Statistics.php:161",
    "lib/Froxlor/Cron/Traffic/TrafficCron.php:207",
    "lib/Froxlor/Cron/Traffic/TrafficCron.php:215",
    "lib/Froxlor/Cron/System/TasksCron.php:234",
    "lib/Froxlor/Cron/System/TasksCron.php:235"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T3"
  ],
  [
   "T4",
   "T5",
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8",
   "T9"
  ],
  [
   "T10"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": true,
  "masking": [],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T3",
   "what": "A realpath/symlink-resolving containment check at DataDump.php:88-91 rejects destinations that do not exist yet, but tests/Backup/DataDumpTest.php:92-100 requires the non-existent '/my-dump' to be accepted and ExportCron.php:68-71 is designed to create the destination on first run."
  },
  {
   "a": "T4",
   "b": "T3",
   "what": "Re-checking containment in ExportCron::handle() with realpath(destdir) fails for a first-run export because realpath() returns false for the destination the cron is meant to create (ExportCron.php:68-71); the check has to resolve the deepest existing ancestor instead."
  }
 ],
 "fairness_risks": [
  "Requiring the dump destination to already exist contradicts the documented create-on-run behaviour (ExportCron.php:68-72) and the existing test tests/Backup/DataDumpTest.php:92-100, which uses a folder that does not exist.",
  "A blanket 'no symlink anywhere under the documentroot' rule would refuse legitimate web layouts (customers commonly keep a symlink such as a release or 'current' directory inside their docroot); the rule must be 'resolves inside the docroot', not 'contains no symlink'.",
  "FileDir::makeSecurePath already rewrites any run of dots (FileDir.php:166-174), so an added rule that rejects such names would refuse legitimate directory names such as 'backup..2024'; today such a name is silently stored under a different name.",
  "Dumps are meant to live inside the public documentroot (DataDump.php:88) and only the documentroot itself is forbidden (DataDump.php:91); a rule that forbids serving the dump would contradict the feature's design.",
  "T8, T9 and T10 are outside the DataDump advisory; a hidden test for them is only fair if the task report is worded at the class level ('symlink-safe containment of customer-controlled paths'), not as a DataDump-only report."
 ],
 "effort_minutes": 135,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T4",
   "T7",
   "T10"
  ],
  "why": "T1 is the described surface and anchors the solver. T4 is the far consumer where the protection never existed and the natural dismissal ('add() already validates and is the only producer') is wrong - the deepseek profile. T7 is the how-type nested/trailing-slash route that no validation of the requested path can close, because the customer owns the contents of the destination and can plant '.tmp' before the cron runs - the mimo profile. T10 is a second implementation of the same root chown over a customer-docroot path that needs no queued job and no export setting at all, so it survives a solver who only hardens the export feature. The four have four different reasons to dismiss and four different fix sites (DataDump.add(), ExportCron.handle(), ExportCron.createCustomerExport(), Statistics::makeChownWithNewStats), and all are reachable from public statics/APIs so behaviour can be tested. T2/T3/T5/T6/T8/T9 are recorded but either share a guard with the chosen traps (T2/T3 with T1, T5/T6 with T4, T8/T9 as one helper fix) or are too far to test fairly."
 },
 "unverified": [
  "The fix commits 9e8f32f1e860 and 2987b0e8806e were not readable (no shell in this session; file tools are restricted to the worktree), so whether DataDump.php:86-93 is A's patch and the exact scope of B's patch are inferred from the advisory wording and tests/Backup/DataDumpTest.php.",
  "The text of GHSA-75h4-c557-j89r and GHSA-4jch-8qq5-hqg6 was not fetched; only the summary in the candidate record was used.",
  "Whether hidden tests exercise ExportCron, FileDir::mkDirWithCorrectOwnership or Statistics is unknown; the pinned tree has no tests for them (only tests/Backup/DataDumpTest.php).",
  "The chown -R / rm -rf symlink-dereference through a trailing slash is assumed from GNU coreutils/PHP path semantics and was not executed here.",
  "Groups T8/T9 and T10 would collapse into one group if the fix introduced a single shared symlink-safe chown helper; as the code stands they are two different fix sites."
 ]
}
  ```
- Published fix sites:   - lib/Froxlor/Api/Commands/DataDump.php:86 — T1 M8 (reason to dismiss: makeCorrectDir/makeSecurePath normalize the value and the documentroot is prepended, so the path is already forced under the customer's home directory.)
  - lib/Froxlor/Api/Commands/DataDump.php:88 — T1 M8 (reason to dismiss: makeCorrectDir/makeSecurePath normalize the value and the documentroot is prepended, so the path is already forced under the customer's home directory.)
  - lib/Froxlor/Api/Commands/DataDump.php:91 — T1 M8 (reason to dismiss: makeCorrectDir/makeSecurePath normalize the value and the documentroot is prepended, so the path is already forced under the customer's home directory.)
  - lib/Froxlor/FileDir.php:118 — T1 M8 (reason to dismiss: makeCorrectDir/makeSecurePath normalize the value and the documentroot is prepended, so the path is already forced under the customer's home directory.)
  - lib/Froxlor/FileDir.php:140 — T1 M8 (reason to dismiss: makeCorrectDir/makeSecurePath normalize the value and the documentroot is prepended, so the path is already forced under the customer's home directory.)
  - lib/Froxlor/Cron/System/ExportCron.php:216 — T1 M8 (reason to dismiss: makeCorrectDir/makeSecurePath normalize the value and the documentroot is prepended, so the path is already forced under the customer's home directory.)
  - lib/Froxlor/Api/Commands/DataDump.php:91 — T2 M8 (reason to dismiss: makeSecurePath already collapses every run of dots to one dot, so '..' traversal is impossible and a lone '.' component is harmless.)
  - lib/Froxlor/FileDir.php:168 — T2 M8 (reason to dismiss: makeSecurePath already collapses every run of dots to one dot, so '..' traversal is impossible and a lone '.' component is harmless.)
  - lib/Froxlor/FileDir.php:174 — T2 M8 (reason to dismiss: makeSecurePath already collapses every run of dots to one dot, so '..' traversal is impossible and a lone '.' component is harmless.)
  - lib/Froxlor/Api/Commands/DataDump.php:86-93 — T3 M11 (reason to dismiss: a symlink check can simply resolve the full target path; nobody needs a data-dump folder that does not exist yet.)
  - tests/Backup/DataDumpTest.php:92-100 — T3 M11 (reason to dismiss: a symlink check can simply resolve the full target path; nobody needs a data-dump folder that does not exist yet.)
  - lib/Froxlor/Cron/System/ExportCron.php:69-71 — T3 M11 (reason to dismiss: a symlink check can simply resolve the full target path; nobody needs a data-dump folder that does not exist yet.)
  - lib/Froxlor/Cron/System/ExportCron.php:64-74 — T4 M4 (reason to dismiss: DataDump.add() validates the path (DataDump.php:86-93) and is the only producer of type-20 tasks (DataDump.php:133), so the root cron can trust the stored row.)
  - lib/Froxlor/Cron/System/ExportCron.php:215-216 — T4 M4 (reason to dismiss: DataDump.add() validates the path (DataDump.php:86-93) and is the only producer of type-20 tasks (DataDump.php:133), so the root cron can trust the stored row.)
  - lib/Froxlor/Cron/System/ExportCron.php:65 — T5 M5 (reason to dismiss: the extra equality tests on line 69 already stop the cron from touching the customers root.)
  - lib/Froxlor/Cron/System/ExportCron.php:69 — T5 M5 (reason to dismiss: the extra equality tests on line 69 already stop the cron from touching the customers root.)
  - lib/Froxlor/Cron/System/ExportCron.php:66 — T6 M10 (reason to dismiss: $customerdocroot is computed right before it is used and looks like the customer's documentroot, so it is the natural base for any containment check.)
  - lib/Froxlor/Cron/System/ExportCron.php:184 — T6 M10 (reason to dismiss: $customerdocroot is computed right before it is used and looks like the customer's documentroot, so it is the natural base for any containment check.)
- Uncovered routes to confirm (pattern B):   - lib/Froxlor/Cron/System/ExportCron.php:98-101 — T7 M8 (reason to dismiss: the destination is inside the customer's own documentroot, so everything below it already belongs to the customer and chowning it to them changes nothing.)
  - lib/Froxlor/Cron/System/ExportCron.php:192 — T7 M8 (reason to dismiss: the destination is inside the customer's own documentroot, so everything below it already belongs to the customer and chowning it to them changes nothing.)
  - lib/Froxlor/Cron/System/ExportCron.php:210 — T7 M8 (reason to dismiss: the destination is inside the customer's own documentroot, so everything below it already belongs to the customer and chowning it to them changes nothing.)
  - lib/Froxlor/Cron/System/ExportCron.php:213 — T7 M8 (reason to dismiss: the destination is inside the customer's own documentroot, so everything below it already belongs to the customer and chowning it to them changes nothing.)
  - lib/Froxlor/Api/Commands/DirOptions.php:94-96 — T8 M2 (reason to dismiss: the report is about the data-export feature; directory options use their own validation (Validate::REGEX_DIR) and the stored path is prefixed with the customer root again.)
  - lib/Froxlor/Cron/Http/Apache.php:1198-1199 — T8 M2 (reason to dismiss: the report is about the data-export feature; directory options use their own validation (Validate::REGEX_DIR) and the stored path is prefixed with the customer root again.)
  - lib/Froxlor/FileDir.php:63 — T8 M2 (reason to dismiss: the report is about the data-export feature; directory options use their own validation (Validate::REGEX_DIR) and the stored path is prefixed with the customer root again.)
  - lib/Froxlor/FileDir.php:101 — T8 M2 (reason to dismiss: the report is about the data-export feature; directory options use their own validation (Validate::REGEX_DIR) and the stored path is prefixed with the customer root again.)
  - lib/Froxlor/Api/Commands/Domains.php:392-398 — T9 M2 (reason to dismiss: a customer cannot choose an absolute documentroot (Domains.php:399) and the relative value is appended to the customer's own documentroot, so it stays in their tree.)
  - lib/Froxlor/Cron/Http/Nginx.php:596 — T9 M2 (reason to dismiss: a customer cannot choose an absolute documentroot (Domains.php:399) and the relative value is appended to the customer's own documentroot, so it stays in their tree.)
  - lib/Froxlor/Cron/Http/Apache.php:850 — T9 M2 (reason to dismiss: a customer cannot choose an absolute documentroot (Domains.php:399) and the relative value is appended to the customer's own documentroot, so it stays in their tree.)
  - lib/Froxlor/FileDir.php:63 — T9 M2 (reason to dismiss: a customer cannot choose an absolute documentroot (Domains.php:399) and the relative value is appended to the customer's own documentroot, so it stays in their tree.)
  - lib/Froxlor/Http/Statistics.php:156-161 — T10 M2 (reason to dismiss: the sub-directory name is a fixed setting and the path is built from the customer's own documentroot, so the customer can only affect their own tree.)
  - lib/Froxlor/Cron/Traffic/TrafficCron.php:215 — T10 M2 (reason to dismiss: the sub-directory name is a fixed setting and the path is built from the customer's own documentroot, so the customer can only affect their own tree.)
- Design plan from the lead: TRACK = STACKED (H3b2). Build the stacked design the reader chose: traps T1, T4, T7, T10. Why: T1 is the described surface and anchors the solver. T4 is the far consumer where the protection never existed and the natural dismissal ('add() already validates and is the only producer') is wrong - the deepseek profile. T7 is the how-type nested/trailing-slash route that no validation of the requested path can close, because the customer owns the contents of the destination and can plant '.tmp' before the cron runs - the mimo profile. T10 is a second implementation of the same root chown over a customer-docroot path that needs no queued job and no export setting at all, so it survives a solver who only hardens the export feature. The four have four different reasons to dismiss and four different fix sites (DataDump.add(), ExportCron.handle(), ExportCron.createCustomerExport(), Statistics::makeChownWithNewStats), and all are reachable from public statics/APIs so behaviour can be tested. T2/T3/T5/T6/T8/T9 are recorded but either share a guard with the chosen traps (T2/T3 with T1, T5/T6 with T4, T8/T9 as one helper fix) or are too far to test fairly. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Requiring the dump destination to already exist contradicts the documented create-on-run behaviour (ExportCron.php:68-72) and the existing test tests/Backup/DataDumpTest.php:92-100, which uses a folder that does not exist. | A blanket 'no symlink anywhere under the documentroot' rule would refuse legitimate web layouts (customers commonly keep a symlink such as a release or 'current' directory inside their docroot); the rule must be 'resolves inside the docroot', not 'contains no symlink'. | FileDir::makeSecurePath already rewrites any run of dots (FileDir.php:166-174), so an added rule that rejects such names would refuse legitimate directory names such as 'backup..2024'; today such a name is silently stored under a different name. | Dumps are meant to live inside the public documentroot (DataDump.php:88) and only the documentroot itself is forbidden (DataDump.php:91); a rule that forbids serving the dump would contradict the feature's design. | T8, T9 and T10 are outside the DataDump advisory; a hidden test for them is only fair if the task report is worded at the class level ('symlink-safe containment of customer-controlled paths'), not as a DataDump-only report.. Conflicts the reader found: A realpath/symlink-resolving containment check at DataDump.php:88-91 rejects destinations that do not exist yet, but tests/Backup/DataDumpTest.php:92-100 requires the non-existent '/my-dump' to be accepted and ExportCron.php:68-71 is designed to create the destination on first run. | Re-checking containment in ExportCron::handle() with realpath(destdir) fails for a first-run export because realpath() returns false for the destination the cron is meant to create (ExportCron.php:68-71); the check has to resolve the deepest existing ancestor instead.

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

## Environment (`tasks/stk-froxlor-ghsa75h4/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-froxlor-ghsa75h4/instruction.md`)
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

## Tests (`tasks/stk-froxlor-ghsa75h4/tests/`)
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
- **Wrong-fix patches** go in `build/stk-froxlor-ghsa75h4/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-froxlor-ghsa75h4/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-froxlor-ghsa75h4/manifest.json`:**
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

**Also in `build/stk-froxlor-ghsa75h4/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-froxlor-ghsa75h4 --only static
python3 -I common/gate/gate.py stk-froxlor-ghsa75h4 --only nop
python3 -I common/gate/gate.py stk-froxlor-ghsa75h4 --only oracle
python3 -I common/gate/gate.py stk-froxlor-ghsa75h4 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-froxlor-ghsa75h4/`;
  - edit only `tasks/stk-froxlor-ghsa75h4/`, `build/stk-froxlor-ghsa75h4/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-75h4-c557-j89r.json`. Verify each trap on the
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

Stacked task slug: `stk-froxlor-ghsa75h4`. Control task slug: `stk-froxlor-ghsa75h4-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-75h4-c557-j89r.json`.
