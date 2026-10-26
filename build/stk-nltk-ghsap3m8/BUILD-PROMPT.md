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

Project root: `/home/mara/cwe-bench`. Task: `stk-nltk-ghsap3m8`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-cgvx-9447-vcch; GHSA-p3m8-78j2-g5p3
- Pinned (vulnerable) commit: b73aa9bc6afa54c335f08d6911f5b9bbba52cd57. Published fix: 441aecb7d330, 155e40343cff.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-p3m8-78j2-g5p3",
 "pattern": "H3b",
 "repo": "nltk/nltk",
 "pinned_commit": "b73aa9bc6afa54c335f08d6911f5b9bbba52cd57",
 "protections": [
  "Download-path confinement: package id/subdir/filename and the zip extraction root come from the index and must resolve inside the caller-chosen download_dir; no such control exists at this pin (nltk/downloader.py:265, :275, :691, :707, :728).",
  "Resource-read confinement: nltk.data.find/_open must not resolve a resource name outside the configured data paths once percent- and backslash-encoded forms are decoded; only a pre-decode os.path.normpath exists (nltk/data.py:237, :242, :507, :531).",
  "Fetch-target restriction: urlopen targets taken from package metadata or from a custom index URL are not scheme- or host-constrained (nltk/downloader.py:706, :949).",
  "Install-time integrity: the downloaded archive is extracted before any checksum comparison; the index-supplied MD5 is consulted only by a later status check (nltk/downloader.py:705-737, :896).",
  "Pre-existing at the pin and not the candidate's missing control: nltk.data.load already restricts pickle classes (nltk/data.py:661-667, :763) and uses yaml.safe_load (:778); the B advisory's nltk.pathsec module and its ENFORCE flag are absent from the entire tree."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M5",
   "origin": "advisory_route",
   "locations": [
    "nltk/downloader.py:265",
    "nltk/downloader.py:275",
    "nltk/downloader.py:281",
    "nltk/downloader.py:283",
    "nltk/downloader.py:691",
    "nltk/downloader.py:707",
    "nltk/downloader.py:728"
   ],
   "reason_to_dismiss": "The index is project-owned HTTPS metadata and the changelog calls a compromised download server an 'unlikely situation' that was already fixed (ChangeLog:211-213), so an XML attribute such as filename overriding the computed name at nltk/downloader.py:275 reads as trusted stored configuration rather than attacker input.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "nltk/downloader.py:225",
    "nltk/downloader.py:265",
    "nltk/downloader.py:275",
    "nltk/downloader.py:281",
    "nltk/downloader.py:283",
    "nltk/downloader.py:691",
    "nltk/downloader.py:699",
    "nltk/downloader.py:707",
    "nltk/downloader.py:728",
    "nltk/downloader.py:875"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M7",
   "origin": "advisory_route",
   "locations": [
    "nltk/downloader.py:691",
    "nltk/downloader.py:692",
    "nltk/downloader.py:695",
    "nltk/downloader.py:698",
    "nltk/downloader.py:699"
   ],
   "reason_to_dismiss": "Deleting a stale package file and creating the install subdirectory look like ordinary pre-transfer cleanup, so a guard placed at the open/write call (nltk/downloader.py:707) appears to cover the operation even though both side effects already consumed the unvalidated path.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "nltk/downloader.py:691",
    "nltk/downloader.py:692",
    "nltk/downloader.py:695",
    "nltk/downloader.py:698",
    "nltk/downloader.py:699",
    "nltk/downloader.py:707"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "nltk/data.py:507",
    "nltk/data.py:237",
    "nltk/data.py:242",
    "nltk/data.py:531",
    "nltk/data.py:46"
   ],
   "reason_to_dismiss": "normalize_resource_name already runs os.path.normpath (nltk/data.py:237), so a check that normalizes the resource name before joining is believed to have removed '..'; leading '..' survives normpath on relative names, and url2pathname is only applied later at the join (nltk/data.py:531), so percent- and backslash-encoded forms are decoded after that normalization and a normpath-based guard misses them.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "nltk/data.py:46",
    "nltk/data.py:229",
    "nltk/data.py:237",
    "nltk/data.py:242",
    "nltk/data.py:507",
    "nltk/data.py:529",
    "nltk/data.py:531",
    "nltk/data.py:532"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M11",
   "origin": "uncovered_upstream",
   "locations": [
    "nltk/data.py:15",
    "nltk/data.py:16",
    "nltk/data.py:885",
    "nltk/data.py:887",
    "nltk/data.py:241"
   ],
   "reason_to_dismiss": "file: URLs with absolute paths are documented and doctested behaviour (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159), so leaving the file: branch at nltk/data.py:885-887 unconfined is intentional rather than a missing control, and a rule that confines it breaks a must-keep-working value.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "nltk/data.py:15",
    "nltk/data.py:16",
    "nltk/data.py:241",
    "nltk/data.py:883",
    "nltk/data.py:885",
    "nltk/data.py:887",
    "nltk/test/data.doctest:52",
    "nltk/test/data.doctest:53",
    "nltk/test/data.doctest:159"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "nltk/downloader.py:706",
    "nltk/downloader.py:949",
    "nltk/downloader.py:484",
    "nltk/downloader.py:264"
   ],
   "reason_to_dismiss": "The default index is the project's HTTPS endpoint (nltk/downloader.py:458) and choosing another index URL is an explicit user action (nltk/downloader.py:52-59), while the package URL is metadata from that same index, so no scheme or host check looks necessary at the fetch site.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "nltk/downloader.py:52",
    "nltk/downloader.py:458",
    "nltk/downloader.py:484",
    "nltk/downloader.py:485",
    "nltk/downloader.py:264",
    "nltk/downloader.py:706",
    "nltk/downloader.py:949"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "nltk/downloader.py:705",
    "nltk/downloader.py:727",
    "nltk/downloader.py:896",
    "nltk/downloader.py:245"
   ],
   "reason_to_dismiss": "The MD5 is taken from the same index as the URL (nltk/downloader.py:245), so it is not an independent trust anchor and verifying it at install time looks redundant; the existing comparison at nltk/downloader.py:896 only runs during a later status check, after the archive has already been extracted at :727-733.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "nltk/downloader.py:245",
    "nltk/downloader.py:705",
    "nltk/downloader.py:707",
    "nltk/downloader.py:723",
    "nltk/downloader.py:727",
    "nltk/downloader.py:733",
    "nltk/downloader.py:896"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "nltk/data.py:332",
    "nltk/data.py:333",
    "nltk/data.py:334",
    "nltk/corpus/reader/api.py:170",
    "nltk/corpus/reader/api.py:195",
    "nltk/corpus/reader/api.py:231"
   ],
   "reason_to_dismiss": "File ids are corpus-internal identifiers selected by the reader, and joining them onto the corpus root is the documented way to reach a corpus file (nltk/corpus/reader/api.py:161-170, :222-232), so they do not look like request-controlled paths and the join at nltk/data.py:332-334 adds no check.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "nltk/data.py:332",
    "nltk/data.py:333",
    "nltk/data.py:334",
    "nltk/corpus/reader/api.py:161",
    "nltk/corpus/reader/api.py:170",
    "nltk/corpus/reader/api.py:195",
    "nltk/corpus/reader/api.py:222",
    "nltk/corpus/reader/api.py:231"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": true,
  "masking": [
   "The percent/backslash shape in T3 only defeats the guard once a normalization-based check is added to nltk.data.find; with no guard at the pin every name is accepted, so the shape becomes observable only after the literal '..' route in the same function is fixed.",
   "The downloader traps T1/T2/T5/T6 only become observable once pathsec enforcement is on: while the A-era control is controlled by a default-false switch (the B advisory), every check is a no-op and the sinks behave exactly as they do at this pin."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T4",
   "what": "A single global pathsec policy that turns enforcement on for both writes and reads (the natural fix for T1, and exactly what the B fix flips) also confines nltk.data reads and rejects the documented absolute file: loads that T4 must keep working (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159)."
  },
  {
   "a": "T2",
   "b": "T3",
   "what": "Fixing T2 by normalizing and confining the resource name at nltk/data.py:507-531 must still allow absolute file: paths (T3); percent decoding therefore has to happen before the confinement test, and a check that runs on the pre-decode name breaks the T3 must-keep-working value."
  }
 ],
 "fairness_risks": [
  "Custom download_dir must remain any caller-chosen writable path, including nested non-existent parents (nltk/downloader.py:46-47, :616-620; nltk/test/unit/test_downloader.py:4-19); a rule that permits writes only under CWD or NLTK's own data directory breaks this legitimate use.",
  "A caller-supplied server_index_url is documented (nltk/downloader.py:52-59, :484-486) and may be a mirror or a local index; forbidding non-GitHub or non-HTTPS index URLs breaks that documented configuration.",
  "Absolute file: resource loads are documented and doctested (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159), and nltk.data.retrieve writes to a caller-chosen filename relative to CWD (nltk/test/data.doctest:168-179); a blanket 'no reads or writes outside nltk_data' rule contradicts both.",
  "Corpus file ids legitimately contain separators for nested corpus layouts (nltk/corpus/reader/ycoe.py:41-43 joins 'psd' and 'pos' onto the corpus root; nltk/corpus/reader/api.py:170, :195, :231 pass caller file ids straight through), so a rule that refuses any file id containing a separator or a '..' component also refuses shapes legitimate corpus code produces."
 ],
 "effort_minutes": 130,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T3",
   "T4",
   "T5",
   "T6"
  ],
  "why": "Five independent guards, each with a different dismissal argument, and both model-specific failure modes. The deepseek trio is where a protection is simply absent under a plausible 'trusted configuration' reason: index-supplied destination path (T1, whose remove/mkdir ordering T2 shares and which one validation at the package-record boundary closes), the official-HTTPS index argument for the fetch target (T5), and checksum-from-the-same-index for install integrity (T6); a solver that accepts 'the index is trusted' loses all three. The mimo pair is where the tempting fix is over-broad: T3 shows normalization-before-decode shapes defeating a normpath-style check, and T4 requires keeping documented absolute file: loads while still blocking escapes. The five guards are behaviourally separable (destination path, resource-name decoding, read-root policy, fetch target, install-time integrity), so tests can distinguish partial fixes. T7 (corpus-reader join) is a real but distant second read path and is left out of the five. Caveat for the harness: the B advisory's nltk.pathsec module is not in this checkout, so the stacked task must be scoped to these A-era sinks visible at the pin; if hidden tests import pathsec symbols, the candidate needs re-pinning to the parent of b_fix 155e40343cff."
 },
 "unverified": [
  "Pin/A-fix mismatch: /home/mara/cwe-bench/pipelines/stacking/out/reader-ds/_run.log:132 records this job as pin=b73aa9bc6a (parent of 441aecb7d3), and the candidate metadata gives a_fix=441aecb7d330 and b_fix=155e40343cff. The pinned tree therefore precedes A, not B.",
  "The B mechanism has no code location at this pin: a case-insensitive grep for pathsec/path_sec/ENFORCE/enforce finds no nltk.pathsec module and no ENFORCE symbol (only nltk/tbl/feature.py:55 and the VerbNet class 'enforce-63' in nltk/test/corpus.doctest:951), and a glob for **/*path* returns nothing. A's pathsec module and B's default flag are not inspectable anywhere in the worktree.",
  "Advisory identification is from model knowledge, not from the tree: CVE-2024-39705 / GHSA-cgvx-9447-vcch is the NLTK package-download/data security fix and GHSA-p3m8-78j2-g5p3 is the later report that pathsec's ENFORCE=False default disables those controls. No advisory text, patch, or fix diff exists under the pinned tree.",
  "History fields a_fix_leaves_b_open=true and b_in_code_a_wrote=true are inferences from the candidate metadata and the B summary (A introduces pathsec, B says its default disables it), not from pinned code, because the A/B commits are unreachable from this worktree.",
  "The scope of pathsec is unknown: whether its controls cover only the downloader or also nltk.data reads (T3, T4) and corpus-reader file ids (T7) cannot be decided from the tree; T3/T4/T7 are therefore recorded as uncovered_upstream, not as confirmed advisory routes.",
  "Not recorded as a trap: nltk/downloader.py:2250 calls zf.extractall(root) with no NLTK-level member-name check, but CPython's ZipFile._extract_member (Python >=3.8, and setup.py:114 requires >=3.8) strips absolute paths and '..' path components, so the member-name sink is not itself an escape; the unprotected part is the index-derived extraction root recorded in T1. This relies on CPython behaviour, not on an artefact in the pin.",
  "Also not recorded: nltk/downloader.py:948-950 parses the remote index with stdlib ElementTree, which is entity-expansion-prone, but that is a DoS hardening item outside pathsec and the default index is HTTPS.",
  "Hidden tests built from B may import nltk.pathsec symbols that do not exist at this pin; if the task's tests do that, the candidate must be re-pinned to the parent of b_fix 155e40343cff before it can run."
 ]
}
  ```
- Published fix sites:   - nltk/downloader.py:265 — T1 M5 (reason to dismiss: The index is project-owned HTTPS metadata and the changelog calls a compromised download server an 'unlikely situation' that was already fixed (ChangeLog:211-213), so an XML attribute such as filename overriding the computed name at nltk/downloader.py:275 reads as trusted stored configuration rather than attacker input.)
  - nltk/downloader.py:275 — T1 M5 (reason to dismiss: The index is project-owned HTTPS metadata and the changelog calls a compromised download server an 'unlikely situation' that was already fixed (ChangeLog:211-213), so an XML attribute such as filename overriding the computed name at nltk/downloader.py:275 reads as trusted stored configuration rather than attacker input.)
  - nltk/downloader.py:281 — T1 M5 (reason to dismiss: The index is project-owned HTTPS metadata and the changelog calls a compromised download server an 'unlikely situation' that was already fixed (ChangeLog:211-213), so an XML attribute such as filename overriding the computed name at nltk/downloader.py:275 reads as trusted stored configuration rather than attacker input.)
  - nltk/downloader.py:283 — T1 M5 (reason to dismiss: The index is project-owned HTTPS metadata and the changelog calls a compromised download server an 'unlikely situation' that was already fixed (ChangeLog:211-213), so an XML attribute such as filename overriding the computed name at nltk/downloader.py:275 reads as trusted stored configuration rather than attacker input.)
  - nltk/downloader.py:691 — T1 M5 (reason to dismiss: The index is project-owned HTTPS metadata and the changelog calls a compromised download server an 'unlikely situation' that was already fixed (ChangeLog:211-213), so an XML attribute such as filename overriding the computed name at nltk/downloader.py:275 reads as trusted stored configuration rather than attacker input.)
  - nltk/downloader.py:707 — T1 M5 (reason to dismiss: The index is project-owned HTTPS metadata and the changelog calls a compromised download server an 'unlikely situation' that was already fixed (ChangeLog:211-213), so an XML attribute such as filename overriding the computed name at nltk/downloader.py:275 reads as trusted stored configuration rather than attacker input.)
  - nltk/downloader.py:728 — T1 M5 (reason to dismiss: The index is project-owned HTTPS metadata and the changelog calls a compromised download server an 'unlikely situation' that was already fixed (ChangeLog:211-213), so an XML attribute such as filename overriding the computed name at nltk/downloader.py:275 reads as trusted stored configuration rather than attacker input.)
  - nltk/downloader.py:691 — T2 M7 (reason to dismiss: Deleting a stale package file and creating the install subdirectory look like ordinary pre-transfer cleanup, so a guard placed at the open/write call (nltk/downloader.py:707) appears to cover the operation even though both side effects already consumed the unvalidated path.)
  - nltk/downloader.py:692 — T2 M7 (reason to dismiss: Deleting a stale package file and creating the install subdirectory look like ordinary pre-transfer cleanup, so a guard placed at the open/write call (nltk/downloader.py:707) appears to cover the operation even though both side effects already consumed the unvalidated path.)
  - nltk/downloader.py:695 — T2 M7 (reason to dismiss: Deleting a stale package file and creating the install subdirectory look like ordinary pre-transfer cleanup, so a guard placed at the open/write call (nltk/downloader.py:707) appears to cover the operation even though both side effects already consumed the unvalidated path.)
  - nltk/downloader.py:698 — T2 M7 (reason to dismiss: Deleting a stale package file and creating the install subdirectory look like ordinary pre-transfer cleanup, so a guard placed at the open/write call (nltk/downloader.py:707) appears to cover the operation even though both side effects already consumed the unvalidated path.)
  - nltk/downloader.py:699 — T2 M7 (reason to dismiss: Deleting a stale package file and creating the install subdirectory look like ordinary pre-transfer cleanup, so a guard placed at the open/write call (nltk/downloader.py:707) appears to cover the operation even though both side effects already consumed the unvalidated path.)
- Uncovered routes to confirm (pattern B):   - nltk/data.py:507 — T3 M8 (reason to dismiss: normalize_resource_name already runs os.path.normpath (nltk/data.py:237), so a check that normalizes the resource name before joining is believed to have removed '..'; leading '..' survives normpath on relative names, and url2pathname is only applied later at the join (nltk/data.py:531), so percent- and backslash-encoded forms are decoded after that normalization and a normpath-based guard misses them.)
  - nltk/data.py:237 — T3 M8 (reason to dismiss: normalize_resource_name already runs os.path.normpath (nltk/data.py:237), so a check that normalizes the resource name before joining is believed to have removed '..'; leading '..' survives normpath on relative names, and url2pathname is only applied later at the join (nltk/data.py:531), so percent- and backslash-encoded forms are decoded after that normalization and a normpath-based guard misses them.)
  - nltk/data.py:242 — T3 M8 (reason to dismiss: normalize_resource_name already runs os.path.normpath (nltk/data.py:237), so a check that normalizes the resource name before joining is believed to have removed '..'; leading '..' survives normpath on relative names, and url2pathname is only applied later at the join (nltk/data.py:531), so percent- and backslash-encoded forms are decoded after that normalization and a normpath-based guard misses them.)
  - nltk/data.py:531 — T3 M8 (reason to dismiss: normalize_resource_name already runs os.path.normpath (nltk/data.py:237), so a check that normalizes the resource name before joining is believed to have removed '..'; leading '..' survives normpath on relative names, and url2pathname is only applied later at the join (nltk/data.py:531), so percent- and backslash-encoded forms are decoded after that normalization and a normpath-based guard misses them.)
  - nltk/data.py:46 — T3 M8 (reason to dismiss: normalize_resource_name already runs os.path.normpath (nltk/data.py:237), so a check that normalizes the resource name before joining is believed to have removed '..'; leading '..' survives normpath on relative names, and url2pathname is only applied later at the join (nltk/data.py:531), so percent- and backslash-encoded forms are decoded after that normalization and a normpath-based guard misses them.)
  - nltk/data.py:15 — T4 M11 (reason to dismiss: file: URLs with absolute paths are documented and doctested behaviour (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159), so leaving the file: branch at nltk/data.py:885-887 unconfined is intentional rather than a missing control, and a rule that confines it breaks a must-keep-working value.)
  - nltk/data.py:16 — T4 M11 (reason to dismiss: file: URLs with absolute paths are documented and doctested behaviour (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159), so leaving the file: branch at nltk/data.py:885-887 unconfined is intentional rather than a missing control, and a rule that confines it breaks a must-keep-working value.)
  - nltk/data.py:885 — T4 M11 (reason to dismiss: file: URLs with absolute paths are documented and doctested behaviour (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159), so leaving the file: branch at nltk/data.py:885-887 unconfined is intentional rather than a missing control, and a rule that confines it breaks a must-keep-working value.)
  - nltk/data.py:887 — T4 M11 (reason to dismiss: file: URLs with absolute paths are documented and doctested behaviour (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159), so leaving the file: branch at nltk/data.py:885-887 unconfined is intentional rather than a missing control, and a rule that confines it breaks a must-keep-working value.)
  - nltk/data.py:241 — T4 M11 (reason to dismiss: file: URLs with absolute paths are documented and doctested behaviour (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159), so leaving the file: branch at nltk/data.py:885-887 unconfined is intentional rather than a missing control, and a rule that confines it breaks a must-keep-working value.)
  - nltk/downloader.py:706 — T5 M4 (reason to dismiss: The default index is the project's HTTPS endpoint (nltk/downloader.py:458) and choosing another index URL is an explicit user action (nltk/downloader.py:52-59), while the package URL is metadata from that same index, so no scheme or host check looks necessary at the fetch site.)
  - nltk/downloader.py:949 — T5 M4 (reason to dismiss: The default index is the project's HTTPS endpoint (nltk/downloader.py:458) and choosing another index URL is an explicit user action (nltk/downloader.py:52-59), while the package URL is metadata from that same index, so no scheme or host check looks necessary at the fetch site.)
  - nltk/downloader.py:484 — T5 M4 (reason to dismiss: The default index is the project's HTTPS endpoint (nltk/downloader.py:458) and choosing another index URL is an explicit user action (nltk/downloader.py:52-59), while the package URL is metadata from that same index, so no scheme or host check looks necessary at the fetch site.)
  - nltk/downloader.py:264 — T5 M4 (reason to dismiss: The default index is the project's HTTPS endpoint (nltk/downloader.py:458) and choosing another index URL is an explicit user action (nltk/downloader.py:52-59), while the package URL is metadata from that same index, so no scheme or host check looks necessary at the fetch site.)
  - nltk/downloader.py:705 — T6 M4 (reason to dismiss: The MD5 is taken from the same index as the URL (nltk/downloader.py:245), so it is not an independent trust anchor and verifying it at install time looks redundant; the existing comparison at nltk/downloader.py:896 only runs during a later status check, after the archive has already been extracted at :727-733.)
  - nltk/downloader.py:727 — T6 M4 (reason to dismiss: The MD5 is taken from the same index as the URL (nltk/downloader.py:245), so it is not an independent trust anchor and verifying it at install time looks redundant; the existing comparison at nltk/downloader.py:896 only runs during a later status check, after the archive has already been extracted at :727-733.)
  - nltk/downloader.py:896 — T6 M4 (reason to dismiss: The MD5 is taken from the same index as the URL (nltk/downloader.py:245), so it is not an independent trust anchor and verifying it at install time looks redundant; the existing comparison at nltk/downloader.py:896 only runs during a later status check, after the archive has already been extracted at :727-733.)
  - nltk/downloader.py:245 — T6 M4 (reason to dismiss: The MD5 is taken from the same index as the URL (nltk/downloader.py:245), so it is not an independent trust anchor and verifying it at install time looks redundant; the existing comparison at nltk/downloader.py:896 only runs during a later status check, after the archive has already been extracted at :727-733.)
  - nltk/data.py:332 — T7 M1 (reason to dismiss: File ids are corpus-internal identifiers selected by the reader, and joining them onto the corpus root is the documented way to reach a corpus file (nltk/corpus/reader/api.py:161-170, :222-232), so they do not look like request-controlled paths and the join at nltk/data.py:332-334 adds no check.)
  - nltk/data.py:333 — T7 M1 (reason to dismiss: File ids are corpus-internal identifiers selected by the reader, and joining them onto the corpus root is the documented way to reach a corpus file (nltk/corpus/reader/api.py:161-170, :222-232), so they do not look like request-controlled paths and the join at nltk/data.py:332-334 adds no check.)
  - nltk/data.py:334 — T7 M1 (reason to dismiss: File ids are corpus-internal identifiers selected by the reader, and joining them onto the corpus root is the documented way to reach a corpus file (nltk/corpus/reader/api.py:161-170, :222-232), so they do not look like request-controlled paths and the join at nltk/data.py:332-334 adds no check.)
  - nltk/corpus/reader/api.py:170 — T7 M1 (reason to dismiss: File ids are corpus-internal identifiers selected by the reader, and joining them onto the corpus root is the documented way to reach a corpus file (nltk/corpus/reader/api.py:161-170, :222-232), so they do not look like request-controlled paths and the join at nltk/data.py:332-334 adds no check.)
  - nltk/corpus/reader/api.py:195 — T7 M1 (reason to dismiss: File ids are corpus-internal identifiers selected by the reader, and joining them onto the corpus root is the documented way to reach a corpus file (nltk/corpus/reader/api.py:161-170, :222-232), so they do not look like request-controlled paths and the join at nltk/data.py:332-334 adds no check.)
  - nltk/corpus/reader/api.py:231 — T7 M1 (reason to dismiss: File ids are corpus-internal identifiers selected by the reader, and joining them onto the corpus root is the documented way to reach a corpus file (nltk/corpus/reader/api.py:161-170, :222-232), so they do not look like request-controlled paths and the join at nltk/data.py:332-334 adds no check.)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T3, T4, T5, T6. Why: Five independent guards, each with a different dismissal argument, and both model-specific failure modes. The deepseek trio is where a protection is simply absent under a plausible 'trusted configuration' reason: index-supplied destination path (T1, whose remove/mkdir ordering T2 shares and which one validation at the package-record boundary closes), the official-HTTPS index argument for the fetch target (T5), and checksum-from-the-same-index for install integrity (T6); a solver that accepts 'the index is trusted' loses all three. The mimo pair is where the tempting fix is over-broad: T3 shows normalization-before-decode shapes defeating a normpath-style check, and T4 requires keeping documented absolute file: loads while still blocking escapes. The five guards are behaviourally separable (destination path, resource-name decoding, read-root policy, fetch target, install-time integrity), so tests can distinguish partial fixes. T7 (corpus-reader join) is a real but distant second read path and is left out of the five. Caveat for the harness: the B advisory's nltk.pathsec module is not in this checkout, so the stacked task must be scoped to these A-era sinks visible at the pin; if hidden tests import pathsec symbols, the candidate needs re-pinning to the parent of b_fix 155e40343cff. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Custom download_dir must remain any caller-chosen writable path, including nested non-existent parents (nltk/downloader.py:46-47, :616-620; nltk/test/unit/test_downloader.py:4-19); a rule that permits writes only under CWD or NLTK's own data directory breaks this legitimate use. | A caller-supplied server_index_url is documented (nltk/downloader.py:52-59, :484-486) and may be a mirror or a local index; forbidding non-GitHub or non-HTTPS index URLs breaks that documented configuration. | Absolute file: resource loads are documented and doctested (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159), and nltk.data.retrieve writes to a caller-chosen filename relative to CWD (nltk/test/data.doctest:168-179); a blanket 'no reads or writes outside nltk_data' rule contradicts both. | Corpus file ids legitimately contain separators for nested corpus layouts (nltk/corpus/reader/ycoe.py:41-43 joins 'psd' and 'pos' onto the corpus root; nltk/corpus/reader/api.py:170, :195, :231 pass caller file ids straight through), so a rule that refuses any file id containing a separator or a '..' component also refuses shapes legitimate corpus code produces.. Conflicts the reader found: A single global pathsec policy that turns enforcement on for both writes and reads (the natural fix for T1, and exactly what the B fix flips) also confines nltk.data reads and rejects the documented absolute file: loads that T4 must keep working (nltk/data.py:15-16; nltk/test/data.doctest:52-56, :159). | Fixing T2 by normalizing and confining the resource name at nltk/data.py:507-531 must still allow absolute file: paths (T3); percent decoding therefore has to happen before the confinement test, and a check that runs on the pre-decode name breaks the T3 must-keep-working value.

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

## Environment (`tasks/stk-nltk-ghsap3m8/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-nltk-ghsap3m8/instruction.md`)
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

## Tests (`tasks/stk-nltk-ghsap3m8/tests/`)
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
- **Wrong-fix patches** go in `build/stk-nltk-ghsap3m8/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-nltk-ghsap3m8/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-nltk-ghsap3m8/manifest.json`:**
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

**Also in `build/stk-nltk-ghsap3m8/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-nltk-ghsap3m8 --only static
python3 -I common/gate/gate.py stk-nltk-ghsap3m8 --only nop
python3 -I common/gate/gate.py stk-nltk-ghsap3m8 --only oracle
python3 -I common/gate/gate.py stk-nltk-ghsap3m8 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-nltk-ghsap3m8/`;
  - edit only `tasks/stk-nltk-ghsap3m8/`, `build/stk-nltk-ghsap3m8/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-p3m8-78j2-g5p3.json`. Verify each trap on the
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
- `score_at_build`: from `pipelines/stacking/1-select/score_stack.py`;
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

Stacked task slug: `stk-nltk-ghsap3m8`. Control task slug: `stk-nltk-ghsap3m8-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-p3m8-78j2-g5p3.json`.
