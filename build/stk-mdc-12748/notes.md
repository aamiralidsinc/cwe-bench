# stk-mdc-12748 build notes

- Start (pipeline): 2026-10-26T02:25:04Z. Builder work: 02:27Z.
- End: <filled after the gate>

## Task

Repo `nuxt-content/mdc`, pinned at `d6e5fc6001085f2d34b905ba0407a2f7392de388` (the direct parent
of the advisory's published fix `61d636c2983f021288e4fc5c4006733b38cf0d53`). Advisory 12748
(GHSA-MXM6-V9R6-R94C / CVE-2026-63671): a URL-scheme deny-list that misses inline `data:` documents
and the SVG link attribute. One protection, four independent concepts, plus one coupled must-keep.

## Levers (one line each)

- T1 (both, advisory route): `src/runtime/parser/utils/props.ts:33` compares the refuse-list with
  `url.protocol` (scheme only) so `data:text/html,...` passes; reason to dismiss: the list already
  carries six `data:` entries and an inline document has no useful origin.
- T3 (both, the published fix's second site): `src/runtime/parser/utils/props.ts:45,50` and
  `src/runtime/components/MDCRenderer.vue:345` check only `href`/`src`, while the SVG link attribute
  arrives as `xLinkHref`; reason to dismiss: SVG xlink is legacy and the property name is not the
  attribute name.
- T4 (deepseek, uncovered upstream): `src/runtime/parser/utils/props.ts:44-51,68-73` and
  `src/runtime/components/MDCRenderer.vue:341-343,399-403` keep binding-prefixed props, which the
  renderer resolves; reason to dismiss: a `:href` value is a data expression, not a raw attribute.
- T6 (deepseek, uncovered upstream): `src/runtime/components/MDCRenderer.vue:211,315-356` (also
  reached through `MDC.vue:87-89` and `MDCCached.vue:101-104`) maps an already-parsed body's props
  to DOM attributes with no re-check; reason to dismiss: the body came from `parseMarkdown`.
- T2 (mimo, coupled must-keep): blocking the whole `data:` scheme would remove legitimate inline
  raster image sources; the functional suite keeps them honest.

## Concepts

`[T1,T2]`, `[T3]`, `[T4]`, `[T6]` — 4 independent edit sites in the reference fix (verdict on the
whole-URL comparison, the checked-name set, binding-prefix normalisation, and the render boundary).

## Verified on the pinned tree (local, Node 20.19.2 + pnpm 11.5.2)

- Dependency install, module prepare and module build; 23 project test files / 51 tests pass.
- Pinned: 9/9 hidden security tests fail, 10/10 hidden functional and 16/16 project tests pass.
- Reference fix: 9/9 security, 10/10 hidden functional, 16/16 project.
- Each miss patch leaves exactly its own concept failing (miss_scheme 5 security failing,
  miss_xlink 2, miss_binding 2, miss_render_boundary 2) with every functional test passing.
- The published fix alone leaves the 2 binding and 2 already-parsed-document tests failing.
- refuse_all and overblock_data are functional_fail; crash_as_refusal is security_fail; the
  hardening and alternative designs score 1.0.
- Control task: 4/4 security fail pinned; its own reference 4/4; incomplete 2 security failing with
  functional green; refuse_all/overblock/crash functional_fail; hardening passes.

## Could not verify / unknowns

- The container gate results are recorded below once run. The shared VM was under load averages of
  85-95 with hundreds of concurrent containers, so builds and trials were slow; nothing about the
  task was changed to accommodate that.
- The first nop attempt failed in the environment image build: `pnpm@11.5.2` needs Node >= 22.13
  (`node:sqlite`), so both images were moved from `node:20-bookworm-slim` to
  `node:22-bookworm-slim`. The dependency install and module build are the same otherwise.
- The in-repo expectation that `data:image/*` sources keep working is a web-platform expectation:
  no project fixture uses one, but the library's predicate allows it today and must keep doing so.
- Upstream `origin/main` (98ba158b26e76a37deeafaeccd977e9fb388eed7) still has no render-boundary
  check (T6), while the binding-prefix route (T4) was later fixed upstream by 461ec3e7 (#496).
- The generic build prompt says the repo goes in `/app`; the frontier conformance machinery requires
  `/workspace`, so the task uses `/workspace` like the rest of the batch.

## Pattern B register

Two rows appended to `build/audit/uncovered-routes.tsv` for T4 (present in latest: no; fixed by a
later upstream commit) and T6 (present in latest: yes), both `real_upstream=yes`,
`in_current_scope=yes (B)`, `built`, `disclosure_status=pending client decision`.

## Gate

<filled after the gate>
