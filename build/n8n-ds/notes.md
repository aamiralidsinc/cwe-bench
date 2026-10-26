# n8n-ds build notes

- Task: `n8n-ds`, pattern `A+B`, track `injected`, builder prompt `build-v1`.
- Advisory: GHSA-2X35-3FW4-9JR4 / CVE-2026-72766 (n8n-io/n8n). Published fix
  `f69dfc6dd2178a14ea1624d2e1d403c2e755042f`; pinned (vulnerable) parent
  `db5e2d068bc92a28a455598daa578fe405dce4bc` (repo version 2.32.0).
- Start UTC: 2026-10-18T20:29Z (driver start); build work begins 2026-10-18T20:31Z.

## Mechanism (one line each)

1. Workflow expressions can yield non-string values for fields the node types as
   strings; the mail library treats `{path}` / `{href}` content objects as a local file
   to read or a URL to fetch, so the value becomes message content.
2. The protected invariant: no workflow-supplied value may make n8n read a host file or
   fetch a URL and embed the result in outgoing mail; non-text values are rendered as
   text instead.

## Levers (each with a different reason to dismiss)

| id | pattern | shape | pinned site | reason a solver would skip it |
|----|---------|-------|-------------|-------------------------------|
| T1 | A (landing, published) | Text/HTML value `{path}` (host file read) and `{href}` (URL fetch) on the current Send Email send operation | `packages/nodes-base/nodes/EmailSend/v2/send.operation.ts:198-221` | none: it is the reported site; baseline the gate checks |
| T2 | A (far site) | same two shapes through the legacy Send Email implementation, which constructs its own transport and copies its own fields | `packages/nodes-base/nodes/EmailSend/v1/EmailSendV1.node.ts:153-195` | legacy version superseded by the default version; different transport construction, so "not the reported node" is arguable |
| T3 | B (uncovered route) | Message / HTML-body values on the Gmail node's legacy implementation, encoded by the mail library without file/URL restrictions | `packages/nodes-base/nodes/Google/Gmail/v1/GmailV1.node.ts:319-331,650-663`; sink `packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts:209-250` | different node and transport (Gmail API, not SMTP); legacy version (default is 2.2); the current version already coerces the body |
| T4 | input shape | non-text values (array / number) must arrive as text, not be rejected or dropped; a one-case fix that only special-cases `{path}`/`{href}` still errors on them | `packages/nodes-base/nodes/EmailSend/v2/send.operation.ts:212-221` | looks like a cosmetic robustness detail next to the security fix |
| T5 | injected sibling | per-attachment path / URL option on the current send operation, handed to the mail library as `{path}` / `{href}` | `packages/nodes-base/nodes/EmailSend/v2/send.operation.ts` options collection + attachment block | it is an attachment option, not a message field; attachments normally carry binary buffers |
| T6 | injected sibling | free-form plain-text alternative on send-and-wait, copied raw into the mail options while the same message goes through a templating helper for HTML | `packages/nodes-base/nodes/EmailSend/v2/sendAndWait.operation.ts:46-51` | send-and-wait builds its own message; the HTML part is templated, so the raw field looks like a benign fallback |

The published fix also adds transport-level file/URL restrictions to the shared
transport factory (`EmailSend/v2/utils.ts:48`) and coerces address fields. The oracle
includes both, but neither is a separate scored lever: a complete coercion at every
entry point already blocks every tested shape, and object-valued address fields are
dropped by the mail library rather than resolved. Noted, not tested.

## Sites and shapes the security tests cover

- Send Email current send operation: Text `{path}`, HTML `{href}`, Text array.
- Send Email legacy implementation: Text `{path}`, HTML `{href}`.
- Gmail legacy implementation: message `{path}` on send, HTML body `{href}` on draft
  create, and message `{href}` on reply (the shared encoder is the sink for all three,
  so a call-site-only fix is caught; reply is a separate call site that had no
  protection at the pinned commit).
- Injected attachment path/URL option: local path and `http://127.0.0.1` URL.
- Injected send-and-wait plain-text alternative: `{path}` and `{href}`.
- Each security test asserts the attack is blocked by outcome, not status: the SMTP /
  API message received by the test's own server must not contain the marker, and no
  request may hit the test's loopback recorder; a normal node error is also accepted.

## Coupled must-keep-working behaviour (functional tests)

- Text and HTML bodies with attribution appended; CC/BCC/Reply-To; both formats.
- Inline (`cid`) and regular binary attachments still attached with their buffers.
- Legacy implementation sends text/HTML and binary attachments.
- Gmail legacy send still produces the same MIME body for a plain string message.
- Send-and-wait still sends and puts the execution to wait; a plain-string value for
  the injected plain-text alternative still becomes a text part.
- SMTP credential test still succeeds.
- The pinned project tests for the mail node (v1, v2 send, v2 send-and-wait) still pass.

## Injection

`environment/injection.patch` adds, in the pinned tree only:
- an "Attachments (Path)" entry in the Mail node's send options, resolved as a mail
  library attachment `path`/`href` (T5);
- a "Plain Text Alternative" field on send-and-wait, copied raw into the text part (T6).

Both use existing parameter plumbing, are reachable through the node's normal execute
entry point, and are untouched by the published fix.

## Not built on

The published fix is a bundled security release; its other components (Git, Snowflake,
Postgres, EditImage, MCP, task-runner, lodash, token-exchange, LLM nodes) belong to
sibling advisories and are out of scope here. The Gmail route used as pattern B is the
screener's listed uncovered route into the same mail-library sink, not a sibling
advisory.

## To verify (fill in as the build proceeds)

- [x] Pinned code reproduces every security attack through the node entry point with a
      real mail library and a loopback SMTP server / HTTP recorder. The injected tree
      (pinned + injection) fails all 16 security tests and passes all functional tests.
- [x] Injection applies cleanly; pinned project tests still pass (27/27).
- [x] Oracle fix passes security (16/16), functional (10/10) and project tests (27/27).
- [x] Each security_fail patch fails only the lever it targets; functional stays green.
      sf-landing-only, sf-no-legacy, sf-no-gmail, sf-objects-only,
      sf-no-attachment-paths, sf-no-send-and-wait, sf-no-file-path all leave the
      custom functional group and the project tests green.
- [x] Over-broad functional_fail patches break a functional test
      (ff-refuse-all, ff-remove-attachments, ff-remove-alternate-part).
- [x] Both pass patches score 1.0 (pass-hardening, pass-alt-inline).
- [x] Full verifier entry point simulated in the dev image (tests/test.sh with /tests
      mounted and /logs written): oracle reward 1.0 (security 16/16, functional 37/37
      including the project tests); vulnerable tree reward 0.0 (security 0/16,
      functional 37/37).
- [ ] Gate stages static / nop / oracle / patches.

## Gate results (2026-10-18)

- static: FAIL only on the two items left for the fairness pass (blind patch, FAIRNESS.md);
  every other static check passes (leaks, exact-status rule, offline allowlist, kill block,
  catalogue, hidden-test isolation).
- nop: PASS. security 0/16, functional 37/37 on the pinned+injected image.
- oracle: PASS. 3/3 runs reward 1.0 with identical per-test results.
- patches: not completed as one run. The shared host runs dozens of concurrent gates, each
  calling `docker network prune -f`; every long run lost its freshly-created compose network
  between creation and container start ("network ... not found"). Each declared check passed
  in at least one gate run: sf-landing-only 0.375, sf-no-legacy 0.75, sf-no-gmail 0.875,
  sf-objects-only 0.8125, sf-no-attachment-paths 0.875, sf-no-send-and-wait 0.875,
  sf-no-file-path 0.8125, ff-refuse-all 0.0 (functional fail), ff-remove-alternate-part 0.0
  (functional fail), pass-hardening 1.0, pass-alt-inline 1.0. The same checks were also run
  end-to-end against the dev image with identical outcomes.
- Gate-run-only workarounds, all reverted: a prebuilt image tag via `[environment] docker_image`,
  public network mode, and `BUILDX_BAKE_ENTITLEMENTS_FS=0` (documented buildx opt-out). The
  shipped task keeps the Dockerfile-built environment and the model-API allowlist.

End UTC: 2026-10-18T23:25Z.

## Upgrade for the sibling-injection rules (2026-10-20)

- `instruction.md` was rewritten to one general property over outgoing email. It no
  longer names the node versions, operations, message fields, attached sources, formats
  or transports, and it does not describe any injected sibling. The preservation
  contracts are stated generally.
- The levers were checked for a HOW-type: T3 (the Gmail legacy route where protection
  never existed, M4) and T4 (non-text shape differential, M8) qualify; T5/T6 remain
  where-type extras. No new lever was added.
- Coverage: added one behavioural security test for Gmail v1 `reply`
  (`test_gmail_legacy.test.ts::does not fetch a URL for the body of a reply`), a call
  site that builds the same message through the shared encoder and had no protection at
  the pinned commit. The existing `sf-no-gmail.patch` still fails on it because the
  oracle fixes the encoder itself, not a call site. No new check patch was needed.
- No change was made under `environment/` or to any repository code, so the prebuilt
  image was NOT rebuilt. The added test, the manifest metadata and the instruction are
  the only changes; a container gate is required because `tests/` changed.
- Counts after the upgrade: 17 security tests.

## Hardening + Frontier conversion (2026-10-22)

Two new fair levers were added, both through O8b injection-room sites and both covered
literally by the existing general property (no instruction change beyond format rules):

- T7 host template (`EmailSend/v2/send.operation.ts`): the current send operation gains an
  `htmlTemplate` option. A value that starts with `/` is read from the host with
  `readFileSync` and written over the HTML body; any other value is the HTML. The read runs
  after the message fields and attachments have been handled, so coercing those fields or
  setting the mail library's file/URL flags does not cover it. Fix: render the value as text
  (or refuse). Coupled functional behaviour: inline HTML template text is still delivered.
  Reason to dismiss: it reads as configuration, not as one of the message fields a report
  names; it is an ordering/auxiliary read.
- T8 remote image (`Google/Gmail/v2/GmailV2.node.ts`): the current Gmail message send gains a
  `logoUrl` option. The node fetches the address itself with the execution helper and pushes
  the response bytes into the attachment list. The mail encoder and transport restrictions
  never see the request, so the fix needs the mechanism understood. Fix: stop fetching (a
  refusal/removal is allowed by the instruction). Coupled functional behaviour: a message
  with a binary attachment is still sent. Reason to dismiss: a decorative image in a
  different node, off the mail library's check path.

Both use existing parameter plumbing, are reachable through the real node execute entry
point, and are untouched by the published fix.

New tests: `security/test_template_file.test.ts`, `security/test_gmail_logo_url.test.ts`,
and `functional/test_new_siblings_legit.test.ts` (the two coupled behaviours).
`support/context.ts` gained a real `helpers.httpRequest` so the remote fetch reaches the
loopback recorder exactly as the product reaches a real server.

New checks: `sf-no-template.patch` (only T7 fails), `sf-no-logo.patch` (only T8 fails),
and `pass-blind.patch` (a complete fix written from the report and repository only). The
oracle, pass-alt-inline and pass-hardening were regenerated against the new injected tree
so they close both levers.

Counts: 19 security tests, 12 custom functional tests, 27 project tests.
Dev-image results (`--network none`): vulnerable+injected security 0/19, functional 12/12,
project 27/27; oracle security 19/19, functional 12/12, project 27/27;
sf-no-template 1 security fail; sf-no-logo 1 security fail; pass-alt-inline,
pass-hardening and pass-blind 19/19 and 12/12. All earlier sf-* checks still leave a
security failure with functional green; both ff-* checks still break functional.

Frontier delivery format: schema 1.4, `/workspace`, separate offline verifier over
`artifacts`, uid-1000 non-root grading, dual scoring. The verifier image ships a pristine
installed+built tree at `/opt/n8n-base`; `tests/test.sh` saves the submission, lays the
pristine sources and build outputs down at `/workspace`, overlays the submission's sources,
links the pristine `node_modules` trees in place, and runs vitest as `agent`.

## Gate results (2026-10-22, Frontier format)

- static: PASS (`conformance_check` prints conforming; re-run after the final
  `[verifier].timeout_sec` bump to 3000).
- nop: PASS. security 19, functional 39; reward 0.0
  (trial `n8n-ds__t6MJqJF`, ~74 min including the two first image builds).
- oracle: PASS. 3/3 runs reward 1.0 with identical per-test results.
- patches: PASS. All 14 declared checks behaved:
  ff-refuse-all 0.0 (16 functional failures), ff-remove-alternate-part 0.0 (1),
  pass-hardening 1.0, pass-alt-inline 1.0, pass-blind 1.0,
  sf-landing-only 0.3158, sf-no-legacy 0.6842, sf-no-gmail 0.7368,
  sf-objects-only 0.7368, sf-no-attachment-paths 0.7895, sf-no-send-and-wait 0.7895,
  sf-no-file-path 0.7368, sf-no-template 0.9474 (only T7 fails), sf-no-logo 0.9474
  (only T8 fails); every security_fail check kept functional 39/39.
- An independent end-to-end run of `tests/test.sh` in the dev image reproduced the
  vulnerable (0/19 security, 39/39 functional, reward 0.0) and oracle (58/58, reward 1.0)
  outcomes.

End (hardening) UTC: 2026-10-22T03:30Z.


