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

Project root: `/home/mara/cwe-bench`. Task: `stk-copyparty-6317`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 6317; CWE-863 incorrect authorization: per-file capability (filekey) escalat
- Pinned (vulnerable) commit: 89040874f53e426e54a94787a3e3ddfa2acd1bad. Published fix: e40755331ba9449993ff482456e6bdd2c6deb950.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-6317",
 "pattern": "H4",
 "repo": "9001/copyparty",
 "pinned_commit": "89040874f53e426e54a94787a3e3ddfa2acd1bad",
 "protections": [
  "P1 folder capability: a folder's dirkey (and the dirkeys of its subfolders) may only be emitted to a caller who already holds folder-level access to that folder - read permission, or that folder's own dirkey (enforced correctly at the ?tree= emitter via the will_read flag, httpcli.py:5874-5890,5910-5917, but not at the browser listing emitter, httpcli.py:7207-7215,7254-7259,7304-7308).",
  "P2 file capability: a filekey may only be emitted for a file the caller can already fetch - read, the folder's dirkey, its own filekey, or upget/uploader status (httpcli.py:2775-2784, 3975-3984, 7293-7303; up2k.py:3493-3503).",
  "P3 file fetch without read: a caller without read may fetch a file only with a valid filekey, or through the documented exemptions - index.html for permission 'h' (httpcli.py:6912-6940), share paths (httpcli.py:6948), or a valid dirkey for the containing folder (httpcli.py:6840-6848,6942-6950)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "copyparty/httpcli.py:7207",
    "copyparty/httpcli.py:7210-7215",
    "copyparty/httpcli.py:6953-6962",
    "copyparty/httpcli.py:6840-6848",
    "copyparty/httpcli.py:7173-7175"
   ],
   "reason_to_dismiss": "The page the emitter runs for is narrowed to the single file the filekey covers (httpcli.py:7173-7175), so serving that page looks scoped to that one file; P1 has no check at all here because add_dk is derived from the volume flag only (7207), which is exactly the advisory's flaw.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "copyparty/httpcli.py:7207 add_dk = vf.get(\"dk\") is the only decision; use_filekey/use_dirkey are not consulted",
    "copyparty/httpcli.py:7214-7215 the value is minted into both the JSON listing (ls_ret[\"dk\"]) and the HTML template context (cgv[\"dk\"])",
    "copyparty/httpcli.py:6953-6962 a file request with ?v is rewritten into the parent folder (vpath,og_fn = vsplit(...)), vn re-resolved without any permission requirement, is_dk set True",
    "copyparty/httpcli.py:6840-6848 the filekey is classified against the file (abspath) but the emitted key is for the parent folder",
    "copyparty/web/browser.html:138 CGV = {{ cgv|tojson }} ships the dk to the client; copyparty/web/browser.js:7519,7543,7558 use it to browse",
    "copyparty/httpcli.py:7463 the same ls_ret (with \"dk\") is returned as JSON for ?ls",
    "README.md:3108 volflag dk grants read-access to that folder - the emitted key is that capability"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "copyparty/httpcli.py:6939-6940",
    "copyparty/httpcli.py:6932-6934",
    "copyparty/httpcli.py:6953-6962",
    "copyparty/httpcli.py:7207-7215"
   ],
   "reason_to_dismiss": "index.html is documented as retrievable without a filekey (README.md:544, README.md:3066, docs/changelog.md:3839), so the key-exempt fetch reads as a sanctioned exception; the is_dir branch clears add_og before falling through (6934) while the direct index.html branch does not (6939-6940), which reads as deliberate scoping rather than a hole.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "copyparty/authsrv.py:1661-1665 permission 'h' expands to 'gh', so an 'h' user has can_get and can_html but not can_read",
    "copyparty/httpcli.py:6912-6913 the index.html path requires can_get and can_html; copyparty/httpcli.py:6939-6940 sets fk_pass for a direct index.html fetch and does not clear add_og",
    "copyparty/httpcli.py:6943-6950 the filekey gate is waived by fk_pass, so no key is ever presented",
    "copyparty/httpcli.py:6953-6962 ?v turns the request into a listing of the parent folder; copyparty/httpcli.py:7161 lists it without any read requirement",
    "copyparty/httpcli.py:7207-7215 add_dk fires on the volume flag alone, so the parent folder's dirkey lands in the page/JSON of a caller who presented no key",
    "copyparty/httpcli.py:7326-7327 dirs are dropped only when dks is absent, so with dks the emitted key also opens subfolders",
    "README.md:544 'folder return their index.html, and filekeys are not necessary for index.html'"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "copyparty/httpcli.py:6851-6853",
    "copyparty/httpcli.py:6942-6950",
    "copyparty/httpcli.py:6953-6962",
    "copyparty/httpcli.py:7207-7215"
   ],
   "reason_to_dismiss": "README.md:3116 says filekeys should be enabled together with dirkeys, so a dks volume without fk reads as an ill-advised configuration the project need not support; and 'g' is documented as 'download files if you know the name' (README.md:542), so serving the one named file looks correct.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "copyparty/authsrv.py:2388-2400 dks/dky normalise into flags[\"dk\"], so a dks-only volume still trips the emitter",
    "copyparty/httpcli.py:6851-6853 a get-only caller on a volume without fk passes the file gate without any key",
    "copyparty/httpcli.py:6943-6950 the 404 only fires when 'fk' is in vn.flags, so nothing stops the request on a dks-without-fk volume",
    "copyparty/httpcli.py:6953-6962 any known filename plus ?v becomes a listing of its parent folder (no Referer header defeats the hotlink check at 6954)",
    "copyparty/httpcli.py:7207-7215 the folder's dirkey is emitted to a caller who never held a key; copyparty/httpcli.py:6993-7000 shows the same caller is refused a direct folder listing, so the key is the escalation"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M6",
   "origin": "injection_room",
   "locations": [
    "copyparty/authsrv.py:3181",
    "copyparty/authsrv.py:3166-3176",
    "copyparty/authsrv.py:1994-1998",
    "copyparty/httpcli.py:7207-7215",
    "copyparty/httpcli.py:6948"
   ],
   "reason_to_dismiss": "A share is an admin/user-created capability, so a recipient looks entitled; the emitted dirkey names the source folder's path, which the share URL never reveals, so it reads as unexploitable; and --shr is a non-default global option (svchub.py:738).",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "copyparty/authsrv.py:3181 shn.flags = o_vn.flags.copy() gives every share node the source volume's volflags, including dk/dks/fk normalised at authsrv.py:2388-2400",
    "copyparty/authsrv.py:3166-3176 a single-file share keeps shr_src=(source vfs, source dir) and realpath=the source directory, so the node's canonical path is the source folder",
    "copyparty/authsrv.py:1994 the share node is built with vf0() flags; 3181 is the only place the source flags arrive",
    "copyparty/httpcli.py:7207-7215 the emitter mints the source folder's dirkey for the share node (gen_fk over the source abspath)",
    "copyparty/httpcli.py:6948 share paths are exempt from the filekey gate, and a share with 'r' (httpcli.py:6474-6480) makes can_read true on the share node, so a folder-authorization guard written as 'can_read or use_dirkey' does not close this case",
    "copyparty/httpcli.py:7463 the dirkey is also in the ?ls JSON"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "copyparty/httpcli.py:7293-7303",
    "copyparty/httpcli.py:7304-7308",
    "copyparty/httpcli.py:7671-7684",
    "tests/test_dots.py:289-293",
    "tests/test_dots.py:311-313",
    "tests/test_dots.py:319-327"
   ],
   "reason_to_dismiss": "Filekeys in a dirkey listing and the filekey inside og_thumb/og_raw are pre-existing, documented behaviours (README.md:3116, docs/changelog.md:2488) that the report does not ask to change, so they look out of scope.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "easy",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "copyparty/httpcli.py:7293-7303 a dirkey-authorized listing must keep emitting per-file filekeys; tests/test_dots.py:289-293 asserts the ?k= on each file href",
    "copyparty/httpcli.py:7304-7308 with dks the listing must keep emitting subfolder dirkeys; tests/test_dots.py:319-327 asserts dirs[0][\"href\"][:6] == \"s1/?k=\"",
    "copyparty/httpcli.py:7671-7672 and 7683-7684 the filekey must stay embedded in og_thumb/og_raw for a filekey-shared file; tests/test_dots.py:311-313 fetches a thumbnail through a dirkey-listing filekey",
    "copyparty/httpcli.py:7044 is_dk already adds 'read' to the reported perms, so a naive 'no keys for non-read callers' rule contradicts the page's own state",
    "README.md:3116 explains why filekeys are needed together with dirkeys (hotlinking from a dirkey-shared folder)"
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
   "T4"
  ],
  [
   "T5"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "A guard written as 'only emit dk to callers with read' (the obvious reading of the advisory) suppresses the dks subfolder dirkeys at httpcli.py:7304-7308, which dirkey callers need and tests/test_dots.py:319-327 assert; the guard has to be 'can_read or use_dirkey'."
  },
  {
   "a": "T1",
   "b": "T5",
   "what": "Refusing the ?v viewer (or dropping keys) for non-read callers breaks the filekey echo into og_thumb/og_raw (httpcli.py:7671-7684) and the filekey hotlinks a dirkey listing must keep (httpcli.py:7293-7303, tests/test_dots.py:311-313)."
  },
  {
   "a": "T4",
   "b": "T5",
   "what": "The cleanest T4 fix (stop copying dk/dks onto share nodes at authsrv.py:3181) also strips the dks subfolder navigation that a legitimate folder share relies on (httpcli.py:7304-7308), so the fix has to distinguish single-file shares (shr_files set, authsrv.py:3166) from folder shares."
  },
  {
   "a": "T2",
   "b": "T5",
   "what": "Closing T2 by clearing add_og at httpcli.py:6940 changes the response for an 'h' user fetching index.html with ?v from the opengraph page to the raw file; the documented behaviour (README.md:544,3066) only promises index.html without a filekey, so the fix must keep returning index.html."
  }
 ],
 "fairness_risks": [
  "A rule that denies the opengraph view to callers without read contradicts the documented og/og_ua feature (README.md:1639-1645), whose whole purpose is link previews for shared file URLs.",
  "A rule that refuses ?k=<filekey>&v refuses the documented combination of filekeys and opengraph (docs/changelog.md:2488) and the medialinks uploader link, which appends &v to a ?k= URL (httpcli.py:2775-2787).",
  "A rule that requires read to receive any key breaks the dirkeys feature itself: dirkey recipients never have read (README.md:3106-3114, httpcli.py:4314-4317).",
  "A rule that suppresses filekeys in a dirkey listing breaks hotlinking from a dirkey-shared folder (README.md:3116; tests/test_dots.py:289-293,311-313).",
  "A rule that requires a key for index.html contradicts the documented 'h' permission semantics (README.md:544,3066, docs/changelog.md:3839).",
  "A rule that drops dk from share nodes entirely breaks dks navigation for folder shares."
 ],
 "effort_minutes": 45,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T5"
  ],
  "why": "Three independent judgements, five route-level tests. (1) T1/T2/T3 are one missing check at one site (httpcli.py:7207-7215) but three entry conditions with three different dismissal arguments: a validated filekey (T1, the advisory), the documented index.html-without-a-filekey exemption for 'h' (T2), and a dks volume with no fk that the docs call ill-advised (T3). The published one-liner ('not use_filekey') closes only T1, so a solver who reproduces it fails the two keyless routes; the correct predicate is folder-level authorization ('can_read or use_dirkey'), which the ?tree= emitter already uses at httpcli.py:5874-5890. This is the deepseek-type core: protection absent plus a plausible reason to dismiss. (2) T4 is independent of that guard because a single-file share with 'r' sets can_read from the share grant while the emitter's key is for the source folder: the producer (authsrv.py:3181 copies the source volume's dk/dks/fk onto every share node) is the only place the two can be told apart, so it is a separate fix site and a separate judgement. (3) T5 is the mimo-type constraint: the fix must not over-harden - it has to keep filekeys in a dirkey listing, subfolder dirkeys under dks, and the filekey embedded in og_thumb/og_raw, all asserted in tests/test_dots.py:289-293,311-313,319-327. The stack is real but thin: 75% of it can be closed by one corrected predicate, so the hidden tests must include at least one keyless route and one share case for the stacking to bite."
 },
 "unverified": [
  "No shell was available, so the published fix diff (e4075533) could not be read; the claim that the upstream patch is only 'not use_filekey' comes from the screener's record and from the shape of httpcli.py:7207, not from the diff.",
  "Git history is unavailable in this session, so the H3 questions (an earlier fix that left this open, or a regression in code an earlier fix wrote) could not be answered; the only in-tree evidence is the hardened sibling at httpcli.py:5874-5890 whose read-or-dirkey rule the browser emitter does not use.",
  "authsrv.py:786-803 exposes subvolumes in a listing when the parent volume has the dk flag, and httpcli.py:7304-7308 mints their dirkeys with the parent's length; I could not construct a config where this hands a key to a caller not already entitled, so it is recorded as injection room only.",
  "The ?tree= endpoint (httpcli.py:5874-5890,5910-5917) was checked and appears closed: with no valid dirkey dk_sz stays False, vfs.get(..., will_read=True) raises for a get-only caller and the except branch nulls dk_sz, so no keys are minted. Not listed as a trap.",
  "Whether the hidden tests can name the source folder of a share (T4) was not determined; the escalation depends on the recipient knowing the source vpath.",
  "No code was executed; every route above is from reading the pinned tree only."
 ]
}
  ```
- Published fix sites:   - copyparty/httpcli.py:7207 — T1 M4 (reason to dismiss: The page the emitter runs for is narrowed to the single file the filekey covers (httpcli.py:7173-7175), so serving that page looks scoped to that one file; P1 has no check at all here because add_dk is derived from the volume flag only (7207), which is exactly the advisory's flaw.)
  - copyparty/httpcli.py:7210-7215 — T1 M4 (reason to dismiss: The page the emitter runs for is narrowed to the single file the filekey covers (httpcli.py:7173-7175), so serving that page looks scoped to that one file; P1 has no check at all here because add_dk is derived from the volume flag only (7207), which is exactly the advisory's flaw.)
  - copyparty/httpcli.py:6953-6962 — T1 M4 (reason to dismiss: The page the emitter runs for is narrowed to the single file the filekey covers (httpcli.py:7173-7175), so serving that page looks scoped to that one file; P1 has no check at all here because add_dk is derived from the volume flag only (7207), which is exactly the advisory's flaw.)
  - copyparty/httpcli.py:6840-6848 — T1 M4 (reason to dismiss: The page the emitter runs for is narrowed to the single file the filekey covers (httpcli.py:7173-7175), so serving that page looks scoped to that one file; P1 has no check at all here because add_dk is derived from the volume flag only (7207), which is exactly the advisory's flaw.)
  - copyparty/httpcli.py:7173-7175 — T1 M4 (reason to dismiss: The page the emitter runs for is narrowed to the single file the filekey covers (httpcli.py:7173-7175), so serving that page looks scoped to that one file; P1 has no check at all here because add_dk is derived from the volume flag only (7207), which is exactly the advisory's flaw.)
  - copyparty/httpcli.py:7293-7303 — T5 M11 (reason to dismiss: Filekeys in a dirkey listing and the filekey inside og_thumb/og_raw are pre-existing, documented behaviours (README.md:3116, docs/changelog.md:2488) that the report does not ask to change, so they look out of scope.)
  - copyparty/httpcli.py:7304-7308 — T5 M11 (reason to dismiss: Filekeys in a dirkey listing and the filekey inside og_thumb/og_raw are pre-existing, documented behaviours (README.md:3116, docs/changelog.md:2488) that the report does not ask to change, so they look out of scope.)
  - copyparty/httpcli.py:7671-7684 — T5 M11 (reason to dismiss: Filekeys in a dirkey listing and the filekey inside og_thumb/og_raw are pre-existing, documented behaviours (README.md:3116, docs/changelog.md:2488) that the report does not ask to change, so they look out of scope.)
  - tests/test_dots.py:289-293 — T5 M11 (reason to dismiss: Filekeys in a dirkey listing and the filekey inside og_thumb/og_raw are pre-existing, documented behaviours (README.md:3116, docs/changelog.md:2488) that the report does not ask to change, so they look out of scope.)
  - tests/test_dots.py:311-313 — T5 M11 (reason to dismiss: Filekeys in a dirkey listing and the filekey inside og_thumb/og_raw are pre-existing, documented behaviours (README.md:3116, docs/changelog.md:2488) that the report does not ask to change, so they look out of scope.)
  - tests/test_dots.py:319-327 — T5 M11 (reason to dismiss: Filekeys in a dirkey listing and the filekey inside og_thumb/og_raw are pre-existing, documented behaviours (README.md:3116, docs/changelog.md:2488) that the report does not ask to change, so they look out of scope.)
- Uncovered routes to confirm (pattern B):   - copyparty/httpcli.py:6939-6940 — T2 M4 (reason to dismiss: index.html is documented as retrievable without a filekey (README.md:544, README.md:3066, docs/changelog.md:3839), so the key-exempt fetch reads as a sanctioned exception; the is_dir branch clears add_og before falling through (6934) while the direct index.html branch does not (6939-6940), which reads as deliberate scoping rather than a hole.)
  - copyparty/httpcli.py:6932-6934 — T2 M4 (reason to dismiss: index.html is documented as retrievable without a filekey (README.md:544, README.md:3066, docs/changelog.md:3839), so the key-exempt fetch reads as a sanctioned exception; the is_dir branch clears add_og before falling through (6934) while the direct index.html branch does not (6939-6940), which reads as deliberate scoping rather than a hole.)
  - copyparty/httpcli.py:6953-6962 — T2 M4 (reason to dismiss: index.html is documented as retrievable without a filekey (README.md:544, README.md:3066, docs/changelog.md:3839), so the key-exempt fetch reads as a sanctioned exception; the is_dir branch clears add_og before falling through (6934) while the direct index.html branch does not (6939-6940), which reads as deliberate scoping rather than a hole.)
  - copyparty/httpcli.py:7207-7215 — T2 M4 (reason to dismiss: index.html is documented as retrievable without a filekey (README.md:544, README.md:3066, docs/changelog.md:3839), so the key-exempt fetch reads as a sanctioned exception; the is_dir branch clears add_og before falling through (6934) while the direct index.html branch does not (6939-6940), which reads as deliberate scoping rather than a hole.)
  - copyparty/httpcli.py:6851-6853 — T3 M4 (reason to dismiss: README.md:3116 says filekeys should be enabled together with dirkeys, so a dks volume without fk reads as an ill-advised configuration the project need not support; and 'g' is documented as 'download files if you know the name' (README.md:542), so serving the one named file looks correct.)
  - copyparty/httpcli.py:6942-6950 — T3 M4 (reason to dismiss: README.md:3116 says filekeys should be enabled together with dirkeys, so a dks volume without fk reads as an ill-advised configuration the project need not support; and 'g' is documented as 'download files if you know the name' (README.md:542), so serving the one named file looks correct.)
  - copyparty/httpcli.py:6953-6962 — T3 M4 (reason to dismiss: README.md:3116 says filekeys should be enabled together with dirkeys, so a dks volume without fk reads as an ill-advised configuration the project need not support; and 'g' is documented as 'download files if you know the name' (README.md:542), so serving the one named file looks correct.)
  - copyparty/httpcli.py:7207-7215 — T3 M4 (reason to dismiss: README.md:3116 says filekeys should be enabled together with dirkeys, so a dks volume without fk reads as an ill-advised configuration the project need not support; and 'g' is documented as 'download files if you know the name' (README.md:542), so serving the one named file looks correct.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4, T5. Why: Three independent judgements, five route-level tests. (1) T1/T2/T3 are one missing check at one site (httpcli.py:7207-7215) but three entry conditions with three different dismissal arguments: a validated filekey (T1, the advisory), the documented index.html-without-a-filekey exemption for 'h' (T2), and a dks volume with no fk that the docs call ill-advised (T3). The published one-liner ('not use_filekey') closes only T1, so a solver who reproduces it fails the two keyless routes; the correct predicate is folder-level authorization ('can_read or use_dirkey'), which the ?tree= emitter already uses at httpcli.py:5874-5890. This is the deepseek-type core: protection absent plus a plausible reason to dismiss. (2) T4 is independent of that guard because a single-file share with 'r' sets can_read from the share grant while the emitter's key is for the source folder: the producer (authsrv.py:3181 copies the source volume's dk/dks/fk onto every share node) is the only place the two can be told apart, so it is a separate fix site and a separate judgement. (3) T5 is the mimo-type constraint: the fix must not over-harden - it has to keep filekeys in a dirkey listing, subfolder dirkeys under dks, and the filekey embedded in og_thumb/og_raw, all asserted in tests/test_dots.py:289-293,311-313,319-327. The stack is real but thin: 75% of it can be closed by one corrected predicate, so the hidden tests must include at least one keyless route and one share case for the stacking to bite. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): A rule that denies the opengraph view to callers without read contradicts the documented og/og_ua feature (README.md:1639-1645), whose whole purpose is link previews for shared file URLs. | A rule that refuses ?k=<filekey>&v refuses the documented combination of filekeys and opengraph (docs/changelog.md:2488) and the medialinks uploader link, which appends &v to a ?k= URL (httpcli.py:2775-2787). | A rule that requires read to receive any key breaks the dirkeys feature itself: dirkey recipients never have read (README.md:3106-3114, httpcli.py:4314-4317). | A rule that suppresses filekeys in a dirkey listing breaks hotlinking from a dirkey-shared folder (README.md:3116; tests/test_dots.py:289-293,311-313). | A rule that requires a key for index.html contradicts the documented 'h' permission semantics (README.md:544,3066, docs/changelog.md:3839). | A rule that drops dk from share nodes entirely breaks dks navigation for folder shares.. Conflicts the reader found: A guard written as 'only emit dk to callers with read' (the obvious reading of the advisory) suppresses the dks subfolder dirkeys at httpcli.py:7304-7308, which dirkey callers need and tests/test_dots.py:319-327 assert; the guard has to be 'can_read or use_dirkey'. | Refusing the ?v viewer (or dropping keys) for non-read callers breaks the filekey echo into og_thumb/og_raw (httpcli.py:7671-7684) and the filekey hotlinks a dirkey listing must keep (httpcli.py:7293-7303, tests/test_dots.py:311-313). | The cleanest T4 fix (stop copying dk/dks onto share nodes at authsrv.py:3181) also strips the dks subfolder navigation that a legitimate folder share relies on (httpcli.py:7304-7308), so the fix has to distinguish single-file shares (shr_files set, authsrv.py:3166) from folder shares. | Closing T2 by clearing add_og at httpcli.py:6940 changes the response for an 'h' user fetching index.html with ?v from the opengraph page to the raw file; the documented behaviour (README.md:544,3066) only promises index.html without a filekey, so the fix must keep returning index.html.

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

## Environment (`tasks/stk-copyparty-6317/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-copyparty-6317/instruction.md`)
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

## Tests (`tasks/stk-copyparty-6317/tests/`)
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
- **Wrong-fix patches** go in `build/stk-copyparty-6317/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-copyparty-6317/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-copyparty-6317/manifest.json`:**
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

**Also in `build/stk-copyparty-6317/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-copyparty-6317 --only static
python3 -I common/gate/gate.py stk-copyparty-6317 --only nop
python3 -I common/gate/gate.py stk-copyparty-6317 --only oracle
python3 -I common/gate/gate.py stk-copyparty-6317 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-copyparty-6317/`;
  - edit only `tasks/stk-copyparty-6317/`, `build/stk-copyparty-6317/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-6317.json`. Verify each trap on the
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

Stacked task slug: `stk-copyparty-6317`. Control task slug: `stk-copyparty-6317-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-6317.json`.
