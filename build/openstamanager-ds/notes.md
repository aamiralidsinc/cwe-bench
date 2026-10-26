# openstamanager-ds — build notes (build-v1, pattern A+B, injected)

Start (UTC): 2026-10-24T05:16Z
End (UTC): 2026-10-24T08:53Z

## Candidate

devcode-it/openstamanager @ 57a2734e2121aa8fcd456eff7c59f03e29e69176 (vulnerable).
Published fix: 0b88ad1963871abfa5e134004ca0c74c496d8d2f (output escaping) and
7c9eafe9ffefcfd61357c81165157090e790c213 (input allowlist drops `a`, re-allowed for the e-mail
body; the same commit also carries Intervention-Image v3 API churn, unrelated).
Family: stored HTML injection, CWE-79.

## The one property (written before choosing routes)

OpenSTAManager is a PHP ERP/CRM. Groups, customer/supplier records, users, contacts and service
types are named by users and shown back on record pages and in the suggestion lists of its
search fields.

Property, as it appears in instruction.md:

> A value a user saved is text. Wherever the product displays that value to any user — on a
> record page or in any suggestion list it offers — the value must arrive as text: it must never
> be able to create or alter elements, attributes, links or script, whatever characters it
> contains. This covers values that were saved before the fix as well as values saved after it,
> and however the product reaches them.

Every security test falls under that sentence as written; the functional tests cover the rest of
the instruction (names still display, product-built links still work).

## Levers (one line each)

L1 MAIN, how-type — `src/Modules.php:316`: the shared link helper escapes the visible text but
returns the caller-supplied fallback raw, and the search-result transformer passes the stored
text as that fallback (`src/AJAX.php:326`); safe for a permitted viewer, raw for one without the
target module's permission. Reason to dismiss: it is the "you may not open this" branch of a
neighbouring feature, and the example re-run as an administrator never reaches it.

L2 shape trap — `modules/utenti/edit.php:255`: the same stored name lands in a quoted attribute
(the restore-permissions confirmation). Reason to dismiss: it reads as a tooltip next to the two
fixed lines. Verified that HTMLPurifier keeps `"` inside text, so the value can really break out.

L3 Pattern B, same file — `modules/utenti/edit.php:110-135`: member username, e-mail, type and
seats printed raw in the table. Reason to dismiss: the report is about the group name.

L4 Pattern B, another package — `modules/anagrafiche/ajax/select.php` and
`modules/interventi/ajax/select.php`: hand-built providers put the stored description back into
the displayed text after the shared mapper has escaped it. Reason to dismiss: another module.

L5 Pattern A second implementation — `src/Plugins.php:134-142`: the plugin-side link helper never
escapes and returns its fallback raw; reached through the injected contact picker. Reason to
dismiss: plugins are a separate subsystem.

T1 Pattern A far sites (where-type) — `src/AJAX.php:127` (generic mapper) and
`modules/utenti/ajax/select.php:54-61,109-116` (the module's own two providers).

Injected siblings (in `environment/injection.patch`, applied at image build):
- IS1 `modules/anagrafiche/ajax/select.php` — a new `referenti_cliente` op built by hand in
  exactly the style of the file's existing `clienti`/`fornitori` ops, with `link` set to the
  existing `plugin:` link style. This makes the (otherwise dead) plugin link branch reachable.
- IS2 `modules/utenti/edit.php` (end of file) — an inline page script that hands the stored group
  name to JavaScript as a string literal. Different context (script, not markup).

## Full candidate list and why the picks won

See the table in the design section of the task brief; in short:
- Screener leads considered: AJAX mapper (kept, T1), Modules::link visible text (fix site),
  Modules::link fallback (kept, L1), Plugins::link (kept, L5), edit.php member table (kept, L3),
  edit.php data-msg (kept, L2), anagrafiche/interventi manual providers (kept, L4),
  Filter.php allowlist (rejected: the property is about what reaches a browser; an input
  allowlist is one valid implementation, not the requirement), actions.php send-email (rejected:
  outbound mail, not a browser), select.js escapeMarkup (rejected: client-side root cause, no JS
  runtime in the verifier).
- Own search: `src/HTMLBuilder/Handler/SelectHandler.php:219` is a second copy of the link
  transformer for form selects — rejected as a route because reaching it needs a fully rendered
  add/edit form; it stays untouched and untested. ~20 hand-built `'text' =>` assignments across
  eight modules — kept as one class (L4); adding more would be "more routes of one concept".
  `modules/utenti/edit.php:124` `Modules::link('Anagrafiche', ...)` — no gap (the default
  fallback is the already-escaped visible text). Page chrome in `include/top.php`, sidebar menus
  and dashboard widgets: real raw echoes, but not reachable from a route the tests can drive
  without building a whole dashboard; not used.

Why the picks beat the others: L1 is the only how-type lever (a mechanism, not a copy); L2 is
the only attribute-context shape; L3/L4 are real unmodified upstream routes at increasing
distance (same file → another package); L5 is a real second implementation in another subsystem;
IS1/IS2 are the two sibling gaps, each with a different reason a solver would skip it.

## Sites/routes/shapes the tests cover

Entry points (real HTTP, session cookie):
- `GET editor.php?id_module=<Utenti e permessi>&id_record=<group>`
- `GET ajax_select.php?op=<resource>`

Shapes: text node, quoted attribute, JavaScript string, select2 `text` field (children included),
table cell, and a product-built `<a>` link that must keep working.

## Coupled must-keep-working (functional)
- The group page still shows the group name in both cards and still lists its member with e-mail.
- A permitted user's search answer still carries the product's own `<a>` link to the record
  (module link and plugin link), pointing at the same module and record.
- Search answers keep their select2 shape (id, text, optgroups with children).
- Ordinary values still appear.

## How the reference fix divides the work

A search answer whose items get a link is escaped by the shared link helper (both of its return
paths, and the plugin helper's own fallback); an answer with no link is escaped where the
provider builds it. That keeps the reference fix to the smallest correct change at each layer,
and it is also why `lever_link_fallback.patch` really leaves a route open: the customer picker
does not escape on its own, it relies on the helper.

## Verification performed

- The application installs from its own migrations on MySQL 8.0 (the database its docker-compose
  pins); the verifier starts from a dump taken after that install.
- Login over HTTP works; `editor.php` renders the group page; `ajax_select.php` answers JSON.
- HTMLPurifier (the product's own input filter) keeps `"`, `'`, `<img src=x>` (normalised to
  `<img src="x" alt="x" />`), `<b>`, so every payload the fixtures store is a value a user can
  have saved through the product.
- MariaDB was tried first and rejected: its `ORDER BY id` resolution rejects the module's own
  list query (error 1052), a MariaDB-only incompatibility the project itself warns about.
- All 13 patches apply cleanly to the injected tree.
- Static gate stage passes.
- Local end-to-end (image + dump + server + PHPUnit, outside Harbor): on the injected tree the
  twelve security tests all fail and the nine functional tests all pass; with the reference fix
  every test passes. Each check patch was run the same way and produced the outcome it declares
  (see the table at the end).

## Deviations / notes
- The application lives at `/workspace`, not `/app`: the delivery format only carries
  `/workspace` across to the verifier.
- The published fix's second commit also tightens the global input allowlist (`Filter.php`,
  `actions.php`). That half is a defence-in-depth input change, not the property being graded, so
  it is not part of the oracle; the oracle is the output-encoding half plus fixes for every
  route and sibling in this task.
- The published fix escapes text twice on search answers that also get a link (it escapes at the
  producer and again in the link helper). The oracle keeps that behaviour; the tests assert "no
  raw markup" rather than one exact escaping, and the functional fixtures use plain names, so a
  single-escaping fix passes just as well.
- The seed dump ships in both images (environment and verifier) because they are built from
  separate contexts; the verifier copy is compressed differently so the two files are not
  byte-identical.

## What I could not verify
- Whether any module page other than the group page would also fail on MariaDB (irrelevant now:
  the verifier uses MySQL 8).
- The client-side half of the advisory (`escapeMarkup` disabled in select.js) is real but is not
  graded: the verifier has no JavaScript runtime, so the JSON `text` field is the boundary the
  tests assert on.

## Check-patch matrix (measured, one local run each)

| patch | declared | observed |
|---|---|---|
| lever_attribute.patch | security_fail | 2 security tests fail, all functional pass |
| lever_link_fallback.patch | security_fail | 1 security test fails, all functional pass |
| lever_manual_providers.patch | security_fail | 1 security test fails, all functional pass |
| lever_member_table.patch | security_fail | 1 security test fails, all functional pass |
| lever_page_script.patch | security_fail | 2 security tests fail, all functional pass |
| lever_plugin_link.patch | security_fail | 1 security test fails, all functional pass |
| far_ajax_mapper.patch | security_fail | 1 security test fails, all functional pass |
| far_utenti_select.patch | security_fail | 2 security tests fail, all functional pass |
| overbroad_link.patch | functional_fail | every security test passes, 2 functional tests fail (the product's own links are escaped away) |
| refuse_all.patch | functional_fail | 7 functional tests fail (the suggestion lists are empty) |
| hardening.patch | pass | 12/12 security, 9/9 functional |
| alternative.patch | pass | 12/12 security, 9/9 functional |

nop: 12/12 security fail, 9/9 functional pass. Oracle: 12/12 and 9/9.

Note for future builders: the PHP built-in server in the probe image runs with opcache enabled and a
2 s revalidation window, so a tree patched immediately before the first request can serve stale
code. The verifier disables opcache for its server; the probe harness had to do the same.

## Gate (2026-10-24, system Docker)

- static: pass
- nop: pass — 12/12 security tests fail on the injected tree, 9/9 functional tests pass (reward 0.0)
- oracle: pass — three runs, reward 1.0 each, identical results (12/12 security, 9/9 functional)
- patches: pass — every declared outcome reproduced:
  lever_link_fallback 0.9167, lever_attribute 0.8333, lever_member_table 0.9167,
  lever_manual_providers 0.9167, lever_plugin_link 0.9167, lever_page_script 0.8333,
  far_utenti_select 0.8333, far_ajax_mapper 0.9167 (all security_fail, functional green);
  overbroad_link 0.0 and refuse_all 0.0 (functional_fail); hardening 1.0 and alternative 1.0 (pass).
- The `blind` patch is not written by this build; the patches stage skips it, as the gate allows.

End (UTC): 2026-10-24T08:53Z
