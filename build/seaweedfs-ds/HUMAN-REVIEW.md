# Human review — seaweedfs-ds — 2026-10-20 — DONE, CONFIRMED, NO CHANGES

Decision: keep the task exactly as is (tests, instruction, verdicts unchanged).

- Review item (a) TestSecZZCatalogOtherUserCannotListNamespaces (listing another account's bucket must be
  refused with 4xx, not served empty): UPHELD AS-IS, with a noted instruction ambiguity — lines 35-36
  ("anything that lists resources leaves out the ones the caller may not see") support an empty-list
  design. Verdict-neutral: only MiMo r2 failed it, and r2 has three other security misses.
- Review item (b) TestSecZZBatchDeleteChecksEveryTable (refused batch delete is all-or-nothing): UPHELD,
  clean — line 42 "removes nothing" + lines 21-22 "every element of a request". No run failed it.
- Verdict-deciding preservation tests for DeepSeek (r1/r2 were 31/31 security, failed only these):
  AdminsBypassBucketPolicy, CatalogEmbeddedAuthenticatorOpenDefault, ShellManagesAnyAccountsBucket — each
  backed by an explicit Preservation bullet (lines 45-54, "exactly as today"). Only opposing phrase:
  line 28 "an explicit deny always applies", scoped to requests without valid credentials; not a
  contradiction. DeepSeek's breaks are genuine (it made denies override owner/admin).
- Breaker status: both-model breaker stands (DeepSeek 0/3, MiMo 0/3), audit recorded.
