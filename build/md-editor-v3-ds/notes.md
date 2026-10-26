# md-editor-v3-ds build notes

- Start (UTC): 2026-10-24T05:01Z (pipeline start)
- End (UTC): TBD

Advisory: GHSA-3RM2-H79C-8QW6 / CVE-2026-84992 (imzbf/md-editor-v3). Pinned
`bea48ec0ba51c19deda9486eb06050b5b8f50b51`, published fix
`2c07360420e74087f5bc63032ab155d93e0a0b10` (3 files, no tests). Track: injected, pattern A+B.

## Levers (one line each)

- T1 (reported site): fence info string interpolated into a quoted class attribute and an unquoted
  language attribute in the highlight callback (`useMarkdownIt.ts:206`), and the tab-group branch
  feeds the same value; escaping only the class or only one renderer branch leaves the other open.
- T2 (published-fix far site): the configured copy label is written into `data-tips` (single and
  tab-group branches) and into the element body of the copy control (`code/index.ts:73-74,98,185`);
  reason to dismiss: application configuration, not document content.
- T3 (published-fix far site, other module): the same texts are written again after a click with
  `innerHTML` for the result and for the timer-restored label (`useCopyCode.ts:48,55`); reason to
  dismiss: post-render event wiring, and the generated markup was already fixed.
- T4 (main, how-type): the instance identifier lands in id/name/for/class attributes *and* inside
  the inline `onclick` script expression and its CSS selector (`code/index.ts:135-170`). HTML
  escaping is decoded by the parser before the script engine runs, so escaping does not fix it; the
  value has to be reduced to a safe DOM segment (or the handler removed). Reason to dismiss: the
  identifier is application-supplied and the branch is a code-block variant the report never shows.
- T5 (pattern B, protection never existed): when the optional math engine instance is not loaded,
  the math token source is interpolated raw into the preview element (`katex/index.ts:211`); math
  tokens are not html tokens, so the optional token-level filter never sees them. Reason to
  dismiss: neighbouring feature and a transient fallback. Real, unmodified upstream code; the
  published fix does not touch it. Latest upstream now escapes it (checked read-only), so
  present_in_latest=no.
- T6 (injected sibling): the callout kind is interpolated raw into a template attribute next to a
  class written through `renderAttrs` (`admonition/index.ts:35`). Reason to dismiss: callout kinds
  read as a fixed vocabulary and the neighbouring line shows the value being handled.
- T7 (injected sibling): the diagram source is interpolated raw into a `data-content` attribute of
  the fallback while the visible body next to it is escaped (`mermaid/index.ts:34`). Reason to
  dismiss: the visible source is escaped and the attribute reads as inert data.

## Sites / test files

- security: 14 tests in 7 files (`tests/security/*.test.ts`), one per site/route/shape.
- functional: 14 tests in 5 files (`tests/functional/*.test.ts`), including the coupled values:
  c++/c# language classes, highlighter markup, configured copy label and icon, click feedback and
  restore, cross-instance independence and tab switching, rendered formula markup, unrendered
  formula text, callout rendering, diagram source display, ordinary markdown.
- Entry point: `MdPreview` mounted with `modelValue` plus public props (`editorId`, `language`,
  `customIcon`, `formatCopiedText`, `no*`) and public config (`config({editorConfig})`,
  `globalConfig.editorExtensions.*.instance`). The copy test performs a real click.

## Verified

- Runner: Vitest 3.2.7 + jsdom 26.1.0, product source imported through `~`/`~~` aliases and
  compiled by `@vitejs/plugin-vue-jsx`; exact verifier command exercised locally.
- Pinned+injected: 14/14 security fail, 14/14 functional pass.
- Oracle (`solution/fix.patch` = published fix reduced to source + sibling/route fixes): 14/14
  security pass, 14/14 functional pass.
- Every `checks/` patch was applied to a clean injected tree and given the two suites; results are
  recorded in the gate `patches` stage (see manifest).
- The injected tree is the pinned commit plus `environment/injection.patch` (two sibling renderers,
  no other change); the verifier ships the plain pinned dependency tree and the submission supplies
  the injected/fixed sources.
- The pinned tree contains no test/spec files and no test script, so there are no project tests to
  run; `git log bea48ec..2c07360` contains only the fix commit and no regression tests.


## Wrong-fix / alternative checks (run locally against the exact suites)

- `sf-miss-fence`: 11/14 security pass (3 fence tests fail), functional 14/14.
- `sf-miss-copytips`: 11/14 (3 copy-label tests fail), functional 14/14.
- `sf-miss-clicktips`: 12/14 (2 click-time tests fail), functional 14/14.
- `sf-miss-editorid`: 13/14 (the script-execution test fails; the attribute test still passes —
  this is the how-type trap: HTML-escaping the identifier satisfies the attribute shape and fails
  the script context), functional 14/14.
- `sf-miss-katex`: 12/14 (2 formula tests fail), functional 14/14.
- `sf-miss-admonition`: 13/14, functional 14/14.
- `sf-miss-mermaid`: 13/14, functional 14/14.
- `sf-reported-only` (reported site only): 3/14, functional 14/14.
- `ff-escape-all` (over-broad): security 14/14, functional 11/14 (copy icon and c++/c# classes).
- `pass-alt` (sanitise at the source and hash the identifier): 14/14 + 14/14.
- `pass-hardening` (oracle plus boundary hardening): 14/14 + 14/14.

## Could not verify

- The advisory text itself was not available; the scope (which values the advisory intends) is
  taken from the published diff and the screener record.
- Whether the published advisory classifies the math fallback and the copy text/identifier routes
  as in scope; the task's property covers them explicitly so they are judged by the property.
- Repository size in MB was not measured.
- `present_in_latest` for the two injected siblings is n/a (they exist only in our copy).

## Out of scope (noted, not built on)

- The preview is constructed with `html: true` and the default `sanitize` prop is the identity, so
  raw HTML in a document passes unless the integrator configures a sanitizer or the optional XSS
  plugin; that is a documented design choice, not part of this advisory.
- The echarts extension's default option parser evaluates the block source with `new Function`
  (documented as something an integrator must override for untrusted content); not pursued.
- `useMermaid` writes `sanitizeMermaid` output through `innerHTML` and the default is the
  identity; not pursued (neighbouring route, integrator-configurable).
- `extraTools` returns integrator HTML by design; the published fix leaves it unchanged and so
  does this task.

## Environment incidents (shared VM)

- 2026-10-24T05:45Z: the host's /tmp tmpfs reached 100% inode use (other build sessions' scratch
  trees), and Docker could not create containers ("mkdir /tmp/containerd-mount...: no space left
  on device"); the first nop attempt failed as an infra error. Removing three multi-day-old
  abandoned scratch trees under /tmp (`ws`, `dagu-modcache`, `fakehome`) restored ~300k inodes and
  the stage was retried unchanged.
- 2026-10-24T06:00Z: the main Docker daemon then wedged: `/_ping` answered but `/containers/json`
  and `docker info` hung, so the verifier image build never started. Following the documented
  shared-VM workaround, a task-private dockerd was started on `unix://build/md-editor-v3-ds/priv-docker/docker.sock`
  (bridge 10.78.0.1/16 outside the compose pool 10.77.0.0/16, host DNS overridden) with node:22-bookworm-slim,
  alpine:3.23.4 and the Harbor egress-sidecar base image pre-pulled, and the gate stages were run with
  DOCKER_HOST pointing at it.
