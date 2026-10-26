# composer-ds — build notes (STOPPED, no task shipped)

- Start UTC: 2026-10-18T19:18:00Z
- End UTC:   2026-10-18T19:52:00Z
- Outcome:   abandoned before building. The advisory's protection is fully closed by two
  realpath-containment guards; every fair lever surface was already trialled on this exact
  advisory and both target models solved it 3/3. No design found that can meet the bar.

## Verified facts (not guesses)
- Pinned `24e396b5279a92fadf4897dd701d2cb97942cda3` == `git rev-parse 53b8bb4c^`; fix
  `53b8bb4c24697b2f00a18cf1ef35a10392701b89` (merge of `ad649fdf…`, identical tree) changes only
  `src/Composer/Installer/BinaryInstaller.php` + `src/Composer/Downloader/FileDownloader.php` (plus
  its own regression tests). Current upstream `main` carries exactly the same two guards and no
  later follow-up guard.
- Complete set of dependency-controlled permission sinks in the pinned tree (grep of
  chmod/chown/chgrp/setfacl over `src/`): BinaryInstaller installBinaries (L103), injected refresh
  (L144), proxy `.bat`/unixy links (L185/192, paths in vendor/bin, not attacker-controlled);
  FileDownloader install loop (L368) and injected refresh (L386); RarDownloader's `chmod -R` on the
  install path (not attacker-controlled, needs unrar). The remaining chmod sites act on config /
  self-update files, not dependency metadata.
- Complete set of `getBinaries()` consumers: BinaryInstaller (3), FileDownloader (2), the
  ValidatingArrayLoader lexical `..` check, EventDispatcher's root-package script resolution
  (trusted root, out of scope), ExecCommand (display only).
- No genuine uncovered route (pattern B): both published sinks are guarded by the fix; no other
  route reaches a chmod of a package-controlled path; the provider (installed.json/reinstall) is
  irrelevant once the sink is guarded.

## Decisive evidence against the bar
- This exact advisory, pinned commit and mechanism set was already built as
  `tasks/composer-symlink-path-inj` (pattern A+B) with five levers: the two published sinks, the
  `..`-metadata input shape, and two injected refresh siblings (BinaryInstaller and
  FileDownloader/PathDownloader).
- Its trials: DeepSeek V4.1 Flash 3/3 solved (reward 1.0), MiMo-V2.6-Pro 3/3 solved
  (`build/composer-symlink-path-inj/runs_*.log`, `trial_detail_*.json`). No test leakage: the
  hidden-test names appear nowhere in either agent trajectory; both models found every sink by
  grepping `chmod`/`getBinaries`/`BinaryInstaller` and applied a realpath containment helper.
- Therefore the strongest fair lever set available for this advisory is known-solvable by both
  target models.

## Candidate levers examined and why none is a fair, bar-meeting addition
- Another chmod sibling (installer, downloader, archive, custom-installer route): every such
  sibling necessarily contains `chmod` and/or `getBinaries()`, both of which both models grep over
  all of `src/`; it is found and guarded. More of the same does not change the outcome.
- A sibling with no `chmod` textual cue (chown/chgrp, helper-delegated mode change): not plausible
  maintainer code for composer (the codebase has no chown/chgrp at all) and still reachable only by
  the same bin list, i.e. unfair or trivially found.
- A sibling whose existing guard is lexically weak (looks protected): both models read the whole
  file, identify the symlink gap that is the point of the advisory, and replace the check.
- A sibling reached through `$link` (vendor/bin) symlink state: a dependency cannot create that
  state; the trigger is not reachable through a real entry point.
- Coupled over-broad trap: the only legitimate cases are in-package symlinks and symlinked install
  paths, which a realpath guard (what both models write) preserves; no legitimate case fails a
  correct fix, so no functional test can separate the models' fixes from the oracle.
- Producer/load-time requirement: the published fix is at the sink, so a producer-only test would
  fail a correct sink-side fix (unfair), and a sink-side test passes the models.
- Removing the instruction's enumerating clauses: both models' discovery was driven by broad
  `chmod|getBinaries` greps, not only by the wording; no evidence it would change the result.

## What I could not verify
- I did not run target-model trials myself (forbidden by the build brief). The bar assessment rests
  on the recorded 3/3 solves of the materially identical build and on the exhaustive sink inventory
  above.
- Current-upstream look was read-only via raw.githubusercontent.com (no later guard found).

## Out of scope (one line)
- Root-package bins (EventDispatcher) are trusted; the guard/chmod race is not pursued; neither is
  built on.
