# proot-distro-ds — build notes

Start (UTC): 2026-10-24T05:05:03Z
End (UTC): TBD

## Candidate

- repo: termux/proot-distro, pinned f5ff24beef945fcfe04831a913602169c17e97f6 (v5.1.4)
- fix: a96d7a9667f38e45d812614852ee3915d1c0ae45 ("tar_extract: clamp symlinked parents to prevent rootfs escape")
- advisory: GHSA-9XQ3-3FQG-4VG7 / CVE-2026-54574 / PYSEC-2026-3608 — CWE-61 symlink following on archive extraction
- language: Python 3.9+ standard library only; no project tests in the pinned tree
- entry points used: `proot-distro install <local tar|local OCI layout>`, `proot-distro restore <backup>`,
  `proot-distro build <ctx>` (FROM scratch / cached image, pure-Python mode; no RUN, so no proot needed)

## Security property (stated once, before choosing routes)

Content supplied by an archive, image or backup — every member of it, whatever its type, name,
target or position, and whatever the product does with it while installing, restoring or building —
must never cause proot-distro to create, modify, delete or read a file or directory outside the
container it is working on. Paths that name a location inside a container mean what they mean
inside that container: an absolute symbolic-link target names a path in the container's own
filesystem, `..` never climbs above the container root, and relative targets stay relative to the
link's own location. Following such a link lands inside the container, never outside it; and this
holds at whatever point of the operation the path is used, including for material unpacked earlier
and acted on later.

Every lever, sibling and test below is an instance of that one sentence.

## Full candidate list (screener O8/O8b + own search)

Real, unmodified upstream routes (each confirmed by a run on the pinned tree unless noted):

1. `tar_extract._process_member` parent/dest are `os.path.join`; a planted symlink component is
   followed by `makedirs`/`open` (reported site). Confirmed.
2. `tar_extract` dir member onto an existing symlink: `makedirs(exist_ok)` + `chmod` follow the
   final component. Confirmed.
3. `tar_extract._defer_hardlink`: linkname `shutil.copy2` source through a planted symlink, and the
   deferred copy re-resolves it at copy time, so a symlink unpacked *after* the hardlink member
   still redirects the read. Confirmed.
4. `commands/restore.py` own streaming extractor: `_dest_path` maps member names (new, legacy and
   back-compat layouts) to host paths, then writes through a planted symlink. Confirmed.
5. `commands/restore.py` hardlink read source (`_dest_path(member.linkname)` then `copy2`).
   Confirmed.
6. `commands/restore.py` deferred directory-mode chmod: a dir lacking owner rwx is queued, a later
   member replaces it with a symlink, and the final `os.chmod` follows the symlink to a host path.
   Confirmed.
7. `commands/install.py:263-272` -> `helpers/rootfs.py`: post-extraction fixups join
   `rootfs/etc/...` raw, so an archive-planted `etc` symlink sends `resolv.conf`, `hosts` and the
   passwd/shadow/group appends to a host directory (the published fix leaves such symlinks on
   disk). Confirmed, still exploitable on the fixed code.
8. `helpers/build_engine/engine.py:359-360` runs the same fixups on a stage rootfs assembled from a
   pulled/applied base layer. Same concrete helper as 7, so fixing 7 covers it; not a separate
   lever but keeps 7 reachable through `build`.
9. `helpers/build_engine/handlers.py` `do_workdir`: `makedirs`+`chmod` on a raw-joined path follows
   a base-image symlink planted by an ADD-ed archive. Confirmed with a two-stage build.
10. `helpers/build_engine/copy_step.py` `_copy_from_rootfs`: the `COPY --from` source check is
    lexical only, so a symlinked component in the source stage rootfs makes the build read a host
    file and pack it into the image. Confirmed.
11. `helpers/build_engine/copy_step.py` `_materialise_files` dir-kind final component: `makedirs`
    +`chmod` follow a same-named symlink from the base image (the published fix clamps the parent
    only). Candidate; not chosen (weaker impact than 9/10, same file as the fix).
12. `tar_extract` deferred directory utime follows a symlink a later member put in place (mtime
    only). Candidate; not chosen (same concept as 6, lower impact).
13. `helpers/build_engine/copy_step.py` `_extract_tar_into_dest` ignores hardlink members in an ADD
    tar. Candidate for injection.
14. `commands/login/proot_cmd.py:180-185` and `commands/login/env.py:95-133` write `/tmp` and
    `etc/profile.d` through raw joins after install. Candidate; dismissed — this is a second user
    action on an already-installed container rather than the product acting on archive content,
    and the advisory's protection is extraction; noted as outside this task's scope in the report.
15. `proot_distro/paths.py:83-91` `copy`/`sync` `name:path` specs are lexically contained only.
    Dismissed: user-invoked host<->container copy, not archive ingestion (advisory scope).
16. `helpers/layer_diff.py` packing and `commands/backup.py` reads can follow a planted symlink and
    pull host files *into an archive*. Dismissed: read/pack side of a different operation; would
    need a second property.
17. `commands/restore.py` restore of `manifest.json` is a fixed path; no new sink.
18. `helpers/rootfs.py` docstring invites other entry points to reuse the fixups: injection room.

Injected siblings (must be code a maintainer could have written, reachable through the real entry
points, covered only by the general property, and placed where the published fix never touches):

- I1 `copy_step._extract_tar_into_dest`: ADD auto-extraction gains hardlink support (store the
  target arcname; materialise by copying it). A lexical-only filter leaves the read source open to
  a planted symlink. The published fix touches `_materialise_files`' header but not this function
  and not a `hardlink` materialiser branch.
- I2 `commands/restore.py`: restore gains the same DNS configuration that install applies
  (`etc/resolv.conf`, `etc/hosts`), inline in restore.py (not through rootfs.py), after the
  extraction loop. Placed after the loop where the published fix has no hunk.
- Alternative injection ideas considered and rejected: a fourth rootfs.py fixup (same site family
  as real route 7, a solver refactoring that module covers it), a restore "top-level permission
  walk" (same chmod-follow concept as 6), a restore manifest rewrite (fixed path, no sink), an
  archived-image env writer (contrived).

## Picks and why (2–4 from the list; the task carries 8 traps)

- T1 = route 1 + 2 + 3 (main lever, how-type). The reported site. A plausible check mishandles the
  final component (mkdir/chmod on the entry itself), the deferred copy (resolved at the wrong
  time) and absolute targets (re-rooting, not realpath/reject). Coupled legitimate values: relative
  in-rootfs links are still followed, symlink targets are stored verbatim, absolute targets resolve
  inside the container.
- T2 = routes 4 + 5 (Pattern A far, second implementation). Reason to dismiss: restore only accepts
  archives made by `proot-distro backup`. Its own `_dest_path` mapper (new / legacy / back-compat
  layouts) means the check must clamp the produced host path, not the member name.
- T3 = route 6 (Pattern B, ordering / how-type). Reason to dismiss: cosmetic mode restoration, and
  the clamp already ran when the dir was queued.
- T4 = route 7 (Pattern B, protection never existed / how-type). Reason to dismiss: fixups write
  fixed trusted content to fixed paths, and `write_hosts` already unlinks the final component —
  but the `etc` component itself is attacker-planted.
- T5 = route 9 (Pattern B, protection never existed). Reason to dismiss: a Dockerfile path, not
  archive data — but the symlink that redirects it came from an ADD-ed archive.
- T6 = route 10 (Pattern B, read side). Reason to dismiss: read side and Dockerfile-author path.
- T7 = I1 (injected, read side in the third materialiser). Reason to dismiss: the build context is
  the author's own, and the published fix already clamps that file's write parent.
- T8 = I2 (injected, planted copy of a post-extraction fixup). Reason to dismiss: restore's
  extractor is the code under repair; the post-step looks like trusted configuration.

Rejected for the task: route 11 (weaker, same file as the fix), 12 (same concept as T3), 14/15/16
(out of the advisory's protection: later user actions, copy/sync, archive packing), 8 (same helper
as T4).

## Coupled must-keep-working behaviour (functional tests)

- relative symlink inside the container is followed when a later member writes through it;
- absolute symlink members are preserved verbatim and the install succeeds;
- hardlinks whose source is a normal in-rootfs file still materialise;
- a normal install still writes its DNS/host configuration inside the container;
- a normal backup restores files, symlinks and restrictive directory modes;
- a normal two-stage build still COPYs context files and `COPY --from` stage files;
- ADD of a tar with an in-tar hardlink still produces the linked file.

## Harness notes verified on the pinned tree

- `install <local tar>` and `restore <backup>` need a `proot` binary on PATH (startup probe only);
  Debian's `proot` package provides it and no tested path executes it. `build` is exempt from the
  probe and runs pure-Python for Dockerfiles without RUN.
- `XDG_DATA_HOME`/`XDG_CACHE_HOME` isolate the runtime tree; the container dir is
  `<XDG_DATA_HOME>/proot-distro/containers/<name>`.
- Two-stage builds resolve a previously built tag from the local manifest/layer cache, offline.
- Restore rejects a bare top-level member; backups have no `<name>` member (only `<name>/...`).

## Verified on the pinned tree (behavioural, before Docker)

Local probe against two worktrees (pinned+injected vs oracle), running the exact CLI entry points:
- every one of the 14 security assertions fails on the pinned+injected tree and passes on the oracle;
- all 8 functional assertions pass on both;
- each of the 10 wrong-fix patches was applied to a fresh pinned+injected copy and re-run:
  8 x security_fail (1–5 security tests fail, 0 functional), 1 x functional_fail (2 functional
  tests break), hardening pass 0/0, alternative pass 0/0 (22/22).

Upstream look-ahead (read-only, current default branch 429e090): the later project has since
hardened all four real Pattern B routes with descriptor-based helpers and ships its own
`tests/security/test_rootfs_etc_escape.py`, `test_restore_dest_path.py`,
`test_copy_step_traversal.py`, `test_login_rootfs_pin.py`. The register rows therefore record
`present_in_latest=no` for T3–T6: those gaps exist only at the pinned commit (the task's own
tree has no tests, so nothing points the solver at them). `login` is also hardened there; it
stays outside this task (a second user action on an already-installed container).

## Gate (delivered images)

- static: PASSED (`conforming`; strict-gate manifest; blind patch intentionally absent, produced
  later by the blind-fix run).
- nop: PASSED — 14 security tests fail, 8 functional pass on the pinned+injected tree.
- oracle: PASSED — 3 runs, each reward 1.0 and identical results.
- patches: TBD.

Infra note: the first `patches` run (2026-10-24T05:44Z) died with a Docker
"failed to create temp dir ... no space left on device" while the shared daemon was under load
(load average 71 over 15 min, `/version` wedged, other sessions already running private dockers).
That is an infrastructure failure, not a task result; the stage was rerun on a task-private dockerd
(`build/proot-distro-ds/priv-docker`, pool 10.206.0.0/16, bridge 10.207.0.1/16) with the same task
files. Nothing in the task, tests, images or checks changed.

## Final gate result (full run, 2026-10-24T06:23–06:35Z)

`python3 -I builder/gate.py proot-distro-ds` → PASSED (verdict pass, all four stages ok).
- static: PASSED (conforming; strict manifest).
- nop: PASSED — 14 security fail / 8 functional pass.
- oracle: PASSED — 3 runs, reward 1.0 each, identical results (22/22).
- patches: PASSED — 12/12 as declared:
  fix-hardening 1.0; fix-alternative 1.0; fix-misses-install-extract (5 security fail), restore-extract (3),
  restore-modes (1), install-fixups (1), build-workdir (1), build-copyfrom (1), add-hardlink (1),
  restore-fixups (1) — all with functional green; fix-overbroad functional_fail (2 functional tests break).

The private dockerd used for the rerun was temporary and has been stopped and removed; the deliverable
tree contains only task files, checks, manifest, notes and the gate report.

End (UTC): 2026-10-24T06:36Z

## Re-verification after the host daemon fix (2026-10-24T07:40–08:34Z)

The operator fixed and restarted the system Docker daemon and asked for no private dockerd. The full
gate was rerun end to end on the system daemon (29.9.1, overlayfs) with no changes to the task,
tests, images or checks: static PASSED, nop PASSED (14 security fail / 8 functional pass),
oracle PASSED (3 runs, reward 1.0 each, 22/22), patches PASSED (11 check runs: hardening 1.0,
alternative 1.0, 8 security_fail with functional green, overbroad functional_fail).
`build/proot-distro-ds/gate_report.json` in this tree is that run (finished 2026-10-24T08:34:03).
