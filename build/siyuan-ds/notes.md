# Build notes: siyuan-ds

- Start (UTC): 2026-10-18 19:33
- End (UTC): (filled at the end)

## Advisory / commits
GHSA-FGMR-7W36-9QFQ / CVE-2026-72796 / GO-2026-6423 — siyuan-note/siyuan.
CWE-862 missing authorization on the alternate static-file channel: in publish
mode a reader reaches kernel static routes that only run the authentication
middleware, not the publish access rules the REST API applies.
Pinned (vulnerable) commit verified: `fd6d23d7bbe84da9f24286e7485453ca84831f48`
(parent of fix `34be6c0bb0739d5b8e99ecc0cbfb474abb16230d`, checked with
`git log --format='%H %P'`). Track INJECTED. Pattern A+B.

## Mechanism (one line)
A publish reader (RoleReader injected by the publish proxy for every proxied
request) reaches `/templates/`, `/export/`, `/widgets/`, `/plugins/`,
`/emojis/`, `/snippets/` through handlers whose only guard is CheckAuth, so
files the owner excluded from publishing are served. The published fix adds an
admin gate, per-resource publish rules, a document-reference producer
(widget/emoji only when a readable document uses them), and safe static file
serving (traversal, symlink, index.html, HEAD).

## Levers (planned)
- T1 (A, main, producer off the check path): widgets + custom emojis. A reader
  may fetch a widget package / emoji file only when (a) the package is not
  publish-disabled / enabled, and (b) a document the reader can access
  references `/widgets/<pkg>/...` or `/emojis/<path>`. The reference mapper has
  to be built from document trees, snippets from widget/iframe/HTML nodes,
  root-relative and absolute loopback URLs, HTML block nodes, HTML-escaped
  attribute values and nested emoji subdirectories; external hosts ignored.
  Only documents the visitor can read contribute references. Dismiss: no publish flag on emojis; the per-document relationship is
  easy to overlook, and blanket denial breaks published pages.
- T2 (A, far site, alternate content class): snippets. Publish-enabled named
  snippets stay readable; publish-disabled ones and every file found only on
  disk (not in conf.json) must be refused to readers; admins keep both.
  Dismiss: a disk-only file has no flag to check, so "the toggle does not
  apply", and the fallback is a second code path.
- T3 (A, unchanged surface with its own logic): templates and export
  artifacts are administrator-only, including `/export/temp/` and HEAD.
  Dismiss: no publish flag applies to them and the export handler has its own
  decoding/encryption logic that looks unrelated.
- T4 (A, neighbouring resource class): plugins. A reader may fetch an
  installed, enabled plugin package unless it is publish-disabled; disabled
  (unloaded) plugins and publish-disabled plugins are refused. Dismiss:
  "published pages need plugin JS" plus the petals/installed-package state.
- T5 (shapes): wildcard traversal, nested symlink escape (blocked), top-level
  symlinked package dir (allowed), directory -> index.html, HEAD. Covered by
  the access-decision tests of T1/T2.
- B1 (pattern B, uncovered route): `POST /api/bazaar/getInstalledPlugin`,
  `getInstalledWidget`, `getInstalledTemplate` list publish-disabled /
  unreferenced / template packages to readers. Dismiss: marketplace metadata
  API, not a static-file route, different package.
- B2 (pattern B, uncovered route): `POST /api/system/getEmojiConf` lists every
  custom emoji to readers, including ones no readable document references.
  Dismiss: "the picker needs it; names only"; present in current upstream.
- S1 (injected sibling): `GET /publish-preview/*filepath`, a reader-facing
  workspace-relative resolver used by the publish preview pane, CheckAuth only,
  serves from the data directory. Dismiss: the name looks publish-related, so a
  solver assumes it is already guarded, and it is a different function.
- S2 (injected sibling): `GET /snippet-preview?name=&type=`, a settings/editor
  preview helper that returns snippet content by name/type with CheckAuth only
  and ignores the publish toggle. Dismiss: query-param preview helper, not a
  static path; a solver patches only the snippet static route.

Distinct reasons to skip: producer/per-document mapping; no flag on a
filesystem fallback; no flag at all for templates/exports; plugin state;
marketplace metadata API; appearance names-only API; looks-publish-related
resolver; non-static preview helper.

## Coupled must-keep-working behaviour
Published pages keep loading referenced widgets and custom emojis,
publish-enabled snippets, enabled plugins; directory requests still return
index.html; a top-level symlinked package directory still serves; admins keep
templates, exports (including temp), disk-only snippets, all plugins/widgets/
emojis, and the unfiltered listings; readers keep receiving the resources that
are published to them through the reader-facing preview endpoints.

## Tests planned
Go tests in the product packages (server, api, model) copied in by test.sh:
- security: templates, export (plain + temp + HEAD), widgets (unreferenced,
  publish-disabled, nested symlink escape), emojis (unreferenced incl. subdir),
  plugins (publish-disabled, unloaded), snippets (publish-disabled, disk-only),
  bazaar listings (plugin/widget/template), emoji conf, publish-preview,
  snippet-preview, traversal shape.
- functional: all the coupled behaviour above plus the project's own
  `serve_assets_test.go`, `serve_svg_test.go`, `publish_access_test.go` and the
  other untouched model/api tests for the area.
Fixtures: temp data/temp/snippets/appearance dirs, real block-tree DB via
treenode.InitBlockTree, real .sy trees through filesys.WriteTree, plugin/
widget/template JSON packages, petal storage, publishAccess.json. Role is
injected on the gin context exactly as the project's serve tests and the publish
proxy do.

## Open questions / to verify
- Bazaar listing offline behaviour (util.IsOnline probe) — the first listing call
  takes ~1.3 s on an offline host; deterministic enough, and the tests never
  depend on the online result.
- Whether the templates listing must be empty for readers: yes, and the
  instruction now states that templates and exports have no publish mechanism;
  the fixture's template package is also marked excluded so both readings agree.

## Verification (local, before the gate)
- Pinned commit: `git log --format='%H %P'` confirmed the parent relation.
- Flaw reproduces at pinned through each tested entry point (reader role on the
  gin context, the same role the publish proxy injects): template, export and
  temp export 200; unreferenced/enabled widgets 200; unreferenced emoji 200;
  publish-disabled and unloaded plugins 200; publish-disabled snippet 200;
  disk-only snippet 200; nested symlink escape 200; HEAD 200; marketplace
  listings and emoji catalog expose the hidden entries; the two injected routes
  return the content.
- Oracle: all 20 security and all 14 functional task tests pass; the four
  project test groups pass on both the pinned tree and the oracle.
- Check patches: 9 security_fail (each leaves at least one security test red
  and all functional green), 1 functional_fail (over-broad admin gate breaks
  published pages), 2 pass (hardening + a structurally different alternative
  that moves the static decision to the file-serving seam). All apply with
  `patch -p1` on the injected tree and compile.
- Test fixture gotchas found and fixed: Lute's ristretto tree cache is
  asynchronous, so a hand-written document must carry an `id` IAL attribute or
  the loader takes the repair path and touches the (uninitialised) SQL index
  queue; all appended nodes now get `id`/`updated` IAL attributes. Directory
  requests and `index.html` requests behave differently (301 vs 200), so the
  tests use directory URLs where they want the index file.
- Image: golang:1.26-bookworm + python3/patch; builds in ~12 min (CGO sqlite);
  1.93 GB. Verified inside the image with `--network none`: the verifier on the
  pinned+injected tree gives security 0/16, functional 59/59 (subtests
  included), reward 0.0; after `solution/solve.sh` (fix.patch) it gives
  security 16/16, functional 59/59, reward 1.0.
- Gate: static fails only on the two items other builders supply (kind=blind
  pass patch and FAIRNESS.md); nop PASSED (16 security tests all fail on the
  vulnerable tree, 59 functional tests all pass). The first oracle run aborted
  with a Docker network race (`network ..._default not found` while another
  gate pruned networks); the rerun PASSED: three oracle trials, reward 1.0 and
  identical security/functional results in all three. Patches stage: see below.


## Fairness concerns I see
- The per-document widget/emoji rule is a design decision; it is stated as an
  invariant in instruction.md so a blind engineer can infer it, but it is the
  hardest part of the task.
- The task covers many entry points; a careful engineer needs to audit every
  route that returns resources, which the invariant tells them to do. The
  estimated fix time is above the 45-minute ideal but matches the upstream fix's
  own 75-minute estimate.
- Upstream still lists installed packages and all custom emoji to readers; the
  invariant "listings must expose only what the visitor may receive" is the
  authority for those two B levers.
- The first marketplace-listing call performs the kernel's internet probe
  (3 s timeout, two attempts offline); the tests never depend on its result.

## Out of scope (not built on)
- `/appearance/` is exempted from authentication when an access code is set and
  serves built-in appearance assets, not publish-controlled content.
- The `/export/` path decoding (`url.PathUnescape` after `TrimPrefix`) is a
  path-handling quirk unrelated to the reader check.
- Current upstream still lists installed packages and custom emoji to readers;
  the B register records the routes as present with this task's protection
  added, not as an upstream-reported issue.

## Shared-machine gate contention (no task change)
- Several gate stages ran concurrently on the same Docker daemon. Their
  per-trial `docker network prune` sometimes removed this task's freshly created
  trial network before Harbor started the sidecar ("network ..._default not
  found"). A temporary helper container of ours (`siyuan-netguard`) is attached
  to this task's trial networks for 20 s and then disconnected, so the network
  is in use when another gate prunes. It touches only `siyuan-ds__*` networks and
  no other agent's containers or images.
- Harbor's egress-control kernel probe (`docker container run` with a 30 s
  timeout) intermittently exceeded its timeout under the shared load (measured
  6 s, 16 s and 132 s for the same probe), which makes Harbor report
  `network_mode='allowlist' is not supported`. The patches stage is retried
  sequentially until a run gets through; this is infrastructure, not a test or
  patch failure.





## Fairness revision (2026-10-20)
- Blocking ambiguity (FAIRNESS 5a): templates/exports have no publish mechanism.
  The instruction now says so explicitly, and `hiddentpl` in the API fixture is
  marked `disabledInPublish:true`, so the "package flag governs templates"
  reading and the "templates are never published" reading both pass.
- Instruction hints neutralised (FAIRNESS section 3): the six-class list, the
  per-class mechanisms, the impact list, the non-exhaustive-examples sentence
  and the test-facing 4xx phrasing were replaced with invariant wording.
- Role scope (U1): the invariant is narrowed to the reader; RoleVisitor is
  rejected by the auth middleware before routing, so no visitor test can fail
  on the pinned tree.
- Readable-document rule (U2): the server fixture now has a second,
  publish-disabled document referencing a widget and an emoji; both must be
  refused while the public document's resources still serve.
- Reference shapes (U3): added absolute loopback URL (NodeIFrame), HTML block,
  HTML-escaped attribute and nested emoji subdirectory references; the
  unsupported relative-path and inline-HTML claims were dropped from the
  manifest/traps text.
- Traversal (U4): the no-marker positive control now covers widgets, plugins
  and emojis as well. A 4xx security test on `%2e%2e` climbs is impossible
  because the pinned static routes already return 404/401 for those spellings
  (it would pass on the vulnerable tree and break nop). Instead a security
  test uses non-canonical spellings that the pinned tree authorizes on the
  first segment and then resolves to an unpublished package:
  `/plugins/openpkg/../hiddenpkg/index.js` and
  `/emojis/refpack/../offpack/c.png` are 200 + marker on the pinned tree and
  4xx on the oracle.
- Methods (U5): HEAD refusals added for templates, plugins and emojis (HEAD
  `/export/` is 404 on the pinned tree, so it cannot be a security test).
- Template listing (U6): status, result code and an empty package list are
  now asserted.
- Snippet type (U7): one name is configured as both an enabled `js` and a
  disabled `css` snippet; the mismatch must be refused while the enabled one
  serves.
- Check patches: `sf-miss-snippets-fallback.patch` leaves the disk-only
  snippet readable to readers and fails exactly
  `TestPubAccessFilesystemSnippetRefusedToReader`; `sf-miss-snippets.patch` is
  kept as the preview-toggle miss. `sf-miss-readable-doc.patch` collects
  widget/emoji references from every document without the readability check
  and fails exactly `TestPubAccessHiddenDocumentResourcesRefusedToReader`.
- U8-U10 were not turned into tests: they would require asserting behaviour the
  instruction does not state (unknown preview prefixes, global petal state,
  listing totals), which would risk making correct fixes fail.
- Gate on the final state: static fails only on the separately wired
  `kind=blind` pass patch (expected, per the builder brief); nop PASSED
  (20 security tests all fail, 61 functional pass); oracle PASSED in 3/3 runs
  at reward 1.0; patches PASSED, 12/12 check patches as declared.
