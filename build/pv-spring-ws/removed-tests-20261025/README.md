XmppForeignDomainTest.java was removed from tasks/pv-spring-ws/tests on 2026-10-25: it required refusing delivery to a
foreign XMPP domain, which the instruction never states (it names only internal destinations as harmful, and the mail
tests require foreign-domain delivery). See build/pv-spring-ws/FAIRNESS-VALIDATION.md. All 7 runs were rescored
without it (common/audit/rescore_from_results.py); MiMo a4 became a solve, so the task is DeepSeek-only.
