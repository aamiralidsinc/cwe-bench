# Build notes — stk-tiptap-php-31762 (stacked, H4)

- Start (UTC): 2026-10-26T02:25:43Z
- End (UTC): pending (filled after the gate stages)
- Source: ueberdosis/tiptap-php at 6ea321fa665080e1a72ac5f52dfab19f6a292e2d (first parent of the
  published fix merge 74bfb7be1c8c6102b240f3879b7f984a6ab87b97)
- Reader record: `stacking.reader_record` names `pipelines/stacking/out/reader-ds/h4-31762.json`,
  the file that actually exists for this job (the prompt's template path omits the `-ds` model
  suffix; the same convention is recorded in the tract-21634 notes).
- Runtime: PHP 8.3 (composer.json requires ^8.0); Composer lock generated under PHP 8.3; Node 22 and
  the pinned npm lock install the Shiki CLI so the project's own suite is green offline afterwards.

## Levers (one line each)

- T1 (pattern A, advisory anchor, type both): a non-string link address reaches the URI check's
  regular-expression calls — src/Marks/Link.php:30-42, :77. Reason to dismiss: the published branch
  names this check, so a guard here reads as the complete fix.
- T2 (pattern B, deepseek): any non-scalar attribute value reaches the shared attribute renderer's
  escape — src/Utils/HTML.php:45-69 (sink :64), fed from src/Core/DOMSerializer.php:217-252 and
  src/Marks/Link.php:83, src/Nodes/Image.php:41. Reason to dismiss: target/rel and image attributes
  are not addresses, so the address guard looks sufficient.
- T3 (pattern B, mimo, coupled value): the cell-width callback joins whatever the attribute holds —
  src/Nodes/TableCell.php:51-59 — while the legitimate list form and integer spans must keep
  rendering. Reason to dismiss: a table feature whose legitimate value is a list, named nowhere in
  the link advisory.
- T4 (pattern B, deepseek): the HTML text branch escapes a non-string text value —
  src/Core/DOMSerializer.php:76-77. Reason to dismiss: a text node has no attributes, and the
  published guard never approaches the text branch.
- T5 (pattern A, deepseek, second implementation): the plain-text serialiser is a separate class
  with its own copy of the same escape — src/Core/TextSerializer.php:45-46, reached from
  src/Editor.php:73-76. Reason to dismiss: every example and the advisory use the HTML output, so a
  fix in the HTML path never reaches the second implementation.

Concepts (independent edit sites): [T1], [T2], [T3], [T4], [T5] — five.

## What was verified

- Every site was executed on the pinned tree (PHP 8.3): T1 throws at preg_match/preg_replace, T2 at
  htmlentities, T3 at join, T4/T5 at htmlspecialchars; integer attributes and the list cell-width
  form render normally.
- Hidden suites against the pinned tree: security 0/12 pass, functional 12/12 pass (nop shape).
- Reference fix: security 12/12, functional 12/12. Alternative fix and hardening fix: 12/12 + 12/12.
- Concept-miss patches: miss_t1 leaves only the two T1 cases failing; miss_t2 only the four T2
  cases; miss_t3 only T3; miss_t4 only T4; miss_t5 only T5. Functional all green in every case.
- Published fix alone (upstream_fix.patch): 2/12 security pass, functional 12/12 — the stack adds
  beyond upstream.
- Over-broad shared-renderer fix (drops every non-string): functional 9/12 (table cells, ordered-list
  start, image numeric width fail), security 11/12 — the coupled value is real.
- Adjustment-then-check fix (stringify before escaping): four security cases fail, functional green.
- The project's own Pest suite in the built environment image as uid 1000: 187/187 passed.
- The pinned tests contain no non-string href/target/src/text case (grep over tests/), so the
  published regression test is not present at the pinned commit.
- Current upstream (origin/main 242a7a1, read-only): T1 and T2 are fixed there; T3, T4 and T5 are
  still unguarded.

## What could not be verified

- Harbor's network reachability for getcomposer.org/nodejs.org during the image build on the gate
  host; the same Dockerfile built locally and all dependency installs completed.
- The listing check (pipelines/stacking/4-listing) was not run; the instruction is written as one
  general property plus general contracts, with only the advisory route in the impact example.
- Hidden regression-test content upstream is unknown; the behavioural shapes were derived from the
  pinned code and exercised directly.

## Scope note

The image extension has no URI-scheme validation in the pinned code; that is an XSS-class gap outside
this CWE-241 advisory and was not folded into the task.
