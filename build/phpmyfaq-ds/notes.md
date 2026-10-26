# phpmyfaq-ds build notes

Start (UTC): 2026-10-24T04:12:27Z
End (UTC): 2026-10-24T08:55:00Z

## Task

phpMyFAQ (PHP 8.3, Composer, PHPUnit 12). Pinned vulnerable commit
`bb2ec34e19420d02e8ccb26f5052c8942ef430f7`; published fix `4c7e3f841ba6cb25564c6802509a669b0e328321`.
The published fix adds `active='yes'` plus the `date_start..date_end` window to two data-access
methods (`getFaqsByIds`, `getFaqByIdAndCategoryId`). Pattern A+B, injected track.

## Security property (written once, in `instruction.md`)

An ordinary visitor may see a FAQ record only while it is enabled and the current time is inside
its publication window; no public read surface may disclose any part of a record that is not
visible, and a response carrying several records carries only the visible ones. Administrators and
FAQ editors keep their existing access.

## Levers (one line each)

- T0 (pattern A, report target): `Faq::getFaqByIdAndCategoryId` returns disabled/scheduled/expired
  records in full through `GET /api/v3.1/faq/{categoryId}/{faqId}`; reason to dismiss: none, this
  is the reported site.
- T1 (pattern B, main how-type): `Faq::getAllFaqs` (collection endpoint) substitutes a message into
  the answer for disabled/expired rows but still returns title, keywords, author, e-mail, dates and
  notes, and returns a scheduled row's full answer because only the window end is examined; reason
  to dismiss: the answer already looks masked and the endpoint documents an enabled field.
- T2 (pattern A far site, producer off the check's path): `Tags::getFaqsByTagId` returns ids with
  no visibility filter and `Faq::getFaqsByIds` is the shared reader behind the tag endpoint;
  reason to dismiss: tag listings look like a separate metadata/preview feature.
- T3 (pattern B, second implementation): `Search::searchDatabase` builds its own conditions with
  the enabled flag only, returning question + answer excerpt for scheduled/expired rows; reason to
  dismiss: search already filters on the enabled flag and is a separate feature.
- T4 (pattern A+B, coupled privileged value): `Faq::getFaq`/`getFaqResult` masks the answer for
  disabled/expired but keeps metadata, never checks the window start, and exposes the editor
  branch; the PDF endpoint links to records through it; reason to dismiss: it looks handled because
  of the message substitution and the explicit administrator flag.
- I1 (injected, how-type): public feed reuses the export query type (`Faq::get` ->
  `QueryHelper::getQuery`), which knows the enabled flag but not the window; reason to dismiss:
  the export path already filters and is a separate feature. The administrative export must keep
  including scheduled records, so a global filter in the query builder is over-broad (functional
  test).
- I2 (injected, wrong authority): public editor-preview endpoint passes the privileged flag
  unconditionally to the detail reader; reason to dismiss: the flag is set, so the privileged
  branch looks deliberate.

## Candidate sibling sites considered (all found in the pinned tree)

Real upstream: by-id-set/tag composition (picked T2); collection reader `getAllFaqs` (picked T1);
database search (picked T3); detail/revision reader + PDF link (picked T4); solution-id lookup
(`getFaqBySolutionId`); solution-id -> id resolution (`getIdFromSolutionId`); sticky list
(`getStickyFaqsData`); export query builder (`QueryHelper`); tag cloud frequencies
(`Tags::getPopularTags`); public sitemap (`Sitemap::getAllFirstLetters/getFaqsFromLetter`);
Elasticsearch/OpenSearch search paths (external service); comments/attachments parent check
(separate feature); `Faq/Statistics` readers and `getAllAvailableFaqsByCategoryId`/`renderFaqs*`
(already have the full triple, no gap). Injected candidates: public feed on the export query type
(picked I1); public solution-id API route (not picked: same reader gap as T4, mostly where-type);
public editor-preview endpoint with a constant privileged flag (picked I2); a new category/bulk
listing route (not picked: duplicate of T1's collection shape); a sitemap-like JSON endpoint (not
picked: duplicate of the active-only reader shape).

Why the picks beat the others: T1/T3/T4 are real, unmodified code with three different mechanisms
(substitution != withholding; an independent condition builder; an end-only window plus a coupled
privileged branch); T2 is the published fix's far site reached through a producer the reader never
calls; I1 and I2 are how-type injected siblings (query-builder reuse; authority decided by a
constant) placed where the published fix never touches. The rejected routes were either the same
shape as a picked lever or an external-service/adjacent-feature concern.

## Verified

- The three hidden states (disabled, scheduled, expired) each reproduce on the pinned, injected
  tree through real controller handlers: 14/14 hidden security tests fail there, 11/11 hidden
  functional and 30/30 project tests pass (local SQLite install from the project's own installer).
- Oracle (published fix + every uncovered route + both injected siblings): 14/14 security, 11/11
  functional, 30/30 project tests pass.
- Missing-lever patches confirmed locally: T0 (3 detail security failures), T1 (1 list), T2 (1
  tag), T3 (2 search), T4 (2 PDF), I1 (2 feed), I2 (3 preview), wrong-resource (3 detail), each
  with 0 functional/project failures. Over-broad variants: refuse-all (6 hidden functional + 3
  project failures), admin-hard-filter (2 functional), global export filter (1 functional).
  pass-hardening and pass-alt: all 55 cases green.
- The verifier path itself was exercised offline on the built images: the injected tree scores
  reward 0.0 (41 passed / 14 security failed / 55 total) and the oracle tree scores 1.0.
- Gate: static PASS; nop PASS (14 security fail, 41 functional/project pass); oracle PASS
  (3 runs, each reward 1.0 with identical results); patches PASS (13/13 checks as declared).
- `injection.patch` applies cleanly to the pinned tree; `solution/fix.patch` applies cleanly on
  top of the injected tree.

## Could not verify

- The advisory text beyond the screener's summary (only the summary and the fix diff were given).
- Whether each uncovered route is still present in current upstream `main`: main has since been
  restructured (`FaqStatus` enum, `api.onlyActiveFaqs`), so the register marks this `unknown`.
- Elasticsearch/OpenSearch search paths (external services; not run).
- Comments/attachments parent-visibility checks (adjacent feature; out of scope, not built).

## Out of scope (not built)

- The collection endpoint returns the internal `notes` field for visible records as well; separate
  exposure, not built on.
- Comment/attachment endpoints do not apply group/user FAQ permissions; separate concern.
- Elasticsearch/OpenSearch indexing of inactive FAQs needs an external service; not checked.

## Gate evidence (job ids)

- static: local run, PASSED (2026-10-24T05:01Z).
- nop: `phpmyfaq-ds-nop-1792818532` (14 security fail, 41 functional pass).
- oracle: `phpmyfaq-ds-oracle1-1792818740`, `phpmyfaq-ds-oracle2-1792819026`,
  `phpmyfaq-ds-oracle3-1792819372` (each reward 1.0, 55/55).
- patches: detached run started 2026-10-24T05:36Z (13 checks); job ids
  `phpmyfaq-ds-chk-*`.

## Infra note (2026-10-24T06:12Z)

The shared Docker daemon wedged during the patches stage (`/_ping` answered, `/version` and
`/info` hung). The patches stage was restarted against a task-private dockerd
(`build/phpmyfaq-ds/priv-docker`, pool 10.202.0.0/16, bridge 10.203.0.1/16) with
`TMPDIR=/var/tmp/pmf-gate` to avoid the shared `/tmp` inode exhaustion. The first trial on the
private daemon rebuilds the image cache; the remaining trials reuse it.
