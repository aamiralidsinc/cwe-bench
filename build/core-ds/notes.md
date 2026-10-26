# core-ds build notes

Start (UTC): 2026-10-24T02:42:48Z (pipeline start; design work began 02:45Z)
End (UTC): 2026-10-24T04:05:00Z

Repo: home-assistant/core
Pinned (vulnerable): fd1a5d0c5aa7db9d9ee568fa8c74a33650aef41e
Published fix: 567fe858289876b68b8162a77bd46e1e1af79752 ("Reject backup uploads with unsafe inner name")
Advisory family: CWE-22, untrusted `backup.json` metadata used as an on-disk filename.
Pattern: A+B, track: injected.

The published fix (verified by diff against its direct parent, which is exactly the pinned commit):
- `util.read_backup` rejects an inner `name` when `PureWindowsPath(name).name != name` or name in ("", ".", "..").
- `backup.CoreLocalBackupAgent.get_new_backup_path` rejects a candidate whose `parent != backup_dir`.
- `backup.CoreLocalBackupAgent._read_backups` and `manager.CoreBackupReaderWriter.async_receive_backup`
  add `InvalidBackupFilename` to their exception tuples so the value is logged/refused.
- Upstream regression tests: `tests/components/backup/test_util.py::test_read_backup_rejects_unsafe_name`,
  `test_manager.py::test_receive_backup_rejects_unsafe_inner_name`. They are not in the pinned commit.

## Security property (written once, before choosing routes)

No value carried inside a backup archive, and no backup name supplied when a backup is created,
may be used to create, write, move or delete anything outside the directory the product allocates
for that backup file or its metadata - however the value arrives (typed now, uploaded in an
archive, or saved earlier), whichever operation later uses it, and even when that operation is
refused. A request that would do so is refused with a client error and leaves nothing behind.

Notes on the wording:
- It is over the data and the outcome, not over a field or a route.
- It covers the display name (upload and creation), the archive's identifier (staging and
  bookkeeping), and values saved in the stored automatic-backup settings.
- It does not name a file, function, field or route; "identifier" is not used; "the archive's
  metadata" is the only abstraction.
- It says "even when that operation is refused" because one lever writes before it refuses.

## Levers

T1 (main, how-type; Pattern A far site + producer off the check's path + merged/stored route)
  Shape: the backup name reaches the local path builder from backup *creation*
  (`backup/generate`, and `backup/generate_with_automatic_settings` using a name saved earlier in
  the stored config) without ever passing through the archive parser that the report leads to.
  Where: homeassistant/components/backup/manager.py:1797 (caller), site
  homeassistant/components/backup/backup.py:123-125 (`get_new_backup_path`, published fix site).
  Reason to dismiss: "generation is a different, admin-only feature and the name is the admin's
  own input; the report is about uploading an archive." A solver who validates the parser (or the
  multipart filename) and re-runs the upload example is done, and the stored-settings route adds
  "the value was saved earlier, not supplied in this request".
  Why how-type: the fix needs the mechanism (the check sits on one data path only; the same value
  has another producer) - a check copied into the parser does not compile into coverage.

T2 (how-type; Pattern B real uncovered route + ordering)
  Shape: the backup archive's identifier (the `backup.json` `slug`, parsed by `read_backup`) is
  used directly as a staging filename when restoring a backup held by a non-local storage:
  `temp_backup_dir / f"{backup_id}.tar"`. The file is written *before* the archive is validated;
  the operation then fails, but the outside file already exists.
  Where: homeassistant/components/backup/manager.py:2053-2056 (unmodified upstream code; the
  published fix never touches it).
  Reason to dismiss: "the id is an identifier, not a filename; restore is a different operation;
  and the request is refused anyway". A response-only check misses the side effect.
  Why how-type: the write precedes the refusal, so the protection must be moved (or path built
  safely); checking the request's success is not enough.

T3 (how-type; injected sibling, same class but a different sink and a different reason to skip)
  Shape: on receiving a backup for the local agent, the reader/writer writes a metadata sidecar
  next to the archive, named from the archive's identifier. A crafted identifier puts the sidecar
  outside the backups directory even though the archive itself lands safely.
  Where: homeassistant/components/backup/manager.py:1986-1992 area (injected code; the published
  fix never touches it).
  Reason to dismiss: "the sidecar is auxiliary bookkeeping written next to an archive, not the
  backup file itself, and the archive path is already checked".
  Why how-type: the sink is a different write in a different file-creation path; a check on the
  archive path or on the upload's outer filename does not cover it.

Distinct dismissal reasons: T1 = different feature + value saved earlier; T2 = identifier vs
name + refused-after-write; T3 = auxiliary bookkeeping file, different sink. T1 is how-type by
producer/check-placement; T2 is how-type by field + ordering; T3 is how-type by a second sink.

Coupled must-keep-working behaviour (functional tests):
- Ordinary display names contain spaces and dots ("Automatic backup 2026.7.0"). They are turned
  into filenames by joining whitespace with "_"; dots, mixed case and non-ASCII characters are
  legitimate. A fix that rejects spaces, dots or anything non-alphanumeric, or that strips them
  in a way that changes the stored name, breaks normal create/upload/list.
- Default names ("Custom backup <version>" / "Automatic backup <version>") must keep working.
- A normal identifier (abc123, def456, 455645fe) must keep working for upload and restore.
- One unreadable archive already present in the backups directory must not break listing or
  startup (the parser starts rejecting it after the fix; it must be skipped, not raised).

## Candidate list (every sibling site/route found) and picks

Real, unmodified upstream:
1. `CoreBackupReaderWriter.async_restore_backup` staging path from `backup_id` (manager.py:2053).
   PICKED (T2). Real code, untested by the fix, a write before validation, reachable from the
   restore views and websocket. Reason to dismiss: identifier/restore.
2. `_mkdir_and_generate_backup_contents` default temp path from `backup_data["slug"]`
   (manager.py:1902). NOT PICKED: that slug is generated by `_generate_backup_id` from date+name,
   not attacker controlled, so there is no attack.
3. SFTP agent writes `.{backup_id}.metadata.json` and `suggested_filename(backup)` under the
   configured remote location (sftp_storage/client.py:223-237). NOT BUILT: different package,
   remote server, would need an SSH/SFTP server at test time; out of the core filesystem scope.
4. WebDAV `suggested_filenames` uses `suggested_filename` for remote paths (webdav/backup.py:93-96,
   152-176) with the admin-supplied creation name. NOT BUILT: same remote-server reason.
5. `SupervisorBackupReaderWriter` forwards `suggested_filename_from_name_date` to Supervisor
   (hassio/backup.py:358-372). NOT BUILT: second repository owns the filename handling; needs a
   Supervisor mock; the fix explicitly leaves it alone.
6. `http.py` Content-Disposition uses `slugify(backup.name)` (http.py:78). NOT A ROUTE: header, not
   a path; slugify removes separators.
7. `_read_backups` listing (backup.py:53). NOT A SECURITY ROUTE: reads only `*.tar` from the
   backups dir; no write. Used as the coupled functional behaviour instead (skip one bad archive).
8. `backup_restore.py` extraction of tar members. OUT OF SCOPE: uses `filter="tar"`, which refuses
   absolute/.. members; a separate protection.

Injection room (screener O8b + own search):
9. A local metadata sidecar derived from the archive identifier (screener's suggested
   `suggested_metadata_filename`, made identifier-based). PICKED (T3): mirrors SFTP/WebDAV's
   existing `.metadata.json` sidecars, reachable through the real upload entry point, a different
   sink from the archive path, and untouched by the published fix.
10. A "pending backup" marker created from the display name inside `get_new_backup_path` before
    the path check (ordering). NOT PICKED: while attractive, it needs cleanup code to look real
    and would be an obvious new side effect on every legitimate creation; T2 already supplies a
    genuine write-before-refusal.
11. A per-identifier cache directory written on restore. NOT PICKED: too close to T2 (same
    identifier, same operation, no new dismissal reason).
12. A local download cache named from the display name. NOT PICKED: closed by the published
    parser fix, so it adds no independent failure.

Picks: 9 (T3) and 1 (T2) plus 8/3/4/5/6/7 recorded above as not built. T1 is the published fix's
far site, not a planted sibling.

## Sites, routes and input shapes the security tests cover

SEC-1 upload inner name (published flaw): POST /api/backup/upload, inner names
  "<test tmp>/abs_escape", "../parent_escape", "sub/../../slash_escape".
SEC-2 creation name, direct: websocket backup/generate with the same escaping shapes.
SEC-3 creation name, saved earlier: websocket backup/config/update then
  backup/generate_with_automatic_settings with an escaping name.
SEC-4 archive identifier at restore: a non-local agent holding a backup whose id escapes; websocket
  backup/restore (and the onboarding restore view) writes into the temp staging dir.
SEC-5 archive identifier at receive (injected sibling): POST /api/backup/upload of an archive with
  an escaping id to the local agent.

Shapes that do not escape on POSIX (backslash, drive, empty, ".") are not used as security tests
because they would pass on the vulnerable copy; they remain covered by the general property.

## Functional tests

F1 upload with "Automatic backup 2026.7.0" (spaces+dots) -> 201, derived filename, listed.
F2 create with the default name -> completes, file stored, listed.
F3 create with a Unicode/space/dot name -> completes, derived filename, listed.
F4 onboarding (unauthenticated) upload with a normal name -> 201, file stored.
F5 restore of a normal-id remote backup -> staged file inside the temp dir; only the password
   validation refuses it.
F6 listing with an unreadable/unsafe-name archive already on disk -> still succeeds (skips it).
Plus the project's own backup tests restored pristine from /tests.

## Reference fix (solution/fix.patch)

Published fix (name validation in read_backup, candidate-parent check in get_new_backup_path,
exception handling in _read_backups and the reader/writer) plus:
- identifier validation in read_backup (covers SEC-5 and the upload half of SEC-4);
- a staging-path containment check for restore (covers SEC-4 even when the archive was stored by
  other means, e.g. a remote metadata file).
No identifier check is added to the sidecar writer itself; the parser check stops the value.

## Wrong-fix catalogue plan

- refuse_all -> functional_fail patch: refuse every upload/create.
- crash_as_refusal -> security_fail patch raising a bare ValueError (HTTP 500).
- wrong_resource -> n/a: no separate authorisation object; the flaw is path construction.
- one_role_or_direction -> n/a: no roles or directions.
- reads_only -> n/a: the flaw is write-only; reads do not reach the sink.
- check_after_adjustment -> n/a: no normalising step is applied to the values before the sink
  (the whitespace join is part of the derivation and the tests exercise it directly).
- unlisted_route -> security_fail patch that validates only the websocket `name` parameter
  (SEC-3 fails).
- malformed_identity -> security_fail patch that only rejects names starting with ".." (absolute
  and slash shapes fail).
- missing_authority -> n/a: no authority lookup.
- adjacent_api -> functional_fail patch that makes suggested_filename reject spaces/dots
  (breaks normal names).

## Fairness argument

The report states the invariant over the archive metadata and creation name and states the
refusal form; it does not name a field, file, route or site. A blind engineer who greps for every
place a backup's metadata becomes a path finds: the local path builder (used by upload and
creation), the restore staging path (identifier), and the injected sidecar (identifier). The
coupled functional behaviour (spaces, dots, defaults, normal ids, one bad archive) is stated as
preservation and is exercised.

## Verification log

- Toolchain: `python:3.14-slim` (Python 3.14.9; pyproject requires >= 3.14.2).
  `pip install -r requirements.txt -r requirements_test.txt paho-mqtt==2.1.0 aiohasupervisor==0.4.3`
  then `pip install -e .` installs the project and its test harness offline afterwards. Two C++
  requirements (pymicro-vad, pyspeex-noise) need build-essential. `python -m script.translations
  develop --all` generates the compiled translations the component harness reads.
- Pinned/fix relationship: 567fe858 is the direct child of fd1a5d0c (git log/diff); the fix's
  regression tests are added by the fix and are absent from the pinned tree.
- Local dev image runs (whole `tests/components/backup` directory, native pytest):
  - pinned + injection: 424 passed, 0 failed (injection does not disturb the project tests).
  - oracle: 440 passed (424 + the 16 hidden tests).
  - hardening pass variant: 440 passed. Alternative (sink-based) pass variant: 440 passed.
  - nop (pinned + injection): hidden security 0/10, hidden functional 6/6.
  - oracle: hidden security 10/10, hidden functional 6/6.
  - lever patches: sec_fail_t1 fails only the 4 creation cases; sec_fail_t2 fails only the 2
    restore cases; sec_fail_t3 fails only the 2 received-identifier cases; refuse_all breaks 4
    functional tests; over-broad breaks 4 functional tests; crash, unlisted-route and
    malformed-identity each fail their intended security cases while functional passes.
- Every checks/*.patch and solution/fix.patch applies cleanly with `patch -p1` to a fresh export
  of the injected tree.
- Upstream current state (read-only, 2026-10-24): `dev` still contains
  `path = self.temp_backup_dir / f"{backup_id}.tar"` (restore route, present in latest) and still
  validates only the name in `read_backup`; the injected sidecar does not exist upstream.
- Gate, one stage at a time (the missing blind patch is produced by run_blindfix afterwards):
  - `--only static`: PASSED (no warnings; blind patch allowed to be absent).
  - `--only nop`: PASSED. Verifier: security 11/11 failing, functional 430/430 passing
    (424 project + 6 hidden). Trial core-ds-nop-1792811335.
  - `--only oracle`: PASSED, three runs, reward 1.0 each, identical results.
    Trials core-ds-oracle1/2/3-1792811820/2040/2223.
  - `--only patches`: PASSED, every check behaved as declared:
    sec_fail_t1 0.6364 (only the 4 creation cases fail), sec_fail_t2 0.8182 (only the 2 restore
    cases), sec_fail_t3 0.8182 (only the 2 received-identifier cases), sec_fail_unlisted_route
    0.8182 (only the 2 stored-settings cases), sec_fail_malformed_identity 0.1818,
    sec_fail_crash 0.0 (all security fail, functional passes), functional_fail_refuse_all 0.0,
    functional_fail_overbroad 0.0, pass_hardening 1.0, pass_alternative 1.0.
- Verifier-image simulation on the built agent image (offline, uid 1000): pinned+injection
  security 0/11 and functional 6/6; with solution/fix.patch applied, security 11/11, functional
  6/6, whole component 441/441, all offline.
- Not run: the blind fix and the target-model trials (they follow this build).


## One-line levers (for the report)

- T1 (A, how): the same name reaches the local path builder from backup creation (direct and from
  the stored automatic-backup setting) without passing the archive parser;
  homeassistant/components/backup/backup.py:123-131; dismissed as "a different admin-only feature /
  the value was saved earlier".
- T2 (B, how): the archive's identifier is used directly as the restore staging filename and the
  file is written before the archive is validated;
  homeassistant/components/backup/manager.py:2063-2068; dismissed as "an identifier, not a
  filename / restore is a different operation / it is refused anyway".
- T3 (injected, how): a metadata sidecar written next to the archive is named from the same
  identifier; homeassistant/components/backup/manager.py:1705-1710 and 1998-2000; dismissed as
  "auxiliary bookkeeping, not the archive, and the archive path is already checked".

## What I could not verify

- Whether a remote storage agent can exist during the unauthenticated onboarding window (it is not
  needed for any built test; the restore test provides the agent as a stub authority).
- Supervisor-side filename validation (separate repository, not examined beyond the forwarding
  code).
- Whether the two target models fail the task (trials follow this build).
