# pv-spring-ws — fairness validation (dispute: XmppForeignDomainTest)

Date: 2026-10-25. Judged from `tasks/pv-spring-ws/instruction.md` (all the solver sees, plus the repo), the hidden tests, `solution/fix.patch`, `manifest.json`, `notes.md`, `checks/*.patch`, `FAIRNESS.md`, the 7 audit verdicts and each run's `verifier/results.json`. No code was run.

## 1. XmppForeignDomainTest::foreignDomainDestinationIsNotDelivered — UNFAIR

What it asserts: with an XMPP connection whose service domain is `safe.example`, a ReplyTo of `xmpp:user@evil.example/resource` must get 0 stanzas and an in-band refusal. This is the rule in the reference fix, copied from upstream: "For REMOTE ... accept only URIs whose JID domain matches the connection's XMPP service domain" (fix.patch, XmppMessageSender javadoc and `xmppRemoteDefaultChecks`).

Why a correct fix written from the instruction can fail it:

1. **The instruction describes the harm as reaching internal destinations.** The only concrete harm it gives is delivery to "an address on the service's own private network". The invariant's test is "safe for peer influence on the transport in use", and its list of forms ("address literals of any family and transport-specific destination syntax") is about how an internal destination can be disguised. It never says that a public, external destination is unsafe, and it never says that a transport must keep peer-chosen destinations inside the service's own domain.
2. **The suite itself defines "safe" as "not internal", and the mail tests prove it.** `MailOutOfBandDeliveryTest` requires delivery to `ops@example.com`, and `MailAuxiliaryRecipientTest` to `audit@example.com`. In both, the transport is `bench://localhost`, so the requester picks a mailbox outside the service's own domain. Peer-chosen mail to any external domain is the standard open-relay concern, which is at least as strong an egress concern as XMPP federation. Yet the tests treat it as "ordinary and legitimate". A fixer who applies the same rule to XMPP (refuse JIDs whose domain is `localhost`, `*.localhost`, an IP literal or a private address, and allow external domains) is consistent with the instruction and with every mail test. That fixer fails this test.
3. **The instruction does not justify treating mail and XMPP differently.** "on the transport in use" allows checks that differ per transport, but it does not say which policy each transport gets. Nothing in the text marks a foreign XMPP domain as unsafe while a foreign mail domain is safe. The only source for that difference is upstream's policy, and the instruction forbids looking up the upstream fix.
4. **The reviewer's "expert knowledge" argument proves too much.** It says a JID outside the connected service domain is peer-directed egress. The same is true of mail to an outside domain, which the suite requires to work. The DeepSeek reviewer itself flagged that "neither criterion is stated and a fixer could plausibly allow them".
5. **The run data agrees.** The test failed in 7 of 7 runs, across two models and very different fixes. In mimo-a4 it was the only failure, after that run had already covered HTTP shapes, fault routes, ordering, JMS indirection and its alias, mail localhost and cc. That pattern points to a hidden policy, not to a missed route.

`XmppOutOfBandDeliveryTest` (on-domain delivery works) is fair and is not disputed. A fair replacement would use an internal XMPP form, such as `xmpp:user@localhost` or `xmpp:user@127.0.0.1`. Alternatively, the instruction could state the own-domain rule, though that would be a hint.

## 2. MailReplyToLocalhostTest::localMailboxDestinationIsNotDelivered — FAIR (risk medium)

`mailto:root@localhost` is a mailbox on the service's own host. It is the mail form of the reported loopback destination, so it is an "internal destination" in "transport-specific destination syntax", and the invariant applies to "every transport the framework offers". A fixer who reads "safe" as "not internal" (the reading that makes the XMPP test unfair) blocks it. The mail functional tests only require external mailboxes, so they do not conflict with this test. The remaining risk is a fixer who argues that every mailbox is fine because mail always goes through the configured SMTP server. That reading ignores the instruction's framing. A competent engineer who covers the mail transport at all refuses localhost mailboxes.

## 3. MailCcRecipientTest::additionalLocalRecipientIsNotDelivered — FAIR (risk low)

`mailto:ops@example.com?cc=root%40localhost`: the instruction says it explicitly: "A single delivery can involve more than one requester-supplied destination ... may proceed only when every one of them is acceptable; otherwise the whole delivery must be refused." This test is fair as long as section 2 is fair, and the cc mailbox is the same localhost mailbox. `MailAuxiliaryRecipientTest` (external cc delivered) does not conflict with it.

## 4. JMS tests (decide other runs) — FAIR (agreeing with both reviewers)

`replyToName=ldap://127.0.0.1:1389/...` and the legacy `replyTo=` alias are covered by "transport-specific destination syntax" and "any destination that ends up being used for the delivery, however that destination is expressed in the request". An indirection name that points at a loopback LDAP server is an internal destination under any reading.

## 5. Per-run fair failures

| Run | Failing tests | Fair failures | Still a model failure? |
|---|---|---|---|
| deepseek-a1 | JmsIndirection, JmsAlias, Xmpp | JmsReplyToIndirectionTest, JmsReplyToAliasTest | YES |
| deepseek-a2 | JmsIndirection, JmsAlias, Xmpp | JmsReplyToIndirectionTest, JmsReplyToAliasTest | YES |
| deepseek-a3 | JmsIndirection, JmsAlias, MailLocalhost, MailCc, Xmpp | JmsReplyToIndirectionTest, JmsReplyToAliasTest, MailReplyToLocalhostTest, MailCcRecipientTest | YES |
| mimo-a1 | MailLocalhost, MailCc, Xmpp | MailReplyToLocalhostTest, MailCcRecipientTest | YES |
| mimo-a2 | JmsIndirection, JmsAlias, Xmpp | JmsReplyToIndirectionTest, JmsReplyToAliasTest | YES |
| mimo-a3 | JmsIndirection, JmsAlias, Xmpp (agent hit its 7200 s limit; graded) | JmsReplyToIndirectionTest, JmsReplyToAliasTest | YES |
| mimo-a4 | Xmpp only | none | NO: effective solve (10/10 functional, 10/10 fair security) |

Outcome: DeepSeek fails 3 of 3. MiMo fails 3 of 4 but solves 1 (a4), so the task is not a MiMo breaker. The task is a breaker for DeepSeek only, unless a repaired XMPP test is re-graded on a4's workspace and a4 fails it.

Recommended repair: replace `XmppForeignDomainTest` with an internal-form JID case, or state the own-domain rule. Then re-grade all 7 workspaces if they can be recovered.

XMPP_TEST: UNFAIR
MIMO_A4: EFFECTIVE_SOLVE
TASK: DEEPSEEK_ONLY
