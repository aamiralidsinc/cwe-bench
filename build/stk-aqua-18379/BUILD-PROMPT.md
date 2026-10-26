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

Project root: `/home/mara/cwe-bench`. Task: `stk-aqua-18379`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 18379; path traversal / symlink following leading to arbitrary file write (CW
- Pinned (vulnerable) commit: d6b9448fc421c58d83ae2fa372e61122f14620f5. Published fix: d5b02b220188de376a661b3aabfa912202a1a59a.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-18379",
 "pattern": "H4",
 "repo": "aquaproj/aqua",
 "pinned_commit": "d6b9448fc421c58d83ae2fa372e61122f14620f5",
 "protections": [
  "Entry-name containment: every path derived from an archive entry name (regular file, directory, or link destination) must stay inside the install destination before any filesystem effect; archives.go:26 builds dstPath with filepath.Join(h.dest, h.normalizePath(f.NameInArchive)) and archives.go:28/34/43/58 all use it with no containment check.",
  "Symlink-target containment: a symlink entry's target must resolve inside the install destination, with relative targets resolved against the link's own directory, before the link is created; archives.go:41-47 creates f.LinkTarget verbatim.",
  "Facade-wide containment: every extractor that Unarchiver.getUnarchiver dispatches to must apply the same containment, not only the tar/zip handler reached through archives.Extractor.Extract (unarchive.go:58-101, archives.go:104-113)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "pkg/unarchive/archives.go:26",
    "pkg/unarchive/archives.go:28",
    "pkg/unarchive/archives.go:58"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "pkg/unarchive/archives.go:26",
    "pkg/unarchive/archives.go:28",
    "pkg/unarchive/archives.go:33-39",
    "pkg/unarchive/archives.go:58",
    "pkg/unarchive/archives.go:109"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "pkg/unarchive/archives.go:41-47",
    "pkg/unarchive/archives.go:43"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "pkg/unarchive/archives.go:41",
    "pkg/unarchive/archives.go:42",
    "pkg/unarchive/archives.go:43",
    "pkg/unarchive/archives.go:48",
    "pkg/unarchive/archives.go:58"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "pkg/unarchive/archives.go:83-90",
    "pkg/unarchive/archives.go:26",
    "pkg/unarchive/archives.go:33-39"
   ],
   "reason_to_dismiss": "filepath.Join already normalises '..' and absolute names, so a guard on the raw f.NameInArchive (or on a plain string prefix) looks sufficient and needs no normalisation step.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "pkg/unarchive/archives.go:83-90",
    "pkg/unarchive/archives.go:86-87",
    "pkg/unarchive/archives.go:26",
    "pkg/unarchive/archives.go:28",
    "pkg/unarchive/archives.go:33-39",
    "pkg/unarchive/archives.go:109"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "pkg/unarchive/archives.go:41-49",
    "pkg/installpackage/check_file.go:181-189"
   ],
   "reason_to_dismiss": "packages legitimately ship relative and dangling symlinks (libfoo.so.1 -> libfoo.so.1.2.3, with the target appearing later in the archive), so the symlink branch must keep creating them.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "easy",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "pkg/unarchive/archives.go:41-49",
    "pkg/unarchive/archives.go:43",
    "pkg/installpackage/check_file.go:181",
    "pkg/installpackage/check_file.go:182",
    "pkg/installpackage/check_file.go:187"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "pkg/unarchive/dmg.go:56",
    "pkg/osfile/copy.go:12-16"
   ],
   "reason_to_dismiss": "macOS-only route that mounts the image with hdiutil and copies the mounted volume with an external copy helper, not archive entries handled by archives.Extractor; the published fix stays in archives.go.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "pkg/unarchive/dmg.go:41",
    "pkg/unarchive/dmg.go:56",
    "pkg/osfile/copy.go:12-16",
    "pkg/osfile/copy.go:19-44",
    "pkg/osfile/copy.go:53",
    "pkg/unarchive/unarchive.go:66-72",
    "pkg/unarchive/unarchive.go:80-86",
    "pkg/controller/wire_gen.go:139",
    "pkg/controller/wire_gen.go:157"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "pkg/unarchive/pkg.go:32"
   ],
   "reason_to_dismiss": "macOS-only and delegated to pkgutil --expand-full: the expanded payload is not an archive entry and the published fix targeted the archives handler.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "pkg/unarchive/pkg.go:23",
    "pkg/unarchive/pkg.go:32",
    "pkg/unarchive/unarchive.go:73-79",
    "pkg/unarchive/unarchive.go:87-92",
    "pkg/asset/format.go:41-42",
    "tests/unarchive/aqua.yaml:20-22"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "pkg/unarchive/archives.go:41-48"
   ],
   "reason_to_dismiss": "hardlink entries are silently dropped today (archives.go:48) and the advisory is about symlink following, so there is nothing to guard.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "pkg/unarchive/archives.go:41",
    "pkg/unarchive/archives.go:42-47",
    "pkg/unarchive/archives.go:48"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "pkg/unarchive/archives.go:129",
    "pkg/unarchive/unarchive.go:59"
   ],
   "reason_to_dismiss": "the decompressor's output name is already reduced by filepath.Base in getUnarchiver (unarchive.go:59), so the join at archives.go:129 cannot escape dest.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "pkg/unarchive/archives.go:120-138",
    "pkg/unarchive/archives.go:129",
    "pkg/unarchive/unarchive.go:59",
    "pkg/unarchive/unarchive.go:95-100"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T3"
  ],
  [
   "T2",
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
  ],
  [
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "archives.go:28 creates parent directories (and archives.go:34 the entry directory) outside dest before any check, so a fix placed only at the write (archives.go:58) leaves the directory side effect observable only once the file write is blocked.",
   "pkg/installpackage/check_file.go:130 stat and :143 chmod follow a link planted under the package dir, and pkg/installpackage/copy.go:14 writes to is.copyDir; these are reachable only while T2 leaves the planting step in place.",
   "T7's hardlink branch only exists once os.Link support is added beside the symlink branch; today archives.go:48 drops every LinkTarget entry that is not a symlink."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T2",
   "b": "T4",
   "what": "A withinDest rule on symlink targets must still create relative and dangling in-dest links; resolving targets with filepath.EvalSymlinks/os.Stat (or rejecting every symlink entry) satisfies T2 while breaking the packages T4 protects (archives.go:43, check_file.go:182-187 builds and creates relative links)."
  }
 ],
 "fairness_risks": [
  "Packages legitimately ship relative symlinks, including dangling ones whose target is created later in the same tar (libfoo.so.1 -> libfoo.so.1.2.3); any rule that requires the target to already exist refuses a legitimate archive.",
  "An absolute symlink whose target is inside the install directory must still be accepted; a rule banning all absolute targets is over-broad.",
  "Archives written on Windows use backslashes as separators and normalizePath deliberately rewrites them (archives.go:83-90); refusing backslash names refuses legitimate archives.",
  "Entry names that merely contain '..' as a substring (foo..tar.gz), or that start with './', must still extract; a substring ban is over-broad while the correct rule is lexical containment of the joined path.",
  "Directory entries (archives.go:33-39) and their creation must keep working; a rule applied only to regular-file writes leaves the MkdirAll side effect at archives.go:28 open.",
  "aqua cp deliberately writes outside the install tree (pkg/controller/cp/copy.go:12, pkg/installpackage/copy.go:14); a blanket no-write-outside-dest rule must not be applied to that path."
 ],
 "effort_minutes": 75,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T5",
   "T6",
   "T4"
  ],
  "why": "T1 and T2 are two guards in the same function that are each individually bypassable: with only the entry-name containment, an archive plants link -> /etc and a later entry named link/passwd passes the lexical check and is written through the link at archives.go:58; with only the symlink-target containment, a plain ../../x entry still escapes at archives.go:26/58. So the solver must make two independent judgements, and the second is one a report about path traversal does not force. T5 and T6 are the other two extractors the same facade dispatches to (unarchive.go:66-92), each protected by a strong and different dismissal - a mounted volume copied with an external helper versus a payload expanded by pkgutil - and each needs its own guard because osfile.Copy (osfile/copy.go:12-16) and pkgutil (pkg.go:32) never see the handler. T4 is the coupled must-keep-working value at the very site of T2: relative and dangling in-dest symlinks are a normal package shape, so the natural over-broad fix (reject symlink entries, or resolve targets with EvalSymlinks) fails a compatibility test that MiMo-style solvers typically trip on. That gives at least one deepseek-type (T5/T6) and one mimo-type (T4) with three different dismissal arguments. It beats a T1+T3 design, which one correctly placed containment check closes, and a T5+T6 design, which has no in-file depth and repeats the same macOS-only dismissal twice. T7 and T8 are optional sixth/seventh injection-room traps if more depth is wanted (hardlink branch; a decompress writer that depends on the base() at unarchive.go:59)."
 },
 "unverified": [
  "The advisory text for GHSA-MF5C-HW34-4HPP / CVE-2026-55569 was not available offline; if it names only entry-name path traversal and not symlink following, T2 becomes a deepseek-type hard trap instead of easy.",
  "fix.diff was not present in the worktree and the fix commit d5b02b22 was not checked out, so the screener's fix-site lines (archives.go:33, archives.go:42, fix.diff:33-35, 60-94) are taken on trust; everything recorded here is read from the pinned pre-fix tree.",
  "otiai10/copy v1.14.1 (go.mod:18) behaviour for a symlink inside the mounted image was not read (module cache is outside the read scope), so the DMG route is recorded as 'no containment check exists' rather than as a confirmed write outside the install directory.",
  "Whether pkgutil --expand-full sanitises payload paths itself was not verified; only aqua's own absence of a check at pkg.go:32 is a fact from the pinned code.",
  "go build ./... and go test ./... were not run (no shell in this session); pkg/unarchive/unarchive_test.go also fetches tarballs from github.com (unarchive_test.go:93, :100), so it is not fully offline.",
  "Git history was not inspectable, so no earlier fix (A) could be identified for the H3 questions; a_fix_leaves_b_open and b_in_code_a_wrote are left null rather than guessed.",
  "pkg/installpackage/go_install.go:27-35 and pkg/installpackage/cargo.go:50-52 write into the install dir via external tools with no containment check; not assessed because they do not process archive entries.",
  "repo_mb was not measured."
 ]
}
  ```
- Published fix sites:   - pkg/unarchive/archives.go:26 — T1 M4 (reason to dismiss: none)
  - pkg/unarchive/archives.go:28 — T1 M4 (reason to dismiss: none)
  - pkg/unarchive/archives.go:58 — T1 M4 (reason to dismiss: none)
  - pkg/unarchive/archives.go:41-47 — T2 M4 (reason to dismiss: none)
  - pkg/unarchive/archives.go:43 — T2 M4 (reason to dismiss: none)
  - pkg/unarchive/archives.go:83-90 — T3 M8 (reason to dismiss: filepath.Join already normalises '..' and absolute names, so a guard on the raw f.NameInArchive (or on a plain string prefix) looks sufficient and needs no normalisation step.)
  - pkg/unarchive/archives.go:26 — T3 M8 (reason to dismiss: filepath.Join already normalises '..' and absolute names, so a guard on the raw f.NameInArchive (or on a plain string prefix) looks sufficient and needs no normalisation step.)
  - pkg/unarchive/archives.go:33-39 — T3 M8 (reason to dismiss: filepath.Join already normalises '..' and absolute names, so a guard on the raw f.NameInArchive (or on a plain string prefix) looks sufficient and needs no normalisation step.)
  - pkg/unarchive/archives.go:41-49 — T4 M11 (reason to dismiss: packages legitimately ship relative and dangling symlinks (libfoo.so.1 -> libfoo.so.1.2.3, with the target appearing later in the archive), so the symlink branch must keep creating them.)
  - pkg/installpackage/check_file.go:181-189 — T4 M11 (reason to dismiss: packages legitimately ship relative and dangling symlinks (libfoo.so.1 -> libfoo.so.1.2.3, with the target appearing later in the archive), so the symlink branch must keep creating them.)
- Uncovered routes to confirm (pattern B):   - pkg/unarchive/dmg.go:56 — T5 M2 (reason to dismiss: macOS-only route that mounts the image with hdiutil and copies the mounted volume with an external copy helper, not archive entries handled by archives.Extractor; the published fix stays in archives.go.)
  - pkg/osfile/copy.go:12-16 — T5 M2 (reason to dismiss: macOS-only route that mounts the image with hdiutil and copies the mounted volume with an external copy helper, not archive entries handled by archives.Extractor; the published fix stays in archives.go.)
  - pkg/unarchive/pkg.go:32 — T6 M4 (reason to dismiss: macOS-only and delegated to pkgutil --expand-full: the expanded payload is not an archive entry and the published fix targeted the archives handler.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T5, T6, T4. Why: T1 and T2 are two guards in the same function that are each individually bypassable: with only the entry-name containment, an archive plants link -> /etc and a later entry named link/passwd passes the lexical check and is written through the link at archives.go:58; with only the symlink-target containment, a plain ../../x entry still escapes at archives.go:26/58. So the solver must make two independent judgements, and the second is one a report about path traversal does not force. T5 and T6 are the other two extractors the same facade dispatches to (unarchive.go:66-92), each protected by a strong and different dismissal - a mounted volume copied with an external helper versus a payload expanded by pkgutil - and each needs its own guard because osfile.Copy (osfile/copy.go:12-16) and pkgutil (pkg.go:32) never see the handler. T4 is the coupled must-keep-working value at the very site of T2: relative and dangling in-dest symlinks are a normal package shape, so the natural over-broad fix (reject symlink entries, or resolve targets with EvalSymlinks) fails a compatibility test that MiMo-style solvers typically trip on. That gives at least one deepseek-type (T5/T6) and one mimo-type (T4) with three different dismissal arguments. It beats a T1+T3 design, which one correctly placed containment check closes, and a T5+T6 design, which has no in-file depth and repeats the same macOS-only dismissal twice. T7 and T8 are optional sixth/seventh injection-room traps if more depth is wanted (hardlink branch; a decompress writer that depends on the base() at unarchive.go:59). Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Packages legitimately ship relative symlinks, including dangling ones whose target is created later in the same tar (libfoo.so.1 -> libfoo.so.1.2.3); any rule that requires the target to already exist refuses a legitimate archive. | An absolute symlink whose target is inside the install directory must still be accepted; a rule banning all absolute targets is over-broad. | Archives written on Windows use backslashes as separators and normalizePath deliberately rewrites them (archives.go:83-90); refusing backslash names refuses legitimate archives. | Entry names that merely contain '..' as a substring (foo..tar.gz), or that start with './', must still extract; a substring ban is over-broad while the correct rule is lexical containment of the joined path. | Directory entries (archives.go:33-39) and their creation must keep working; a rule applied only to regular-file writes leaves the MkdirAll side effect at archives.go:28 open. | aqua cp deliberately writes outside the install tree (pkg/controller/cp/copy.go:12, pkg/installpackage/copy.go:14); a blanket no-write-outside-dest rule must not be applied to that path.. Conflicts the reader found: A withinDest rule on symlink targets must still create relative and dangling in-dest links; resolving targets with filepath.EvalSymlinks/os.Stat (or rejecting every symlink entry) satisfies T2 while breaking the packages T4 protects (archives.go:43, check_file.go:182-187 builds and creates relative links).

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

## Environment (`tasks/stk-aqua-18379/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-aqua-18379/instruction.md`)
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

## Tests (`tasks/stk-aqua-18379/tests/`)
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
- **Wrong-fix patches** go in `build/stk-aqua-18379/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-aqua-18379/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-aqua-18379/manifest.json`:**
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

**Also in `build/stk-aqua-18379/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-aqua-18379 --only static
python3 -I common/gate/gate.py stk-aqua-18379 --only nop
python3 -I common/gate/gate.py stk-aqua-18379 --only oracle
python3 -I common/gate/gate.py stk-aqua-18379 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-aqua-18379/`;
  - edit only `tasks/stk-aqua-18379/`, `build/stk-aqua-18379/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-18379.json`. Verify each trap on the
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

Stacked task slug: `stk-aqua-18379`. Control task slug: `stk-aqua-18379-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-18379.json`.
