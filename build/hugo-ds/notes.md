# hugo-ds — build notes

Candidate: GHSA-C54G-XJWJ-8G82 / CVE-2026-50133 / GO-2026-5313, gohugoio/hugo.
Pinned: `90d9f812b2cafc79ca125a829936dec9654aec64`; published fix:
`e41a06447daa3071a01f333fdcec0a5153c3c8d1`.
Track: injected. Pattern: B. Build start 2026-10-24T05:15Z. Build end 2026-10-24T09:06Z
(the VM was paused for about an hour by the operator for a host Docker fix; the gate was
re-run from the nop stage afterwards).

## Gate results (run one stage at a time)

- `static`: PASS (`gate_report.partial.json`, started 2026-10-24T05:37:44).
- `nop`: PASS — 10 security tests fail on the untouched pinned+injected tree, 30 functional
  tests pass (12 hidden + 18 project), `build/hugo-ds/evidence` not needed
  (trial `hugo-ds-nop-1792828009`).
- `oracle`: PASS — 3 runs, reward 1.0 each, identical results
  (trials `hugo-ds-oracle1/2/3`, finished 2026-10-24T08:52:13).
- `patches`: PASS — miss_subtype (1 security fails), miss_resource (3), miss_resource_suffix (2),
  miss_cascade (1), deny_all (functional fails), hardening (1.0), alt (1.0).
  Logs: `~/.tb-graders/cwe/work/hugo-ds/gate-*.log`.


## Levers

- **T1 — HTML identity (how-type shape, real upstream).** `media/mediaType.go:194` decides "HTML"
  from the media subtype, while a plausible policy matches the full media-type name. A site that
  declares its own content format `application/html` (suffix `ahtml`) gets a verbatim body that a
  `text/html`-only deny rule admits. Reason to dismiss: it is not `text/html`, so a policy over
  media types appears not to apply.
- **T2 — adapter resources (route where the protection never existed, plus a path shape; real
  upstream).** `hugolib/content_map_page_assembler.go:1275` publishes a body added by a content
  adapter's resource API as a page resource when a template links it. Its format comes from a
  declared media type or, when absent, from the `.html`/`.htm` target path
  (`resources/resource.go:110`). The published fix never touches this path. Reason to dismiss: it
  is a page resource, not a page, and nothing is published unless a template asks for its link.
- **T3 — cascaded format (producer after the check; injected sibling).** The injected extension in
  `resources/page/pagemeta/page_frontmatter.go:122` lets a section's cascade set the markup for
  descendant pages and re-resolves the content format at `:384`, after
  `hugolib/page__meta.go:215` has already gated it. Reason to dismiss: cascade is legitimate
  page-configuration inheritance, not the content file's own format.

## Verified

- Every route was reproduced with the built CLI on the pinned (and pinned+injected) tree and closed
  by the reference fix; the manifest's `verified.routes` lists each one.
- The reference fix adds a default-deny content policy matched on the HTML identity (any media type
  whose subtype is HTML) with the `[security] allowContent` opt-in, gates page metadata at init and
  again after shared configuration is applied, and gates adapter resources after resolving a format
  that was not declared.
- Local results: 10 security tests fail on pinned+injected and pass on the reference fix; 12
  functional tests pass on both. Patch variants behave as declared (missing subtype / missing
  resource gate / missing path resolution / missing cascade gate / deny-all).
- Project tests (`resources/page/pagemeta`, `config/security`, `hugolib/pagesfromdata` subsets) pass
  on pinned+injected and on the reference fix, restored from pristine copies at grading time.
- Latest upstream read-only look (`origin/HEAD` = `ed22b85c`, 2026-10-22): the deny rules are still
  the exact `text/html` and `text/org` names and the only gate is still in page-metadata init;
  `HandleResource` is still ungated. So T1 and T2 are still present upstream.

## Could not verify

- The screener's Org export-block route: not built (a different markup, outside this advisory's
  protection).
- External converters (asciidoctor, rst2html, pandoc) are not installed; their routes were not
  pursued (they are gated by the executive allow-list and are outside this advisory).
- Whether every plausible "correct" sanitising design (escape instead of refuse) would satisfy the
  stated refusal contract; the contract requires a failed build, so such a design is out of contract
  by construction.
- The screener's `present_in_latest` for the injected sibling has no upstream counterpart; recorded
  as unknown in the register.
