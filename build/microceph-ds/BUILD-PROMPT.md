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

Project root: `/home/mara/cwe-bench`. Task: `microceph-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-XG3J-C7Q4-F9PH", "CVE-2026-10720", "GO-2026-5755"]; canonical/microceph; path traversal (CWE-23) / filename identity: unvalidated name -> config/keyring file write and delete under ConfPath, including a charset-valid reserved-name collision
- Pinned (vulnerable) commit: 2688eaec23a0e6a0dd8c40de78b58c4732f7c252. Published fix: 5c2760d8fb765d670e2673d3a537b67eae4b67c6.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "19844",
 "advisory_ids": [
  "GHSA-XG3J-C7Q4-F9PH",
  "CVE-2026-10720",
  "GO-2026-5755"
 ],
 "repo": "canonical/microceph",
 "pinned_commit": "2688eaec23a0e6a0dd8c40de78b58c4732f7c252",
 "fix_commits": [
  "5c2760d8fb765d670e2673d3a537b67eae4b67c6"
 ],
 "trust_decision": {
  "summary": "Whether a caller-supplied remote name (URL path segment or JSON body Name/LocalName) is a safe single-component cluster name before it is joined with ConfPath to write, overwrite or delete <name>.conf / <name>.keyring / rbd_mirror/<name>_peer_keyring; at the pinned commit no check exists in the remote handlers, the file writer, the token writer or the DB delete helper.",
  "evidence": [
   "microceph/api/remote.go:39-50",
   "microceph/api/remote.go:140-141",
   "microceph/ceph/configwriter.go:23-29",
   "microceph/ceph/rbd_mirror.go:722-726",
   "microceph/database/remote_extras.go:88-93"
  ]
 },
 "landing_point": {
  "where": "microceph/api/remote.go:47",
  "why": "The advisory names the remote-import API; cmdRemotePut passes req.Name straight into renderConfAndKeyringFiles, which builds <name>.conf/<name>.keyring at remote.go:140-141."
 },
 "fix_sites": [
  {
   "where": "microceph/api/remote.go:47",
   "entry_point": "PUT /1.0/client/remotes/{name} (CLI `microceph remote import`; also re-sent with RenderOnly=true to every cluster member, remote.go:61-67)",
   "module_kind": "HTTP handler (landing point); adds URL-vs-body name match + LocalName check"
  },
  {
   "where": "microceph/api/remote.go:86",
   "entry_point": "GET /1.0/client/remotes/{name}",
   "module_kind": "HTTP handler (lookup only, defence in depth)"
  },
  {
   "where": "microceph/api/remote.go:105",
   "entry_point": "DELETE /1.0/client/remotes/{name} (CLI `microceph remote remove`)",
   "module_kind": "HTTP handler"
  },
  {
   "where": "microceph/database/remote_extras.go:71-93",
   "entry_point": "DELETE /1.0/client/remotes/{name} via database.DeleteRemoteDb",
   "module_kind": "database helper package (os.Remove on ConfPath/<name>.conf|.keyring)"
  },
  {
   "where": "microceph/ceph/configwriter.go:28-29",
   "entry_point": "PUT /1.0/client/remotes/{name} via ceph.NewCephConfig/NewCephKeyring(...).WriteConfig; also every other Config writer (bootstrap, adopt, rgw, nfs)",
   "module_kind": "lower-level shared file-writer API in ceph package"
  },
  {
   "where": "microceph/ceph/rbd_mirror.go:708-726",
   "entry_point": "replication enable rbd (/1.0/ops/replication/{wl}/{name}, ops_replication.go:37) -> EnablePoolMirroring -> BootstrapPeer -> writeRemotePeerToken (rbd_mirror.go:331)",
   "module_kind": "ceph replication internals, separate feature (rbd mirroring)"
  },
  {
   "where": "microceph/api/cluster.go:33",
   "entry_point": "GET /1.0/cluster (CLI `microceph cluster export`)",
   "module_kind": "HTTP handler; existing regex check only refactored to IsValidClusterName (length cap added)"
  },
  {
   "where": "microceph/constants/constants.go:92-93",
   "entry_point": "shared validator used by all the sites above",
   "module_kind": "constants/helper (regex ^[a-z0-9]+$ -> ^[a-z0-9]{1,63}$ + IsValidClusterName)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "microceph/ceph/configwriter.go:28-29 (Config.WriteConfig, shared by all generated config files); second candidate: microceph/ceph/rbd_mirror.go:708-726 (rbd-mirror peer token writer in the replication feature)"
 },
 "O3_reason_to_dismiss": "The report is about remote import, so validating names in cmdRemotePut looks complete; WriteConfig is a generic writer whose callers use constant filenames, and writeRemotePeerToken belongs to rbd replication and only receives names read back from the DB, which looks already trusted.",
 "O4_distance": {
  "files": 5,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate remote names [a-z0-9]{1,63} must still import, list, delete and mirror; `remote list` (GET without name, remoteName==\"\") must keep working (fix skips validation when empty); and WriteConfig must keep accepting plain local filenames such as ceph.conf, radosgw.conf, ganesha.conf and tmp_ceph.conf used by bootstrap/adopt/rgw/nfs. A fix that reserves too much, or that rejects configFile values with dots or rejects an empty GET name, breaks these.",
  "where": "microceph/api/remote.go:77-95; microceph/ceph/configwriter.go:55; microceph/ceph/configwriter.go:115; microceph/ceph/configwriter.go:130; microceph/cmd/microcephd/adopt_bootstrapper.go:78"
 },
 "O6_input_shapes": [
  "traversal in body Name (../x, a/b) -> conf/keyring written outside ConfPath (fix.diff:99-103)",
  "URL {name} differs from body Name (identity differential: PUT writes body name, DELETE removes URL name) (fix.diff:105-107)",
  "traversal or newline in LocalName, which is interpolated into keyring section header and config key lookup (fix.diff:109-111; microceph/api/remote.go:162-163)",
  "charset-valid reserved names ceph / ganesha / radosgw that collide with the local cluster's own ConfPath files (fix.diff:80-94)",
  "over-length names >63 chars (fix.diff:304)",
  "empty name (rejected on PUT/DELETE, allowed on list GET) (fix.diff:54-59)",
  "absolute path or subdir as configFile at the writer layer (fix.diff:201)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "Remote names persisted by database.PersistRemoteDb (microceph/database/remote_extras.go:17-20) are read back by GetRemoteDb and passed to writeRemotePeerToken (microceph/ceph/replication_rbd.go:127-138); this is a DB round trip, not a schema or serializer producer",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "peerBootstrapImport builds ConfPath/rbd_mirror/<cluster>_peer_keyring from the remote name without validation; the fix guards only the writer, not this reader",
   "where": "microceph/ceph/rbd_mirror.go:581-589",
   "reason_to_dismiss": "Read-only path handed to the rbd CLI, and the name comes from a DB row already validated on import.",
   "distance": "ceph package, rbd_mirror.go; 2 packages away from api/remote.go",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Remote names stored before upgrade are loaded from the DB and passed unvalidated as --cluster to rbd/ceph (resolved by ceph to <cluster>.conf) in rbd and cephfs replication",
   "where": "microceph/ceph/cephfs_snapshot.go:49-55",
   "reason_to_dismiss": "The value is a CLI argument to an external tool, not a file path microceph opens, and new rows are validated on PUT.",
   "distance": "ceph package, replication_cephfs.go/cephfs_snapshot.go",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "microceph/ceph/rbd_mirror.go:581-586",
   "sibling": "make peerBootstrapImport (or a cephfs peer-token equivalent) write or clean up its own per-remote token file",
   "why_realistic": "Mirrors writeRemotePeerToken; a maintainer adding token cleanup on disable would naturally reuse the same fmt.Sprintf name pattern."
  },
  {
   "where": "microceph/ceph/replication_rbd.go:152-160",
   "sibling": "rbd disable removes ConfPath/rbd_mirror/<remote>_peer_keyring with os.Remove",
   "why_realistic": "Disable pairs naturally with the token write in enable; the name comes from the DB record and looks trusted."
  },
  {
   "where": "microceph/cmd/microcephd/adopt_bootstrapper.go:238-242",
   "sibling": "temp conf/keyring file names derived from a user-supplied cluster/adopt name instead of constants",
   "why_realistic": "Uses raw fmt.Sprintf(\"%s/%s\") with os.Remove, so a parametrised name would bypass WriteConfig's new guard on the cleanup side."
  }
 ],
 "O9_family": "path traversal (CWE-23) / filename identity: unvalidated name -> config/keyring file write and delete under ConfPath, including a charset-valid reserved-name collision",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "Go 1.25.10 (microceph/go.mod:3); microcluster v3 with go-dqlite v3 (cgo + libdqlite/raft likely needed to compile the api and database packages)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "microceph/ceph/configwriter_test.go (suite using tests/testutils.go temp SNAP_DATA); the fix adds microceph/api/remote_test.go (unit tests of validateRemoteName/validateRemoteImportRequest). Handlers use DB/ceph mocks via package vars (database.GetRemoteDb/DeleteRemoteDb are vars, common.ProcessExec)."
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "microceph/api/remote.go, microceph/api/cluster.go, microceph/ceph/configwriter.go, microceph/ceph/rbd_mirror.go, microceph/database/remote_extras.go, microceph/constants/constants.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Copy the cluster.go regex check onto req.Name in cmdRemotePut only, which leaves the reserved names (ceph/radosgw overwriting the local cluster's own conf/keyring), the URL-vs-body mismatch, LocalName, DELETE/DeleteRemoteDb, the WriteConfig layer and the rbd-mirror token writer open."
 },
 "out_of_scope_notes": [
  "Remote token config values (fsid, mon.host.*, public_network, key) are rendered unescaped into ceph.conf/keyring templates (microceph/api/remote.go:145-166); newline/directive injection is a different property.",
  "clientServiceInit builds a symlink path from service name and hostname (microceph/ceph/service_placement_client.go:72-75); the names come from the service registry and cluster state, so this is not in scope."
 ],
 "unverified": [
  "Repo size in MB not measured (no shell used); tiny_repo/giant_repo not assessed but the repo is clearly mid-sized.",
  "Whether the api package unit tests compile offline without libdqlite headers (cgo) was not checked.",
  "No latest release was given, so present_in_latest is unknown for both O8 routes.",
  "Exact HTTP prefix for remote routes (/1.0 under ExtendedPathPrefix) was inferred from microceph/client/remote.go:19, not read from the router.",
  "Whether rbd/ceph CLIs resolve --cluster <name> to ConfPath/<name>.conf in the snap was not verified."
 ]
}
  ```
- Published fix sites:   - microceph/api/remote.go:47 — entry point: PUT /1.0/client/remotes/{name} (CLI `microceph remote import`; also re-sent with RenderOnly=true to every cluster member, remote.go:61-67) [HTTP handler (landing point); adds URL-vs-body name match + LocalName check]
  - microceph/api/remote.go:86 — entry point: GET /1.0/client/remotes/{name} [HTTP handler (lookup only, defence in depth)]
  - microceph/api/remote.go:105 — entry point: DELETE /1.0/client/remotes/{name} (CLI `microceph remote remove`) [HTTP handler]
  - microceph/database/remote_extras.go:71-93 — entry point: DELETE /1.0/client/remotes/{name} via database.DeleteRemoteDb [database helper package (os.Remove on ConfPath/<name>.conf|.keyring)]
  - microceph/ceph/configwriter.go:28-29 — entry point: PUT /1.0/client/remotes/{name} via ceph.NewCephConfig/NewCephKeyring(...).WriteConfig; also every other Config writer (bootstrap, adopt, rgw, nfs) [lower-level shared file-writer API in ceph package]
  - microceph/ceph/rbd_mirror.go:708-726 — entry point: replication enable rbd (/1.0/ops/replication/{wl}/{name}, ops_replication.go:37) -> EnablePoolMirroring -> BootstrapPeer -> writeRemotePeerToken (rbd_mirror.go:331) [ceph replication internals, separate feature (rbd mirroring)]
  - microceph/api/cluster.go:33 — entry point: GET /1.0/cluster (CLI `microceph cluster export`) [HTTP handler; existing regex check only refactored to IsValidClusterName (length cap added)]
  - microceph/constants/constants.go:92-93 — entry point: shared validator used by all the sites above [constants/helper (regex ^[a-z0-9]+$ -> ^[a-z0-9]{1,63}$ + IsValidClusterName)]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

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

## Environment (`tasks/microceph-ds/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/microceph-ds/instruction.md`)
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

## Tests (`tasks/microceph-ds/tests/`)
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
- **Wrong-fix patches** go in `build/microceph-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/microceph-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/microceph-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/microceph-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py microceph-ds --only static
python3 -I builder/gate.py microceph-ds --only nop
python3 -I builder/gate.py microceph-ds --only oracle
python3 -I builder/gate.py microceph-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/microceph-ds/`;
  - edit only `tasks/microceph-ds/`, `build/microceph-ds/` and, for pattern B, the register;
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
