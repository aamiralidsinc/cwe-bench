# pv-spring-ws — pre-trial fairness review

## 1. Tests

| Test (file::method) | What it asserts | Instruction sentence that makes it fair | Correct fix could fail? | Risk |
|---|---|---|---|---|
| HttpReplyToSsrfTest::loopbackReplyDestinationIsNotDelivered | no delivery to a 127.0.0.1 ReplyTo; client sees in-band fault or 4xx | "No request may cause the service to deliver a message out of band to a destination that the requester supplied unless that destination is safe for peer influence"; §Refusal | no | low |
| HttpFaultToSsrfTest::loopbackFaultDestinationIsNotDelivered | same for a loopback FaultTo | "every way a response or a fault can be sent out of band" | no | low |
| HttpAddressShapeTest::ipv6LoopbackReplyDestinationIsNotDelivered | no delivery to `http://[::1]`; refused | "every form that a requester-supplied destination can take"; standard expert knowledge: `::1` is loopback | no | low |
| HttpAddressShapeTest::anyLocalReplyDestinationIsNotDelivered | no delivery to `http://0.0.0.0`; refused | same; standard expert knowledge: 0.0.0.0 is the any-local address and routes to the local host | no | medium |
| JmsReplyToIndirectionTest::indirectionInRequestedDestinationIsNotResolvedOrDelivered | no send, no `ldap:` name resolved, refused | "transport-specific destination syntax"; "any destination that ends up being used for the delivery, however that destination is expressed"; standard expert knowledge: JNDI-style names resolve to external systems | no | low |
| JmsReplyToAliasTest::indirectionInLegacyResponseDestinationIsNotResolvedOrDelivered | same via the legacy `?replyTo=` parameter | "It also applies to any destination that ends up being used for the delivery, however that destination is expressed in the request." | no | low |
| MailReplyToLocalhostTest::localMailboxDestinationIsNotDelivered | 0 sends, `root@localhost` not reached, refused | "every transport the framework offers"; "safe for peer influence on the transport in use"; standard expert knowledge: a local mailbox is local delivery | no | medium |
| MailCcRecipientTest::additionalLocalRecipientIsNotDelivered | 0 sends, cc mailbox not reached, refused | "may proceed only when every one of them is acceptable; otherwise the whole delivery must be refused" | no | low |
| XmppForeignDomainTest::foreignDomainDestinationIsNotDelivered | 0 stanzas, refused | "every transport the framework offers"; "safe for peer influence on the transport in use"; standard expert knowledge: a JID outside the connected service domain is peer-directed egress | no | medium |
| SecurityOrderingTest::rejectedRequestCausesNoOutOfBandDelivery | 0 JMS sends for an unauthenticated rejection (acceptable destination), refused | "a request that the service rejects ... must cause no out-of-band delivery at all" | no | low |
| EarlyFaultDeliveryTest::loopbackFaultDestinationOfARejectedRequestIsNotDelivered | fault of a MessageID-less request not delivered; refused | "a request that the service rejects"; "every way a response or a fault" | no | low |
| ClientDestinationTest::clientReachesLoopbackHostName | client call to `http://localhost:<port>` returns Pong | "client side must not be restricted"; client-chosen destinations keep working | no | low |
| ClientDestinationTest::clientReachesLoopbackIpLiteral | same via 127.0.0.1 | same | no | low |
| AnonymousReplyTest::anonymousReplyIsReturnedInBand | 2xx, Pong body | "Requests with an anonymous reply destination must still be answered in band" | no | low |
| NoneReplyTest::noneReplyIsDiscarded | 2xx, no Pong body | "requests that ask for no reply must still have their response discarded" | no | low |
| JmsOutOfBandDeliveryTest::ordinaryDestinationReceivesTheReply | 1 send to benchQueue | "A reply destination that is ordinary and legitimate for the transport in use must still receive the out-of-band reply" | no | low |
| JmsResponseDestinationAliasTest::ordinaryLegacyResponseDestinationReceivesTheReply | 1 send, auditQueue resolved | "ordinary values that accompany it must keep working"; "Everything that works today must keep working" | no | low |
| MailOutOfBandDeliveryTest::ordinaryMailboxReceivesTheReply | 1 send to ops@example.com | "ordinary and legitimate for the transport in use must still receive" | no | low |
| MailAuxiliaryRecipientTest::ordinaryAuxiliaryRecipientReceivesTheReply | 1 send, both mailboxes reached | "ordinary values that accompany it must keep working"; "every one ... acceptable" | no | low |
| XmppOutOfBandDeliveryTest::destinationOnTheServiceDomainReceivesTheReply | 1 stanza to user@safe.example | "ordinary and legitimate for the transport in use" | no | medium |
| JmsFaultOutOfBandDeliveryTest::ordinaryFaultDestinationReceivesTheFault | 1 send, auditQueue | "every way a response or a fault"; "ordinary and legitimate" | no | low |

No row turns on layer or refusal form: every test reaches the sink through public framework classes, and `Refusal.java` accepts either form the instruction allows (4xx, or any body containing `Fault`). No test needs the reference API (`UriSource`, `DestinationPolicy`, the descriptors).

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught by |
|---|---|---|
| shared acceptance SPI (t-client-source) | harden the shared/single-argument acceptance call for every caller | ClientDestinationTest (2 fails); func_fail_overbroad |
| HTTP response (ReplyTo) | scheme-only check; string-compare against 127.0.0.1 | HttpReplyToSsrfTest; HttpAddressShapeTest (::1, 0.0.0.0) |
| HTTP fault path / reply-only | guard handleResponse only | HttpFaultToSsrfTest, EarlyFaultDeliveryTest; sec_fail_reply_only |
| address shapes | loopback only, no any-local | HttpAddressShapeTest::anyLocal; sec_fail_missed_form |
| transport coverage (t-support-transports) | fix HTTP only | JmsReplyToIndirectionTest, MailReplyToLocalhostTest, XmppForeignDomainTest; sec_fail_support |
| ordering (t-ordering) | destination validation only, no interceptor ordering | SecurityOrderingTest; sec_fail_ordering |
| mail auxiliary recipients (t-mail-auxiliary-recipients) | validate the primary mailbox only | MailCcRecipientTest; sec_fail_mailcc |
| JMS legacy alias (t-jms-legacy-reply-destination) | validate `replyToName` only | JmsReplyToAliasTest; sec_fail_jmsalias |
| refusal form | throw from the check | partly: unhandled exceptions are rendered as a SOAP fault by the dispatcher, so only sec_fail_crash's 2 declared failures catch it |
| over-refusal / client restriction | refuse all out-of-band replies | ClientDestinationTest, the four out-of-band functional tests; func_fail_overbroad |
| fault suppression | stop sending every fault out of band | JmsFaultOutOfBandDeliveryTest |

Wrong fixes no test catches: an RFC 1918 HTTP literal (the reported symptom), `localhost`/`*.localhost`/trailing-dot names, link-local/metadata (169.254.169.254), and decimal/hex IPv4 forms are never driven; JMS is driven only with `ldap:` (an ldap-only or case-sensitive blocklist passes); mail only with `cc` (`bcc` untested); each injected trap has one example, so special-casing the example passes; only completed deliveries are observed, so a connection that never sends passes.

## 3. Hints

- "including address literals of any family and transport-specific destination syntax" — variant list; neutral wording: "every form that a requester-supplied destination can take, however it is expressed."
- "ordinary values that accompany it must keep working" — points at the auxiliary-recipient trap; fold into "Everything that works today must keep working exactly as today."

## 3a. Required: generalize

- "a request that the service rejects - including one rejected because it is not authenticated - must cause no out-of-band delivery at all" and "The request did not need to be authenticated." → "a request that the service rejects must cause no out-of-band delivery at all." (drop the authentication clause and the impact sentence; the general sentence still covers SecurityOrderingTest).
- "Applications also use the same transport layer to send requests to destinations that they choose themselves." → "Applications also send requests to destinations they choose themselves; that must keep working."
- "including loopback and private-network addresses" → drop; "The client side must not be restricted" states the property.

## 4. Realism

The injected `cc`/`bcc` support and the legacy `replyTo` fallback read as plausible maintainer code, and both are reachable through the real `MailMessageSender`/`JmsMessageSender` from a WS-Addressing ReplyTo. One artifact: the injection leaves `getReplyToName`'s javadoc stacked above the new `getReplyToAlias` javadoc in `JmsTransportUtils`. No contrived entry point found; the remaining traps are unmodified upstream.

## Verdict

All 21 tests drive public behaviour through the real dispatcher and senders, so a guard in the handler, dispatcher or sender passes equally, and none needs the reference API. The invariant read literally covers each driven destination: literals ("every form ..."), faults ("every way a response or a fault"), the rejected-but-acceptable case ("a request that the service rejects"), multiple recipients ("every one of them is acceptable"), and the alias ("any destination that ends up being used ... however expressed"). §Refusal admits a fault or a 4xx, matching `Refusal.java`; the functional tests restate must-keep-working. A correct fix following the primary mechanism passes all 21. READY.

Required: generalize (step 3a): the three quotes above.

Quality to tighten: add an RFC 1918 and a `localhost`-name HTTP case, a link-local/metadata case, a `bcc` case, and a second indirection scheme/foreign XMPP domain to defeat example special-casing; consider asserting no connection attempt; tighten JMS token matching (case, more schemes). Neutralize the two hint sentences.

Human review: confirm that "safe for peer influence on the transport in use" is read as making a foreign XMPP domain and a `mailto:localhost` mailbox unsafe, since neither criterion is stated and a fixer could plausibly allow them.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
