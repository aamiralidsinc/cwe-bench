# indico-ds — build notes

Start: 2026-10-24T04:59:42Z (pipeline) / design work 05:00Z
Advisory: GHSA-C4WC-GGRJ-JG9V / CVE-2026-107396 (indico/indico)
Pinned: 3c69cba9b1d1dc7ae46e289ae39403597583ec3d
Fix: d4c8c7127176efa4cb53c64119ca8ee2b551be18
Pattern: A. Track: injected.

## What the published fix actually does (verified from the diff)

- attachment link add/edit form: `URLField(..., [DataRequired()])` -> `[DataRequired(), URL()]`
- menu link form: same one-validator addition
- `IndicoLinkListField.pre_validate`: every `url` element must start with `http://`/`https://`
- `EventNoteSchema` / `CompiledEventNoteSchema`: `@post_dump` -> `sanitize_html(data['html'])`
- new project test: pure schema dump (absent at the pinned commit, so no leaked regression test)

`wtforms.validators.URL()` (3.2.1) only requires `^[a-z]+://` plus a valid hostname. It rejects
`javascript:alert(1)`, `data:text/html,...`, `vbscript:...`, but accepts `javascript://host/%0a...`.
Hidden tests therefore use the plain scheme form, never the `://` bypass (the oracle would fail it).

## Security properties (written once, general; no route names)

P1 (link targets): a target a user supplies must never be one that executes code when opened.
Code-executing schemes (e.g. `javascript:`) must not be kept or handed back to any client; ordinary
`http`/`https` addresses keep working.

P2 (stored rich text): rich text one user saves must never be handed to another user/client with
markup that can execute (script elements, event-handler attributes, script-bearing link targets);
ordinary formatting/media/links are kept. The author's raw text round-trips exactly so editing is
lossless.

## Levers (each with its own reason to skip)

### L1 — HOW, main: note HTML sanitized at every delivery; raw source must survive
Where: `indico/modules/events/notes/schemas.py` (editor API single dump, conflict dump,
`many=True` compile dump).
Shape: one object vs a list of objects; `html` must be sanitized while `source` is byte-identical.
Why dismissed: the HTML display page already calls `sanitize_html`, so the JSON editor API looks
like an internal, already-safe consumer; blanket-sanitizing the whole payload (including `source`)
looks tidy but destroys editing.
Coupled must-keep-working: raw source round-trip, allowed markup (`<img src>`, `<b>`, safe links)
kept, existing safe content delivered unchanged.

### L2 — HOW, Pattern A far site: the second producer of note HTML
Where: `indico/modules/events/notes/util.py::build_note_api_data` (real, unmodified upstream),
delivered by the legacy HTTP export `/export/note/<event>.json` (also reused by the event export).
Why dismissed: "the editor JSON API is where note HTML is handed to a browser; the export is for
external integrations". The published fix never touches it. Verified live: at the pinned commit the
export returns `"html":"<img src=x onerror=alert(1)>"` to an unauthenticated-capable client.
Why HOW: the check (schema) never calls this producer; the fix needs the extra producer understood.

### L3 — HOW, shape + lower-level API: generic link-list field
Where: `indico/web/forms/fields/simple.py::IndicoLinkListField` (real fix site) feeding
`EventPrivacyForm` and the public event page links.
Shape: a JSON list of `{title,url}`; every element must be checked; a one-element list has its
title blanked by `process_formdata`, so a title-based or first-element check mishandles it.
Why dismissed: it is generic form-library code in `indico/web` and is not a `URLField`, so a grep
for the reported field pattern misses it.

### L4 — where-type, Pattern A far site: menu links
Where: `indico/modules/events/layout/forms.py::MenuLinkForm.link_url` (real fix site), add and edit
routes; href rendered in the event navigation.
Why dismissed: "the report example is a material link; the navigation menu is another feature".

### L5 — landing point: attachment links
Where: `indico/modules/attachments/forms.py::AttachmentLinkFormMixin.link_url`; add + edit, event
and category routes.

### I1 — injected (P1), URL field that lost its guard
Where: `indico/modules/events/management/forms.py::EventLocationForm.own_map_url` — injected as
`URLField(_('Map URL'), [Optional()])`; rendered as the event's map href.
Why dismissed: it is a location setting, not one of the reported "custom link" fields.

### I2 — injected (P1), link stored in settings, not a URL field
Where: injected `website_url` on `ConferenceLayoutForm` + `layout_settings`, rendered as an anchor
in the conference header. Plain string field, no `URLField` to grep for.
Why dismissed: layout/appearance settings do not look like link input.

## Candidate list (all found; why each was picked or dropped)

- `build_note_api_data` export (notes/util.py; NoteExportHook + events/api.py) — PICKED (L2).
  Real unmodified upstream, second producer, verified live.
- event export note fields (events/api.py:311,361,399,600) — same producer as L2; covered by fixing
  it; no independent test.
- conflict response `html=render_note(submitted source)` (notes/util.py:101) — the submitter's own
  input (self-XSS); screener dismissed; not covered (would need sanitizing the author's own echo).
- event/category cloning copies stored `link_url` (layout/clone.py:68, attachments/clone.py:102) —
  copies already-validated data; after a correct fix no bad value can exist; not independently
  reachable; dropped.
- `ReferenceType.url_template` / `scheme` (events/forms.py:37) — admin-only configuration with
  deliberate non-http schemes; out of scope.
- room-booking `map_url_template` (rb/schemas.py) — admin-only and already scheme-restricted.
- user `mastodon_server_url` — has a dedicated validator and is used in share JS, not href.
- legal terms/privacy URLs — admin-only, already `URL()`-validated.
- event page HTML (`page.html|sanitize_html` at its one delivery) — no JSON delivery; a new
  page-content endpoint would be a planted route without a consumer; dropped.
- papers/editing `html` schemas — different product features, outside this advisory; not built on.
- `own_map_url` (already `URL()` upstream) — INJECTED as I1 (guard removed; pre-fix pattern).
- layout `website_url` — INJECTED as I2 (new realistic link surface in settings + header).

## Sites / routes / shapes the hidden tests cover

P1: attachment add (event), attachment edit (event), attachment add (category), menu add, menu
edit, privacy link list single-element, privacy link list multi with one bad element, own map URL,
layout website URL.
P2: editor API GET, editor API POST response, conflict response (`conflict.html`), compiled list
(`many=True`), legacy note export.

## Coupled must-keep-working (functional)

- http/https add + edit for attachments and menu entries keep working and are stored/rendered.
- multi-link list with titles stored intact; single link works; privacy text still saved.
- map URL and website URL keep working with ordinary https.
- note raw source round-trips byte-identically; allowed markup (img src, strong, safe anchor) kept
  in delivered html; compile and conflict still work; export still returns the note fields.
- project's own tests: notes models, layout menu models, attachments util.

## Verification plan

- Confirm every security test fails on the pinned+injected tree (nop) and passes with fix.patch.
- Confirm functional tests pass on both.
- Wrong-fix patches: one per lever (security_fail), an over-broad functional_fail, a hardening pass,
  an alternative-design pass, plus catalogue patches (refuse_all, crash_as_refusal, add-only).
- Test stack: real Flask app via indico's pytest fixtures (PostgreSQL + redis, offline, uid 1000),
  HTTP entry points through `test_client`, side effects read from the DB/settings.

## Local verification (before the Docker gate)

Stack: the project's own pytest fixtures (real Flask app, temporary PostgreSQL 17 cluster,
temporary redis-server), tests driving the real HTTP entry points with `test_client`, run as
uid 1004 locally and as uid 1000 in the verifier image.

| tree | security | functional (hidden) | project tests |
|---|---|---|---|
| pinned + injection (nop) | 14 failed | 9 passed | 20 passed |
| injection + solution/fix.patch (oracle) | 14 passed | 9 passed | 20 passed |
| checks/harden.patch (pass/hardening) | 14 passed | 9 passed | 20 passed |
| checks/alternative.patch (pass/alternative) | 14 passed | 9 passed | 20 passed |

Wrong-fix variants (each matched its declared expectation in the local matrix):
miss_attach (3 security fail), miss_menu (2), miss_list (2), miss_schema (4), miss_export (1),
miss_map (1), miss_website (1), add_only (1), crash_as_refusal (3), refuse_all (1 functional fail),
overbroad_sanitize (3 functional fail).

Two transient "N errors" runs were seen while looping 26 pytest processes back to back on the
shared VM (the local postgres/redis fixture startup, not the task); each reran clean. The verifier
runs only three pytest processes per trial in a fresh container.

## Pattern B register

One real uncovered route was found and built on: the legacy note export producer
(`build_note_api_data`), still unsanitized on upstream master 803665a. Row appended to
build/audit/uncovered-routes.tsv. No other real route was built on (dismissed candidates are
listed above).

## Docker gate (system daemon)

The first attempts hit the host Docker outage (the system daemon wedged under ~40 concurrent
Harbor builds; a task-private dockerd was used temporarily, then shut down when the operator
fixed and restarted the system daemon). Final numbers below are from the system daemon.

- static: PASSED
- nop: PASSED - 14/14 security tests fail on the pinned+injected tree, 29/29 functional pass
  (9 hidden + 20 project).
- oracle: PASSED - 3 runs, reward 1.0, identical results.
- patches: see the final line below.

One oracle attempt hit the documented startup egress-probe flake
("network_mode='allowlist' is not supported by requested network policy", the 30 s probe
timing out under the shared VM's load). The stage was re-run unchanged; task.toml was not
weakened.

## End

- patches: PASSED - all 13 checks matched their declared expectation:
  security_fail: miss_attach (3 sec fail), miss_menu (2), miss_list (2), miss_schema (4),
  miss_export (1), miss_map (1), miss_website (1), add_only (1), crash_as_refusal (3);
  functional_fail: refuse_all (1 fun fail), overbroad_sanitize (3 fun fail);
  pass: harden (reward 1.0), alternative (reward 1.0).
  (The blind patch is supplied later by the blind-fix run; it is listed in patch_checks and is
  skipped while absent, as the brief allows.)

Final: static PASS, nop PASS, oracle PASS, patches PASS.
End: 2026-10-24T09:53Z.

