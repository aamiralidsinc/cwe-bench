# local-operator-ds — build notes

Start (UTC): 2026-10-24T05:27:24Z
End (UTC): 2026-10-24T09:35:00Z

Advisory: PYSEC-2026-4009 / GHSA-22MG-8GW7-636X (damianvtran/local-operator)
Pinned: 17b6b673f9fe6ff7de58d8c886df0e5eae8cb16c
Fix:    29fc4c68a3ed1d238b8abf6b6a6136a3361416a5
Pattern A, injected. Main entry point: the agent profile APIs (HTTP) + `AgentRegistry` library API + the
agent edit HTTP route.

## Plan (written before building)

### Security properties, stated once

P1 (profile intake): *Bringing a profile into the installation is a copy into a destination the service
chooses. No value that arrives with a profile — or with any bundle of profile data — may determine which
filesystem location the service reads, creates, replaces or removes, including a value the service saved
earlier and reads back later. Bringing one in never removes or overwrites a profile, or its private
files, that is already present.*

P2 (agent-named reads): *Whenever a request names an agent and asks the service to read a file, the
location must resolve inside the workspace configured for that agent. A request may instead carry the
file's contents itself; when it does — including an empty buffer — the service must use what it was given
and must not read the location.*

Refusal contract (one statement for the product): a request that would break either property is refused
with a client error and leaves nothing behind outside the place the operation owns.

Coupled must-keep-working values (stated once): display names stored verbatim even when path-shaped;
instruction files still copied and private history still excluded; export→import round trips including
older profiles; workspace files read by relative or in-workspace absolute path; in-workspace links;
a filesystem-root workspace; empty buffers are real buffers.

### Levers

L0 (reported site, shape trap) `archive_identity`: the archive `id` selects `agents_dir / id`, which is
rmtree'd when present. Shapes: `../outside`, `../../outside`, absolute, empty, and — the trap — a
perfectly valid UUID that names an existing local agent (tempting fix: validate the id is a UUID and keep
it, leaving "if exists: rmtree"). Where: `local_operator/agents.py:1488,1503-1512` (pinned).
Reason to dismiss/skip: a UUID looks like a safe identity; the report names the archive id, so a
validator that keeps it reads as a fix.

L1 (MAIN, how-type: producer off the check's path) `stored_profile_identity`: the registry loads agents
keyed by the `id` stored in each `agent.yml` (`_load_agents_metadata`, `_refresh_agents_metadata`), not by
the directory name, and destructive/read operations join that stored id to `agents_dir`
(`delete_agent`, `update_agent`, `save_agent`, export, state load/save). An intake that gives the row a
fresh directory but persists the shared document verbatim poisons the registry identity; a later normal
request (delete of the row the user sees) then removes a location the profile did not own, or the whole
store. The intake's check never calls the loader. Injected sibling S1 supplies the document.
Where: `local_operator/agents.py:283-310,653-685` (real loader) + injected `local_operator/profile_share.py`
and `POST /v1/agents/install`.
Reason to dismiss/skip: the intake assigns a fresh UUID and reserves its directory exclusively, so it
"obviously" cannot name a destination; the stored id is only a display field.

L2 (how-type: route where the protection never existed, sink in untouched real code)
`legacy_manifest_identity`: the product still migrates the pre-0.2 single-file store (`agents.json`);
`migrate_legacy_agents` joins each manifest `id` to `agents_dir` with `mkdir(parents=True)` and writes
`agent.yml` there. Injected sibling S2 adds the compatibility upload route that feeds it a submitted
manifest. The published fix never touches this file region.
Where: `local_operator/agents.py:1229-1290` (real) + injected `AgentRegistry.import_legacy_manifest`
and `POST /v1/agents/legacy-import`.
Reason to dismiss/skip: legacy compatibility code, "local data only", and the upload is extracted with
the project's safe extractor, so the route looks protected.

L3 (shape trap: a resolved path against a lexical check) `workspace_preview_confinement`: injected
sibling S3, a read-only workspace file endpoint for the desktop editor, contains the file with
`str(target.resolve()).startswith(str(workspace_root))`. Traversal, absolute-outside and symlink escapes
are rejected; a sibling directory whose name shares the workspace's prefix is not.
Where: injected `local_operator/server/routes/editor.py` + `app.py` include.
Reason to dismiss/skip: a containment check exists and looks canonical, and the endpoint is a preview
helper, not the edit route the report names.

L4 (coupled must-keep-working, over-broad fix trap) `coupled_legitimate_values`: profile names that look
like paths are display names; permitted instruction files still arrive; export→import round trips work;
relative and in-workspace absolute paths, in-workspace links, a filesystem-root workspace and an empty
editor buffer all keep working. A stricter-than-needed fix (santise the name, refuse links, refuse root
workspaces, treat an empty buffer as absent) fails.
Where: `local_operator/agents.py:1489-1543`; `local_operator/server/routes/chat.py:644-654` (pinned).

L5 (published second protection) `workspace_edit_confinement`: the edit route's server-side read is
unconfined at the pinned commit (traversal, absolute outside, sibling prefix, symlink escape, NUL,
directory, non-UTF-8, missing/blank/relative workspace) and the request can carry the buffer instead
(`file_content`, empty is valid).
Where: `local_operator/server/routes/chat.py:644-654`; `local_operator/server/models/schemas.py:949`.

### Sites / routes / shapes covered by security tests

- `POST /v1/agents/import` + `AgentRegistry.import_agent` (and `download_agent_from_radient` via the
  `GET /v1/agents/{agent_id}/download` pull route): path-shaped ids, absolute id, empty id, valid UUID of an
  existing agent, collision with a file/symlink/dangling symlink, malformed metadata, copy failure
  cleanup, ZIP symlink/traversal entries.
- `POST /v1/chat/agents/{agent_id}/edit`: traversal, absolute outside, sibling prefix, symlink escape,
  NUL, directory, non-UTF-8, missing/blank/relative/file workspace, supplied buffer (non-empty and empty).
- S1 `POST /v1/agents/install`: a path-shaped document id, and a document id equal to an existing agent,
  each followed by the product's own reload and a normal delete addressed with the id the store reports.
- S2 `POST /v1/agents/legacy-import`: manifest id `../../outside`.
- S3 `GET /v1/chat/agents/{agent_id}/files/content`: sibling-prefix escape.

### Injected sibling candidates: the full list, and why the picks won

Every candidate found by search of the pinned tree:

1. `agents.py:_load_agents_metadata` / `_refresh_agents_metadata` — real loader keyed by stored yml id,
   not the directory name. **Used** (this is the producer half of L1; it is the mechanism, reached
   through S1, not a sibling by itself).
2. `agents.py:migrate_legacy_agents` — manifest ids joined into `agents_dir`, `mkdir(parents=True)`,
   never had any check. **Used** as the sink of S2 (real code, untouched by the fix).
3. `agents.py:migrate_agents_dir` — moves nested directories by directory name; not attacker-controlled.
   Not used (no attacker value reaches it).
4. `agents.py:delete_agent` / `update_agent` / `save_agent` / `clone_agent` / `export_agent_archive` /
   `load_agent_state` / `save_agent_state` — all join a registry key to `agents_dir`; reachable with a
   poisoned key only. Not injected; they are the consequence paths L1 tests.
5. `agents.py:download_agent_from_radient` — temp zip name built from the caller-supplied `agent_id`;
   over HTTP a path param cannot carry a separator, and the CLI attacker is the same local user.
   Dismissed as out of the remote threat model (noted in the report).
6. `agents.py:export_agent_archive` — filename from the agent's name is already reduced to a basename
   upstream; the cleanup holds the created directory. Not a gap.
7. `agents.py:_safe_extract_zip` — traversal and symlink rejection already present. Not a gap;
   functional-test material.
8. `server/routes/static.py` media/HTML routes — client-supplied absolute path read filtered only by
   mime type. Real and unconfined, but the screener records it as a separate file-read surface outside
   this advisory. Noted in the report, not built on.
9. `server/routes/chat.py` attachments — passed through to the executor as text listing; no server read
   (verified: `server/utils/operator.py:660-683`). Not a gap.
10. `teams.py` — `validate_team_id` plus symlink refusal already present. Guarded.
11. `server/routes/config.py` — reads a fixed path. Not a gap.
12. `server/routes/agents.py:import_agent` route — temp zip path is a fixed name. Not a gap.
13. `cli.py` serve bind default — an exposure default, not a check; a different protection. Not built on.

Picks:
- **S1 shared-profile install document** (new `profile_share.py` + route in `routes/agents.py`): a
  how-type producer whose flaw is only visible after a reload; looks safe because it generates a fresh
  id and reserves its directory with an exclusive mkdir. Beats candidate 5 (local-only) and candidate 8
  (out of scope).
- **S2 legacy bundle import** (route + small registry method, sink in the real migration): a route where
  the protection never existed, close to real code, far from the reported site. Beats candidate 2 alone
  because real code alone has no attacker-controlled entry point.
- **S3 workspace preview read** (new `routes/editor.py`): a real-looking containment check that is
  lexical, so a resolved target escapes through a prefix sibling. Beats candidate 8 (out of scope,
  no agent workspace) as the second confinement surface.

Three siblings, three different reasons to skip (looks validated / looks legacy / check exists).

### Test plan

security/: import shapes (path ids, absolute id, empty id, valid UUID of an existing agent, collisions
with file/symlink/dangling symlink, malformed metadata, ZIP member abuse, pull route), edit shapes
(traversal, absolute outside, sibling prefix, symlink escape, NUL, directory, non-UTF-8, workspace
failures, buffer non-empty/empty), S1 (path-shaped and victim-UUID document, after reload; legacy yml
already on disk), S2 (manifest traversal), S3 (prefix sibling). All assert a client error (4xx, never one
exact code) plus no side effect, or for reads: the outside content never reaches the model.

functional/: import a normal profile (name verbatim with a path-shaped name, instruction file copied,
private history excluded, returned id addresses the row), export→import round trip, legacy/older profile
import, install a normal document, edit with an in-workspace absolute path / in-workspace link / root
workspace, unknown agent 404, files never written by edit.

### What I must verify while building

- Every security test fails on pinned+injected and passes on the oracle (locally, then gate nop/oracle).
- Every functional test passes on both trees.
- The project's own affected tests pass at the pinned commit in the image.
- No test file content in environment/ (inject.patch must not share lines with tests).
- instruction.md contains no file/function/route/sibling identifiers.

## Build log and verification (filled while building)

Built at /home/mara/cwe-bench/tasks/local-operator-ds. Injected siblings are applied by
environment/inject.patch; the reference fix is solution/fix.patch (published source changes plus the
loader, shared-profile, legacy-manifest and workspace-view fixes).

Local verification before the gate (offline, in a venv built from the pinned tree):

- pinned+injected tree: security 36/36 FAIL, functional 12/12 PASS (the nop shape).
- oracle tree: security 36/36 PASS, functional 12/12 PASS; with the project's own three affected test
  files re-run from pristine copies, 96 pass and the 3 tests that assert the pre-fix id-preserving
  import are deselected (they encode the vulnerability).
- every check patch behaves as declared: sec_miss_archive 1 security failure, sec_miss_stored 2,
  sec_miss_legacy 2, sec_miss_preview 1, sec_miss_edit 15, crash_as_refusal 3, check_after_adjustment 2,
  malformed_identity 1, reads_only 16, all with functional 12/12; func_overbroad 1 functional failure,
  refuse_all 3 functional failures; hardening and alt_fix 36+12 pass.
- score.py over the three JUnit files: oracle reward 1.0 (144/144), nop reward 0.0 (security 0/36,
  functional 108/108).

## What I could not verify

- Whether the advisory's published text describes the edit-route read as well as the archive import;
  only the screener summary was available.
- The repo size in MB (not measured).
- Whether current upstream still trusts a stored agent.yml id for destructive joins: the checked-out
  default branch has since added id validation in save/read paths, so the producer half of L1 is
  exercised by our own sibling plus the planted-row test rather than by upstream code.
- The models' behaviour (no trials were run, as instructed).

## Outside this advisory's scope (noted, not built on)

- GET /v1/static/{images,videos,audio,html} read a client-supplied absolute path filtered only by mime
  type; the screener records this as a separate file-read surface, so it is not part of the tests.
- The legacy HTTP API has no authentication; the published commit's serve-bind default change is an
  exposure default, not a check, and is included in the oracle only for fidelity (no test depends on it).
- download_agent_from_radient builds a temporary zip path from the caller-supplied hub id; over HTTP a
  path parameter cannot carry a separator and the CLI caller is the same local user.

## Gate results (one stage at a time; re-run green after the host Docker outage)

The shared VM's Docker daemon was wedged under load during the first attempts (`docker info`
hung). Stages were first run green against a task-private dockerd; after the operator fixed and
restarted the system daemon, every stage was re-run green on the system Docker (task files
unchanged; private dockers stopped, none started afterwards). A harness background-timeout and two
`--only`/full attempts were cut by the outage before writing results; no task defect was involved.

- static: PASS (only the blind pass patch and FAIRNESS.md are absent, as expected).
- nop: PASS - security 36/36 fail on the pinned+injected tree, functional 108/108 pass
  (12 hidden + 96 project tests from pristine copies).
- oracle: PASS - 3 runs, reward 1.0 each, identical results.
- patches: PASS - all 13 checks behaved as declared:
  sec_miss_archive 1 security failure (reward 0.9722); sec_miss_stored 2 (0.9444); sec_miss_legacy 2
  (0.9444); sec_miss_preview 1 (0.9722); sec_miss_edit 15 (0.5833); crash_as_refusal 3 (0.9167);
  check_after_adjustment 2 (0.9444); malformed_identity 1 (0.9722); reads_only 16 (0.5556);
  func_overbroad 1 functional failure (0.0, the verbatim display name); refuse_all 9 functional
  failures (0.0); hardening 1.0; alt_fix 1.0.

Full gate run (all four stages in one `gate.py local-operator-ds` invocation, system Docker):
static, nop, oracle and patches all ok; build/local-operator-ds/gate_report.json has
verdict "pass", passed true. The run needed an egress-probe retry at start (the known shared-VM
flake) but completed without further retries.
