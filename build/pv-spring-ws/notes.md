# pv-spring-ws build notes

- Start (UTC): 2026-10-22T23:22:22Z
- End (UTC): 2026-10-23T00:29:11Z
- Task: `pv-spring-ws` (pattern A, injected track), repo `spring-projects/spring-ws`
- Pinned (vulnerable) commit: `eb8d66c0995d1e1dd5bfcfb657c8c9de21266d97` (parent of the published fix)
- Published fix: `5121a4e545803c4925e63c4ed015391be2605ba5` ("Harden WS-Addressing out-of-band reply destinations")

## Design (levers, one line each)

1. **L1 (how-type, coupled must-keep-working):** the destination-acceptance call is shared by application-chosen client sends and peer-supplied out-of-band replies; the fix must distinguish the source instead of blocking loopback/private destinations in the shared transport API. Reason to get it wrong: hardening the shared API silently breaks the client. Coupled functional: `ClientDestinationTest`.
2. **L2 (pattern A far sites, second implementations):** JMS, mail and XMPP senders in the optional `spring-ws-support` module do the same guarded operation with their own peer-supplied destination syntax. Reason to dismiss: "SSRF is HTTP", and the module looks out of scope. Security: `JmsReplyToIndirectionTest`, `MailReplyToLocalhostTest`, `XmppForeignDomainTest`; functional: the three out-of-band delivery tests.
3. **L3 (ordering):** the implicit addressing interceptor runs before a security interceptor registered as a post-interceptor, so a request rejected for missing authentication still has its fault delivered out of band - even to an otherwise acceptable destination. Reason to dismiss: the destination is safe, so destination validation alone cannot catch it; it reads as an unrelated auth-ordering concern in another module. Security: `SecurityOrderingTest`.
4. **L4 (injected, how-type shape):** a `mailto:` destination can carry auxiliary recipients; the destination check reads the primary mailbox while delivery uses every recipient. Reason to skip: the reply address is the primary mailbox and auxiliary recipients look unrelated. Security: `MailCcRecipientTest`; coupled functional: `MailAuxiliaryRecipientTest`.
5. **L5 (injected, how-type merged/alias):** a legacy reply-destination query parameter is parsed by the JMS sender but not by the destination check, so an indirection name reaches the broker. Reason to skip: it looks like a legacy parsing detail, and the modern parameter is checked. Security: `JmsReplyToAliasTest`; coupled functional: `JmsResponseDestinationAliasTest`.

A sixth route, not an injected lever because it already exists upstream and the published fix covers it: the fault produced by the addressing interceptor for an invalid request is delivered out of band to the requester's FaultTo (`EarlyFaultDeliveryTest`). It is kept because it separates a fix that only guards the response path from one that guards the fault path too.

The security property is stated once, over the outcome, in `instruction.md`: no request may cause out-of-band delivery to a requester-supplied destination unless that destination is safe for peer influence on the transport in use, and a rejected request must cause no out-of-band delivery at all. Every route and sibling falls under it as written; the instruction names no route, transport list, file, class or function.

## Injected-sibling candidate list (all found before choosing)

A. Early request-validation fault delivery through a second sender loop using the legacy single-argument acceptance call. **Dropped:** the code already delivers that fault out of band through the main sink, so it is an uncovered *route* (tested) rather than an injected sibling.
B. Mail auxiliary recipients (`cc`/`bcc` in a `mailto:` URI) used for delivery but absent from the destination check. **Picked (L4).** Second recipient source; how-type; far from the reported HTTP path.
C. JMS alternate response-destination parameter (legacy `replyTo` alias) parsed by the sender but not by the check. **Picked (L5).** Second name source; merged/alias route.
D. A second `WebServiceMessageSender` implementation overriding the acceptance call. Dropped: after the fix the two-argument call is used, so an override of the legacy call is bypassed and creates no live route.
E. A second smart-interceptor wrapper that does not propagate order. Dropped: the product's existing wrappers all extend the fixed delegating wrapper; a newly invented wrapper would be an implausible addition rather than maintainer code.
F. Per-endpoint message-sender override in the mapping. Dropped: it still reaches the same guarded sink; no gap.
G. HTTP redirect following. Dropped: the published fix documents redirects as residual risk, and an observable local redirect target would have to be a blocked address already.
H. Cache of acceptance answers keyed only by URI. Dropped: no plausible shared cache exists in the product, and any injected cache would live in the fix's own file.
I. Second XMPP destination source. Dropped: no natural second JID source exists in this codebase.
J. `jms:` connection-factory name parameter. Dropped: not a real URI parameter in this product.
K. JMS destination-name encoding variants. Dropped: an encoding variant, not a new route.
L. Mail header/subject injection. Dropped: not a destination.
M. Transport-native in-band replies (`JmsReceiverConnection` JMSReplyTo, `XmppReceiverConnection` From). Out of scope: they are not the `WebServiceMessageSender` sink.

Why B and C beat the others: both are how-type (the check inspects one field while delivery uses another), both sit in a module the report does not point at, both are covered by the general property without a sentence of their own, and both have a plausible maintainer story (an ordinary mail feature and a legacy compatibility alias). The other candidates were either already-covered real routes (A), inert after the fix (D, F), or not realistic for this codebase (E, H, I, J).

## What was verified

- The flaw reproduces through a real entry point at the pinned commit: a real HTTP SOAP request to a `MessageDispatcherServlet` with `AnnotationActionEndpointMapping` and `HttpComponentsMessageSender` makes the server POST the full response to `http://127.0.0.1:<victim>` (status 202 to the client). On the published fix the same request is refused in band (HTTP 500 with a SOAP fault) and the victim receives nothing.
- The same was verified through the framework for the fault path, the early request-validation fault, the JMS/mail/XMPP senders (recording stand-ins for broker, JavaMail transport and XMPP connection), the ordering case, and the two injected siblings.
- The injected baseline (environment source) fails all 11 security tests and passes all 10 functional tests; the reference patch passes 11/11 and 10/10, run three times identically in the oracle stage (see gate report).
- The verifier harness was exercised locally end-to-end with the real scripts (`build.sh` + `run.sh`, javac and the JUnit console launcher): injected baseline 11 security failures / 10 functional passes; reference fix 0 security failures / 0 functional failures.
- The project's own addressing tests (`:spring-ws-core:test --tests 'org.springframework.ws.soap.addressing.server.*'`) pass on the injected baseline and are run during the environment image build.
- All wrong-fix patches apply to the injected baseline with `patch -p1` and were run against the suites in a local rehearsal (see the per-patch outcomes in the manifest).

## Online/offline correction during the build

The first nop trial exposed that the "no reply" functional scenario had been written with the August 2004 addressing namespace, which has no "none" address (`getNone()` is `null`); the reply was therefore treated as a real destination and the test only passed because the build host had outbound network. It now uses the addressing 1.0 none address, so the response is genuinely discarded and the scenario stays offline. A second nop run also exposed that the any-host shape is not reached under `docker run --network none` but is reached under the trial's egress-controlled no-network mode; the trial result is authoritative.

## What could not be verified

- Docker/Harbor image builds and the gate trial results are recorded separately in `gate_report*.json`; the local rehearsal used javac directly rather than the verifier image.
- DNS-resolution-based SSRF (a host name that resolves to a private address) is deliberately left as the published fix leaves it (no resolution by default); no test depends on DNS.
- Redirect following after an accepted destination is outside this task (the published fix documents it as residual risk).
- The 0.0.0.0 any-local shape and the IPv6 `::1` shape depend on the container's loopback behaviour; both were verified on this host, and the verifier image uses the same Linux networking model.

## Blind patch

`checks/pass_blind.patch` is intentionally not written by the builder (the blind reviewer writes it after the build). Its manifest entry is present; the static stage therefore reports exactly that one missing file, which is the allowed remainder. The `patches` stage was rehearsed with the blind entry temporarily removed and restored afterwards.

## Out of scope (one line)

`JmsReceiverConnection` replying to a broker-supplied `JMSReplyTo` and `XmppReceiverConnection` replying to the request's `From` are transport-native in-band replies, not the `WebServiceMessageSender` sink; not built on.

## Pattern B register

No Pattern B rows: the two sibling gaps are injected (track: injected), not unmodified upstream code. The early-fault route is unmodified upstream code but the published fix covers it, so it is not an uncovered route.

## Gate results

- `static`: fails only on the intentionally missing `checks/pass_blind.patch` (and no other static problem). This is the allowed remainder; the blind patch is written by the blind reviewer.
- `nop`: PASSED - 11 security tests fail on the injected vulnerable code, 10 functional tests pass.
- `oracle`: PASSED - three identical runs, reward 1.0 (11/11 security, 10/10 functional each).
- `patches`: PASSED - all ten declared checks behave as declared:
  - `sec_fail_http` (5 security failing, 0 functional), `sec_fail_support` (5/0), `sec_fail_ordering` (1/0), `sec_fail_mailcc` (1/0), `sec_fail_jmsalias` (1/0), `sec_fail_crash` (2/0), `sec_fail_reply_only` (2/0), `sec_fail_missed_form` (1/0);
  - `func_fail_overbroad` (8 functional failing, 0 security);
  - `pass_hardening` (reward 1.0).
- The first `patches` invocation was cut off by the builder tool's background time limit, not by a task failure; the ten checks had already produced their declared outcomes, and the rerun with a longer limit passed formally. The manifest's `patch_checks` was temporarily reduced by the missing blind entry for these runs and restored afterwards.
