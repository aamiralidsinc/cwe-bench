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

Project root: `/home/mara/cwe-bench`. Task: `stk-virtualenv-2350`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 2350; download of code without integrity check (CWE-494), supply-chain/artif
- Pinned (vulnerable) commit: d721ff140ce4afdc2a9b76751e4584e25d9fbea6. Published fix: a01ed3e2f239d6ab1fce62c5c7664ccf268fff6d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-2350",
 "pattern": "H4",
 "repo": "pypa/virtualenv",
 "pinned_commit": "d721ff140ce4afdc2a9b76751e4584e25d9fbea6",
 "protections": [
  "A seed wheel fetched by `pip download` must be authenticated against the authoritative PyPI release record for the distribution/version it claims before it is returned to a seeder; today download_wheel decides nothing and returns whatever pip left in the folder (src/virtualenv/seed/wheels/acquire.py:140-142).",
  "A wheel replayed from the persisted app-data update log must be the wheel that was authenticated, not merely the file currently at <app_data>/wheel/house/<stored filename> (src/virtualenv/seed/wheels/periodic_update.py:53-56, :68-72).",
  "The install image that seeding uses must be derived from authenticated wheel bytes; today the image is keyed only on installer class + wheel stem and is never rebuilt once present (src/virtualenv/seed/embed/via_app_data/via_app_data.py:67-70, src/virtualenv/seed/embed/via_app_data/pip_install/base.py:219-220).",
  "Wheels shipped inside the package are authenticated on load against the compiled-in sha256 table (src/virtualenv/seed/wheels/embed/__init__.py:96-108) - the one place in this tree where this protection already exists, and it covers only BUNDLE_FOLDER."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/virtualenv/seed/wheels/acquire.py:86-112",
    "src/virtualenv/seed/wheels/acquire.py:140-142"
   ],
   "reason_to_dismiss": "pip download already fetched the file over HTTPS from the configured index and exited 0, so the fetch itself is the trust boundary and the wheel filename pip prints is the release identity; there is nothing for virtualenv to check a second time.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "src/virtualenv/seed/wheels/acquire.py:113-114 (only the distribution name and version spec are checked before the command line is built)",
    "src/virtualenv/seed/wheels/acquire.py:137-139 (the sole success criterion is pip's exit code)",
    "src/virtualenv/seed/wheels/acquire.py:140-142 (the wheel found by _find_downloaded_wheel is logged and returned unexamined)",
    "src/virtualenv/seed/wheels/acquire.py:80-81 (the returned wheel is recorded in the update log for later replay)"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "src/virtualenv/seed/wheels/acquire.py:145-154",
    "src/virtualenv/seed/wheels/acquire.py:157-172"
   ],
   "reason_to_dismiss": "When pip reports 'File was already downloaded <path>' it is the same file pip downloaded into this folder on an earlier run, and the no-marker fallback only picks a wheel that is already sitting in virtualenv's own app-data folder, so both are the tool's own cached artefacts.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "src/virtualenv/seed/wheels/acquire.py:148-152 ('Saved ' and 'File was already downloaded ' are accepted equally; the second names a file that never crossed the index in this run)",
    "src/virtualenv/seed/wheels/acquire.py:153-154 (no marker at all falls back to the house)",
    "src/virtualenv/seed/wheels/acquire.py:157-172 (find_compatible_in_house returns any compatible wheel already present in to_folder, selected only by distribution/version/python tag)",
    "src/virtualenv/seed/wheels/acquire.py:77 (to_folder is app_data.house, the shared persistent wheel folder)"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "src/virtualenv/seed/wheels/acquire.py:145-154",
    "src/virtualenv/seed/wheels/util.py:16-30",
    "src/virtualenv/seed/wheels/acquire.py:115"
   ],
   "reason_to_dismiss": "The wheel's distribution and version are read from the filename pip printed, which is exactly the string PyPI uses for a release file, so an exact name comparison against the release list is sufficient.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/virtualenv/seed/wheels/acquire.py:148-152 (three selection shapes: 'Saved', 'already downloaded', no marker; a check hung on one of them misses the others)",
    "src/virtualenv/seed/wheels/acquire.py:153-154 (the fallback returns a wheel nobody named)",
    "src/virtualenv/seed/wheels/util.py:16 (self._parts = path.stem.split('-'), then distribution=parts[0] at :26 and version=parts[1] at :30 - a raw hyphen split, not a PEP 503 normalisation)",
    "src/virtualenv/seed/wheels/acquire.py:115 (the request is built from the caller's distribution string, which is not necessarily the filename's spelling)",
    "src/virtualenv/seed/wheels/util.py:20 (a wheel only parses when the stem has at least 5 hyphen-separated parts)"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M6",
   "origin": "uncovered_upstream",
   "locations": [
    "src/virtualenv/seed/wheels/periodic_update.py:53-56",
    "src/virtualenv/seed/wheels/periodic_update.py:58-72",
    "src/virtualenv/seed/wheels/periodic_update.py:94-104",
    "src/virtualenv/app_data/via_disk_folder.py:104-105"
   ],
   "reason_to_dismiss": "The wheel in the house was already hashed when download_wheel fetched it; the update log only stores metadata and never holds bytes, so re-checking a file replayed from the log is redundant work on every environment creation.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/virtualenv/seed/wheels/periodic_update.py:53-56 (_update_wheel constructs Wheel(app_data.house / ver.filename) from the stored filename; the file is never opened)",
    "src/virtualenv/seed/wheels/periodic_update.py:64-72 (the selection returns that Wheel for 'periodic'/'manual' log entries)",
    "src/virtualenv/seed/wheels/periodic_update.py:94-104 (add_wheel_to_update_log records wheel.name and the source only - no digest)",
    "src/virtualenv/seed/wheels/periodic_update.py:134-140 (NewVersion.to_dict carries filename/release_date/found_date/source, so the producer has no field a verifier could compare against)",
    "src/virtualenv/app_data/via_disk_folder.py:104-105, :107-111 (the log and the house are both plain app-data files)",
    "tests/unit/seed/wheels/test_bundle.py:63-66 (an existing test expects a Wheel to be returned for a log entry whose file need not exist in the house)"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/virtualenv/seed/wheels/bundle.py:54-59",
    "src/virtualenv/seed/wheels/bundle.py:35-38",
    "src/virtualenv/seed/embed/base_embed.py:109-116"
   ],
   "reason_to_dismiss": "The directory was named by the user on the command line (--extra-search-dir), so its wheels are the user's own trust decision, in exactly the way --find-links is; nothing virtualenv could compare them to exists for a private build.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/virtualenv/seed/wheels/bundle.py:54-59 (from_dir returns the first wheel discover_wheels finds in each directory, with no digest or provenance check)",
    "src/virtualenv/seed/wheels/bundle.py:35-38 (a search-dir wheel wins over the bundled wheel whenever its version_tuple is greater)",
    "src/virtualenv/seed/embed/base_embed.py:109-116 (--extra-search-dir is a supported, repeatable CLI option)",
    "src/virtualenv/seed/wheels/util.py:86-97 (selection is by distribution/version/python tag only)"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M10",
   "origin": "injection_room",
   "locations": [
    "src/virtualenv/seed/embed/via_app_data/via_app_data.py:64-73",
    "src/virtualenv/seed/embed/via_app_data/via_app_data.py:156-160",
    "src/virtualenv/seed/embed/via_app_data/pip_install/base.py:219-220"
   ],
   "reason_to_dismiss": "The image was built from a wheel that had already passed the download check, and rebuilding it because the wheel file changed would throw away the whole point of the app-data cache.",
   "distance": {
    "files": 3,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/virtualenv/seed/embed/via_app_data/via_app_data.py:67 (key = Path(installer_class.__name__) / wheel.path.stem - the cache key names the wheel, not its bytes)",
    "src/virtualenv/seed/embed/via_app_data/via_app_data.py:68-71 (the installer reads the wheel only when the image is built)",
    "src/virtualenv/seed/embed/via_app_data/via_app_data.py:156-160 (build_image is skipped whenever has_image() is true)",
    "src/virtualenv/seed/embed/via_app_data/pip_install/base.py:219-220 (has_image() is 'the directory exists and is non-empty')",
    "src/virtualenv/app_data/via_disk_folder.py:113-114 (the image path is wheel/<py>/image/1/<name>, persistent across runs)"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "src/virtualenv/seed/embed/pip_invoke.py:44-78",
    "src/virtualenv/seed/embed/pip_invoke.py:57-58"
   ],
   "reason_to_dismiss": "The requirement is version-pinned and the matching wheel is already in the --find-links folder, so pip resolves the local file and never consults an index; --download is precisely the user asking pip to use the network.",
   "distance": {
    "files": 1,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "src/virtualenv/seed/embed/pip_invoke.py:57-58 (--no-index is added only when downloads are disabled)",
    "src/virtualenv/seed/embed/pip_invoke.py:60-75 (the wheel is located with download=False, i.e. from bundle/search dirs only, then the requirement is pinned to that version)",
    "src/virtualenv/seed/embed/pip_invoke.py:76-77 (the folder is passed as --find-links, so pip may still choose an index candidate for the same version)",
    "tests/unit/seed/embed/test_pip_invoke.py:45 (an existing test asserts '--no-index' is NOT in the command when --download is passed)"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "src/virtualenv/seed/wheels/bundle.py:42-51",
    "src/virtualenv/app_data/base.py:83-97",
    "src/virtualenv/app_data/via_disk_folder.py:78-85"
   ],
   "reason_to_dismiss": "The copy in the house is just the bundled wheel extracted so zipapp installs can reach it, and the bundled file itself is sha256-verified before extraction, so the copy inherits that verification.",
   "distance": {
    "files": 3,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/virtualenv/seed/wheels/bundle.py:47 (load_embed_wheel wraps the verified bundled path in app_data.ensure_extracted(wheel.path, lambda: app_data.house))",
    "src/virtualenv/app_data/base.py:93-97 (ensure_extracted only copies when IS_ZIPAPP; otherwise the bundled path is used directly)",
    "src/virtualenv/app_data/via_disk_folder.py:80-85 (the destination under the house is reused whenever it already exists; the existing bytes are never hashed)",
    "src/virtualenv/app_data/via_disk_folder.py:107-111 (house is the same folder download_wheel writes into)"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "src/virtualenv/seed/wheels/acquire.py:134",
    "src/virtualenv/seed/wheels/acquire.py:175-192",
    "src/virtualenv/seed/seeder.py:27"
   ],
   "reason_to_dismiss": "A private mirror or an offline wheelhouse legitimately serves a rebuilt wheel under the same distribution/version/filename PyPI also uses, so 'the digest must equal PyPI's' cannot be enforced unconditionally; the only safe reading is that an unverifiable wheel is let through, which in practice means not adding an enforcing check at all.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/virtualenv/seed/wheels/acquire.py:134 (the caller's env is passed straight into pip_wheel_env_run, so PIP_INDEX_URL / PIP_EXTRA_INDEX_URL / PIP_INDEX redirect the download)",
    "src/virtualenv/seed/wheels/acquire.py:175-192 (pip_wheel_env_run copies the caller env and only adds PIP_USE_WHEEL/PIP_USER/PIP_NO_INPUT/PYTHONIOENCODING/PYTHONPATH)",
    "src/virtualenv/seed/seeder.py:27 (self.env = options.env, i.e. the process environment by default)",
    "src/virtualenv/run/__init__.py:91 (env defaults to os.environ)",
    "src/virtualenv/seed/wheels/periodic_update.py:388-405 (the PyPI metadata lookup returns None on any failure, the shape a 'not verifiable' outcome must reuse)"
   ]
  },
  {
   "id": "T10",
   "mechanism": "M7",
   "origin": "injection_room",
   "locations": [
    "src/virtualenv/seed/wheels/acquire.py:117-132",
    "src/virtualenv/seed/wheels/acquire.py:77",
    "src/virtualenv/seed/wheels/periodic_update.py:291"
   ],
   "reason_to_dismiss": "Raising from a failed check is enough - the caller sees the error and will not seed that wheel; a validation failure should not start deleting files out of a shared cache that other runs and the verified embed path also write to.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/virtualenv/seed/wheels/acquire.py:129-132 (pip is told to write directly into to_folder with -d, so the bytes land on disk before anything can inspect them)",
    "src/virtualenv/seed/wheels/acquire.py:77 (to_folder is app_data.house)",
    "src/virtualenv/seed/wheels/periodic_update.py:291 (the periodic updater uses the same app_data.house as wheelhouse)",
    "src/virtualenv/seed/wheels/periodic_update.py:318-325 (do_update calls download_wheel with to_folder=wheelhouse)",
    "src/virtualenv/seed/wheels/acquire.py:157-172 (a rejected-but-left-behind wheel in the house is exactly what find_compatible_in_house later returns)"
   ]
  },
  {
   "id": "T11",
   "mechanism": "M8",
   "origin": "published_fix_far_site",
   "locations": [
    "src/virtualenv/seed/wheels/periodic_update.py:379-385",
    "src/virtualenv/seed/wheels/periodic_update.py:388-405"
   ],
   "reason_to_dismiss": "The lookup cache is only a performance optimisation, and a failed lookup already has to mean 'not verifiable, let the wheel through'; caching that failure merely avoids retrying a network call that just failed.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "mimo",
   "evidence": [
    "src/virtualenv/seed/wheels/periodic_update.py:382-385 (_PYPI_CACHE stores the result even when it is None, process-wide)",
    "src/virtualenv/seed/wheels/periodic_update.py:388-396 (any exception is swallowed and content stays None)",
    "src/virtualenv/seed/wheels/periodic_update.py:399-405 (URLError also yields None)",
    "tests/unit/seed/wheels/test_periodic_update.py:36-40 (the test suite has to clear _PYPI_CACHE between tests, confirming the cached failure is sticky)"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T3",
   "T9",
   "T10"
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
  ],
  [
   "T8"
  ],
  [
   "T11"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": true,
  "masking": [
   "A wheel rejected by a new download check is still left in app_data.house (acquire.py:129-132), so the replay route (T4) and the image route (T6) only become observable as separate bugs once the download check exists and refuses a file; before that the poison is simply used everywhere and nothing looks wrong.",
   "The wheel image (T6) hides the wheel from every later check: once wheel/<py>/image/1/<installer>/<stem> exists, the wheel file is never opened again (via_app_data.py:156-160, pip_install/base.py:219-220), so a fix placed only on acquisition never runs on the seeding path that actually copies files into the venv.",
   "T2's house fallback is masked by T1's success: as long as download_wheel returns whatever pip wrote, nobody notices that the fallback branch (acquire.py:157-172) can return a file pip never downloaded; it becomes a distinct hole the moment T1's check is added only on the 'Saved ' branch.",
   "T8 can only shadow the verified bundle when IS_ZIPAPP is true (app_data/base.py:93-97); in a normal source checkout the bundled path is yielded directly, so the route is invisible until the zipapp layout is considered."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T9",
   "what": "The natural fix for T1 (reject any wheel whose sha256 does not equal PyPI's) rejects the private-mirror, offline and private-distribution cases that acquire.py:134 and acquire.py:175-192 make supported configurations; the guard has to have a third 'not verifiable -> allow' outcome, so the same site carries both the hidden requirement and the must-keep-working value."
  },
  {
   "a": "T4",
   "b": "T1",
   "what": "Checking a replayed wheel against PyPI needs a digest the producer never stored (periodic_update.py:94-104, :134-140), while the existing contract allows a log entry whose file is absent from the house (tests/unit/seed/wheels/test_bundle.py:63-66); recording a digest at download time and re-verifying when the file exists are two separate changes that must agree."
  },
  {
   "a": "T6",
   "b": "T1",
   "what": "Keying the image on wheel bytes (or invalidating it after a rejected download) forces rebuilds of wheel/<py>/image/1/... on every content change, while tests/unit/seed/embed/test_bootstrap_link_via_app_data.py:105-110 asserts a second create reuses the cache and produces identical site-packages; the fix has to invalidate on mismatch without breaking ordinary reuse."
  },
  {
   "a": "T5",
   "b": "T9",
   "what": "Verifying --extra-search-dir wheels against PyPI is only safe under the same 'not on PyPI -> allow' rule; otherwise a private wheel placed there (bundle.py:54-59) fails to seed, which is the documented purpose of the option (base_embed.py:109-116)."
  }
 ],
 "fairness_risks": [
  "Custom/private index: acquire.py:134 forwards the caller's environment into the pip subprocess, so PIP_INDEX_URL / PIP_EXTRA_INDEX_URL / PIP_INDEX legitimately change where the wheel comes from; a rule that requires PyPI's digest rejects a wheel served by exactly the configured source.",
  "Offline or proxied installs: the only metadata source used in this tree fails closed to None (periodic_update.py:388-405); treating 'no metadata' as a mismatch breaks air-gapped environment creation, so 'unverifiable' must mean allow.",
  "Private/local distributions and wheels whose filename is not a PyPI release file must be let through (the published fix's own branches, per the screener's O6 shapes); refusing them breaks private packaging.",
  "--extra-search-dir is a documented user trust boundary (base_embed.py:109-116); enforcing PyPI digests there contradicts the contract unless the unverifiable case is allowed.",
  "PipInvoke's --download path deliberately leaves the index enabled; tests/unit/seed/embed/test_pip_invoke.py:45 asserts '--no-index' is absent, so a fix that adds it to close T7 breaks a documented flag and its regression test.",
  "The update log is deliberately metadata-only: tests/unit/seed/wheels/test_bundle.py:63-66 expects a Wheel for a log entry whose file need not exist in the house, so a replay check must tolerate a missing file rather than turning the cache into an error.",
  "Wheel-image reuse is a tested behaviour (tests/unit/seed/embed/test_bootstrap_link_via_app_data.py:105-110); any content-keyed cache must still produce the same site-packages on the second create.",
  "A pip.conf / PIP_CONFIG_FILE index redirect is invisible to an env-based gate (the published fix's documented limitation per the screener); a gate reading only the three env vars leaves a supported configuration unverified, and a gate that also reads config files changes behaviour for users who never set the env vars.",
  "Refused input shape that legitimate use needs: a wheel whose filename differs from PyPI's canonical filename for the same release (build tag, local version suffix) must not be treated as a mismatch when its bytes are the published artefact."
 ],
 "effort_minutes": 180,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T4",
   "T5",
   "T6"
  ],
  "why": "Four independent judgements in four different files/packages, each with a different reason a solver can honestly stand down: T1 'pip already fetched it over HTTPS and exited 0'; T4 'it was hashed when it was downloaded, the log is only metadata'; T5 'the user named that directory'; T6 'the image was built from a wheel that had already passed the check'. T1's group is where the DeepSeek-shaped trap and the MiMo-shaped trap sit together: the protection is simply absent (T1) while the same site carries the coupled must-keep-working value that private mirrors/offline/private names are legitimate (T9), so a pass/fail check either misses the hole or over-hardens and breaks supported configurations; T4 is the producer-off-the-check's-path trap (the log turns a stored filename into a Wheel without reading it) and rewards the solver who extends the log schema or re-verifies on replay; T5 is a second absent-protection route with a strong dismissal; T6 is a proxy-object trap (the image cache decides on the stem, not the bytes) that no acquisition-time check reaches. Every one is testable offline with mocked Popen/urlopen and a local wheel file, and each needs a different mechanism to fix (verify returned bytes with a three-way outcome plus cleanup, extend the producer/replay, verify only when the name is a PyPI release, key or invalidate the image). Fixing only the sink the report names leaves three of the four open, which is exactly the stacking this checkout supports. Alternatives left out: T7 (PipInvoke index resolution) is a real second implementation but its 'correct' behaviour contradicts the --download flag asserted at test_pip_invoke.py:45; T8 is zipapp-only (app_data/base.py:93-97) so it is not reachable in an unpacked checkout; T11 (cached None fails open) is a property of whichever lookup the fix chooses rather than a site of its own; T2/T3/T9/T10 belong to T1's group because one correctly written guard at download_wheel closes or must honour them."
 },
 "unverified": [
  "The published fix commit a01ed3e2f239d6ab1fce62c5c7664ccf268fff6d and its diff are not present in this worktree; every fix.diff line number attributed in this record comes from the screener, not from code I read, and the fix's exact behaviour (verify_wheel_digest, the index gate, the 'let through' branches) is taken on trust.",
  "No git history is reachable in this restricted session (Bash is disabled and .git lives outside the allowed roots), so whether src/virtualenv/seed/wheels/acquire.py:22-48/_check_distribution and the embed sha256 table were separate earlier fixes, and their order relative to this advisory, is inferred from their shape and tests only.",
  "No code was executed. Pip's 'File was already downloaded' output, pip's preference between an index candidate and a --find-links candidate at equal version, and PyPI's handling of non-normalised distribution names in the JSON route are read from the code plus standard pip/PyPI behaviour, not observed.",
  "Repository size in MB, buildability and the test suite could not be measured (no shell); the screener's repo_mb is null.",
  "Whether the hidden tests treat the replay (T4), --extra-search-dir (T5) or image-cache (T6) routes as required fixes is unknown; the design assumes the task author adds behavioural tests for them, and each is written to be mockable offline.",
  "The advisory text (GHSA-94P9-XGH2-XP45 / CVE-2026-102930 / PYSEC-2026-4011) was not available; the threat model used here (a wheel that is not the PyPI release its filename names) is the screener's trust_decision summary, not a document I read.",
  "The screener's kinds M3 and M5 did not resolve to a distinct missing protection in the pinned code: M3 is a statement about where the helper must live (the PyPI loader is private to src/virtualenv/seed/wheels/periodic_update.py:382-405, one module from the sink), and M5 is realised as the stored update log (T4) and the inherited process environment (T9)."
 ]
}
  ```
- Published fix sites:   - src/virtualenv/seed/wheels/acquire.py:86-112 — T1 M4 (reason to dismiss: pip download already fetched the file over HTTPS from the configured index and exited 0, so the fetch itself is the trust boundary and the wheel filename pip prints is the release identity; there is nothing for virtualenv to check a second time.)
  - src/virtualenv/seed/wheels/acquire.py:140-142 — T1 M4 (reason to dismiss: pip download already fetched the file over HTTPS from the configured index and exited 0, so the fetch itself is the trust boundary and the wheel filename pip prints is the release identity; there is nothing for virtualenv to check a second time.)
  - src/virtualenv/seed/wheels/acquire.py:145-154 — T2 M1 (reason to dismiss: When pip reports 'File was already downloaded <path>' it is the same file pip downloaded into this folder on an earlier run, and the no-marker fallback only picks a wheel that is already sitting in virtualenv's own app-data folder, so both are the tool's own cached artefacts.)
  - src/virtualenv/seed/wheels/acquire.py:157-172 — T2 M1 (reason to dismiss: When pip reports 'File was already downloaded <path>' it is the same file pip downloaded into this folder on an earlier run, and the no-marker fallback only picks a wheel that is already sitting in virtualenv's own app-data folder, so both are the tool's own cached artefacts.)
  - src/virtualenv/seed/wheels/acquire.py:145-154 — T3 M8 (reason to dismiss: The wheel's distribution and version are read from the filename pip printed, which is exactly the string PyPI uses for a release file, so an exact name comparison against the release list is sufficient.)
  - src/virtualenv/seed/wheels/util.py:16-30 — T3 M8 (reason to dismiss: The wheel's distribution and version are read from the filename pip printed, which is exactly the string PyPI uses for a release file, so an exact name comparison against the release list is sufficient.)
  - src/virtualenv/seed/wheels/acquire.py:115 — T3 M8 (reason to dismiss: The wheel's distribution and version are read from the filename pip printed, which is exactly the string PyPI uses for a release file, so an exact name comparison against the release list is sufficient.)
  - src/virtualenv/seed/wheels/acquire.py:134 — T9 M11 (reason to dismiss: A private mirror or an offline wheelhouse legitimately serves a rebuilt wheel under the same distribution/version/filename PyPI also uses, so 'the digest must equal PyPI's' cannot be enforced unconditionally; the only safe reading is that an unverifiable wheel is let through, which in practice means not adding an enforcing check at all.)
  - src/virtualenv/seed/wheels/acquire.py:175-192 — T9 M11 (reason to dismiss: A private mirror or an offline wheelhouse legitimately serves a rebuilt wheel under the same distribution/version/filename PyPI also uses, so 'the digest must equal PyPI's' cannot be enforced unconditionally; the only safe reading is that an unverifiable wheel is let through, which in practice means not adding an enforcing check at all.)
  - src/virtualenv/seed/seeder.py:27 — T9 M11 (reason to dismiss: A private mirror or an offline wheelhouse legitimately serves a rebuilt wheel under the same distribution/version/filename PyPI also uses, so 'the digest must equal PyPI's' cannot be enforced unconditionally; the only safe reading is that an unverifiable wheel is let through, which in practice means not adding an enforcing check at all.)
  - src/virtualenv/seed/wheels/periodic_update.py:379-385 — T11 M8 (reason to dismiss: The lookup cache is only a performance optimisation, and a failed lookup already has to mean 'not verifiable, let the wheel through'; caching that failure merely avoids retrying a network call that just failed.)
  - src/virtualenv/seed/wheels/periodic_update.py:388-405 — T11 M8 (reason to dismiss: The lookup cache is only a performance optimisation, and a failed lookup already has to mean 'not verifiable, let the wheel through'; caching that failure merely avoids retrying a network call that just failed.)
- Uncovered routes to confirm (pattern B):   - src/virtualenv/seed/wheels/periodic_update.py:53-56 — T4 M6 (reason to dismiss: The wheel in the house was already hashed when download_wheel fetched it; the update log only stores metadata and never holds bytes, so re-checking a file replayed from the log is redundant work on every environment creation.)
  - src/virtualenv/seed/wheels/periodic_update.py:58-72 — T4 M6 (reason to dismiss: The wheel in the house was already hashed when download_wheel fetched it; the update log only stores metadata and never holds bytes, so re-checking a file replayed from the log is redundant work on every environment creation.)
  - src/virtualenv/seed/wheels/periodic_update.py:94-104 — T4 M6 (reason to dismiss: The wheel in the house was already hashed when download_wheel fetched it; the update log only stores metadata and never holds bytes, so re-checking a file replayed from the log is redundant work on every environment creation.)
  - src/virtualenv/app_data/via_disk_folder.py:104-105 — T4 M6 (reason to dismiss: The wheel in the house was already hashed when download_wheel fetched it; the update log only stores metadata and never holds bytes, so re-checking a file replayed from the log is redundant work on every environment creation.)
  - src/virtualenv/seed/wheels/bundle.py:54-59 — T5 M4 (reason to dismiss: The directory was named by the user on the command line (--extra-search-dir), so its wheels are the user's own trust decision, in exactly the way --find-links is; nothing virtualenv could compare them to exists for a private build.)
  - src/virtualenv/seed/wheels/bundle.py:35-38 — T5 M4 (reason to dismiss: The directory was named by the user on the command line (--extra-search-dir), so its wheels are the user's own trust decision, in exactly the way --find-links is; nothing virtualenv could compare them to exists for a private build.)
  - src/virtualenv/seed/embed/base_embed.py:109-116 — T5 M4 (reason to dismiss: The directory was named by the user on the command line (--extra-search-dir), so its wheels are the user's own trust decision, in exactly the way --find-links is; nothing virtualenv could compare them to exists for a private build.)
  - src/virtualenv/seed/embed/pip_invoke.py:44-78 — T7 M2 (reason to dismiss: The requirement is version-pinned and the matching wheel is already in the --find-links folder, so pip resolves the local file and never consults an index; --download is precisely the user asking pip to use the network.)
  - src/virtualenv/seed/embed/pip_invoke.py:57-58 — T7 M2 (reason to dismiss: The requirement is version-pinned and the matching wheel is already in the --find-links folder, so pip resolves the local file and never consults an index; --download is precisely the user asking pip to use the network.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T4, T5, T6. Why: Four independent judgements in four different files/packages, each with a different reason a solver can honestly stand down: T1 'pip already fetched it over HTTPS and exited 0'; T4 'it was hashed when it was downloaded, the log is only metadata'; T5 'the user named that directory'; T6 'the image was built from a wheel that had already passed the check'. T1's group is where the DeepSeek-shaped trap and the MiMo-shaped trap sit together: the protection is simply absent (T1) while the same site carries the coupled must-keep-working value that private mirrors/offline/private names are legitimate (T9), so a pass/fail check either misses the hole or over-hardens and breaks supported configurations; T4 is the producer-off-the-check's-path trap (the log turns a stored filename into a Wheel without reading it) and rewards the solver who extends the log schema or re-verifies on replay; T5 is a second absent-protection route with a strong dismissal; T6 is a proxy-object trap (the image cache decides on the stem, not the bytes) that no acquisition-time check reaches. Every one is testable offline with mocked Popen/urlopen and a local wheel file, and each needs a different mechanism to fix (verify returned bytes with a three-way outcome plus cleanup, extend the producer/replay, verify only when the name is a PyPI release, key or invalidate the image). Fixing only the sink the report names leaves three of the four open, which is exactly the stacking this checkout supports. Alternatives left out: T7 (PipInvoke index resolution) is a real second implementation but its 'correct' behaviour contradicts the --download flag asserted at test_pip_invoke.py:45; T8 is zipapp-only (app_data/base.py:93-97) so it is not reachable in an unpacked checkout; T11 (cached None fails open) is a property of whichever lookup the fix chooses rather than a site of its own; T2/T3/T9/T10 belong to T1's group because one correctly written guard at download_wheel closes or must honour them. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Custom/private index: acquire.py:134 forwards the caller's environment into the pip subprocess, so PIP_INDEX_URL / PIP_EXTRA_INDEX_URL / PIP_INDEX legitimately change where the wheel comes from; a rule that requires PyPI's digest rejects a wheel served by exactly the configured source. | Offline or proxied installs: the only metadata source used in this tree fails closed to None (periodic_update.py:388-405); treating 'no metadata' as a mismatch breaks air-gapped environment creation, so 'unverifiable' must mean allow. | Private/local distributions and wheels whose filename is not a PyPI release file must be let through (the published fix's own branches, per the screener's O6 shapes); refusing them breaks private packaging. | --extra-search-dir is a documented user trust boundary (base_embed.py:109-116); enforcing PyPI digests there contradicts the contract unless the unverifiable case is allowed. | PipInvoke's --download path deliberately leaves the index enabled; tests/unit/seed/embed/test_pip_invoke.py:45 asserts '--no-index' is absent, so a fix that adds it to close T7 breaks a documented flag and its regression test. | The update log is deliberately metadata-only: tests/unit/seed/wheels/test_bundle.py:63-66 expects a Wheel for a log entry whose file need not exist in the house, so a replay check must tolerate a missing file rather than turning the cache into an error. | Wheel-image reuse is a tested behaviour (tests/unit/seed/embed/test_bootstrap_link_via_app_data.py:105-110); any content-keyed cache must still produce the same site-packages on the second create. | A pip.conf / PIP_CONFIG_FILE index redirect is invisible to an env-based gate (the published fix's documented limitation per the screener); a gate reading only the three env vars leaves a supported configuration unverified, and a gate that also reads config files changes behaviour for users who never set the env vars. | Refused input shape that legitimate use needs: a wheel whose filename differs from PyPI's canonical filename for the same release (build tag, local version suffix) must not be treated as a mismatch when its bytes are the published artefact.. Conflicts the reader found: The natural fix for T1 (reject any wheel whose sha256 does not equal PyPI's) rejects the private-mirror, offline and private-distribution cases that acquire.py:134 and acquire.py:175-192 make supported configurations; the guard has to have a third 'not verifiable -> allow' outcome, so the same site carries both the hidden requirement and the must-keep-working value. | Checking a replayed wheel against PyPI needs a digest the producer never stored (periodic_update.py:94-104, :134-140), while the existing contract allows a log entry whose file is absent from the house (tests/unit/seed/wheels/test_bundle.py:63-66); recording a digest at download time and re-verifying when the file exists are two separate changes that must agree. | Keying the image on wheel bytes (or invalidating it after a rejected download) forces rebuilds of wheel/<py>/image/1/... on every content change, while tests/unit/seed/embed/test_bootstrap_link_via_app_data.py:105-110 asserts a second create reuses the cache and produces identical site-packages; the fix has to invalidate on mismatch without breaking ordinary reuse. | Verifying --extra-search-dir wheels against PyPI is only safe under the same 'not on PyPI -> allow' rule; otherwise a private wheel placed there (bundle.py:54-59) fails to seed, which is the documented purpose of the option (base_embed.py:109-116).

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

## Environment (`tasks/stk-virtualenv-2350/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-virtualenv-2350/instruction.md`)
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

## Tests (`tasks/stk-virtualenv-2350/tests/`)
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
- **Wrong-fix patches** go in `build/stk-virtualenv-2350/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-virtualenv-2350/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-virtualenv-2350/manifest.json`:**
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

**Also in `build/stk-virtualenv-2350/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-virtualenv-2350 --only static
python3 -I common/gate/gate.py stk-virtualenv-2350 --only nop
python3 -I common/gate/gate.py stk-virtualenv-2350 --only oracle
python3 -I common/gate/gate.py stk-virtualenv-2350 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-virtualenv-2350/`;
  - edit only `tasks/stk-virtualenv-2350/`, `build/stk-virtualenv-2350/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-2350.json`. Verify each trap on the
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

Stacked task slug: `stk-virtualenv-2350`. Control task slug: `stk-virtualenv-2350-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-2350.json`.
