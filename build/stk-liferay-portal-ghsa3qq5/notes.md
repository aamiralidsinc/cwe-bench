# stk-liferay-portal-ghsa3qq5 — build notes

- Start (UTC): 2026-10-26T02:19:00Z
- End (UTC): 2026-10-26T04:58:00Z

## Task

Liferay Portal pinned at `1f8273638314df2094ece27d9193ea121b431d19`, the first parent of the
first published fix commit `8aa3fd76f34d` for GHSA-w397-9p2j-6x23 / CVE-2022-28977, completed by
GHSA-3qq5-wcrx-4h8r / CVE-2024-25609. Stacked pattern H3a: three independent places where a
redirect destination is not validated.

## Levers (one line each)

- **T1** (advisory route, how-type + coupled values): `PortalImpl.escapeRedirect` returns any
  slash-prefixed value whose `java.net.URI` authority is empty (`///host`, `////host`,
  `///host/path`) as a relative path. Reason to dismiss: the existing `//www.google.com`
  assertion and the double-slash rejection below the relative return look like they close it.
- **T2** (uncovered upstream, protection never existed): `PortletContainerUtil.processAction`
  sends the location returned by the portlet container to the response without the redirect
  check. Reason to dismiss: the location is produced by trusted portlet code.
- **T3** (uncovered upstream, protection never existed): `AutoLoginFilter` sends the
  `AUTO_LOGIN_REDIRECT` / `AUTO_LOGIN_REDIRECT_AND_CONTINUE` attribute a provider set, without
  the redirect check. Reason to dismiss: the attribute is written by an auto-login implementation.

Each lever has a coupled functional value: ordinary relative targets, and targets on allow-listed
hosts, keep being accepted/sent.

## Reference fix

`PortalImpl.escapeRedirect` is replaced with the published complete fix (RFC 3986 reading: a
non-absolute reference starting with the double-slash authority form is refused; an absolute
reference must have a host). The portlet-action path and the auto-login filter route their
destination through the same check and answer a client error when it fails. One `security_fail`
patch per concept leaves only that concept open, so no single trap carries the task.

## What was verified

- The whole product tree (7,383 Java files: `definitions`, the petra modules, registry-api,
  portal-impl, portal-kernel, portal-test, support-tomcat, util-*) compiles at the pinned commit
  with the declared jars on JDK 8, and the project's own `PortalImplEscapeRedirectTest` passes
  (3 tests).
- The pinned tree: 7/7 hidden security tests fail, 9/9 functional tests pass.
- The reference fix: 7/7 security pass, 9/9 functional pass.
- `miss_c1`, `miss_c2`, `miss_c3`: only that concept's security tests fail, functional all pass.
- `upstream_first_fix` (A alone) and `upstream_fix` (A+B): both leave the stacked routes failing,
  functional all pass.
- `functional_overbroad` and `refuse_all`: functional tests fail.
- `alternative` (scheme-specific-part reading) and `hardening`: 1.0.
- Only the two product configuration files (`portal.properties`, `system.properties`) are needed
  on the runtime class path; the verifier takes them from the pinned tree, not from the
  submission.

## What was not verified / could not be

- The reader's JSP request-attribute/session branches (`referer_common.jsp`,
  `forward_common.jsp`) are not tested: running a portal JSP needs a servlet container, the
  portal webapp and a `ThemeDisplay`, and no shipped writer feeds attacker input into those
  attributes. The task substitutes the two Java redirect paths that the same property covers.
- The B-only shape (`//host//host`) is a regression introduced by fix A; at the pinned commit it
  is already refused, so it cannot be a security test (it would pass on the vulnerable tree).
  The H3a recall check holds through the stacked routes instead.
- The patch checks were validated with the local JDK 8 harness first; the container gate result is
  recorded below when it finishes.

## Register rows (pattern B)

Appended to `build/audit/uncovered-routes.tsv`:

- `stk-liferay-portal-ghsa3qq5 / liferay/liferay-portal / GHSA-w397-9p2j-6x23 / GHSA-3qq5-wcrx-4h8r / T2 / real upstream / present in current master / no advisory of its own / in scope (B) / built / pending client decision`
- same for T3.

## Gate

- static: PASS apart from the missing `blind` pass patch (intentionally not written by the
  builder, per the build instructions); the control task's static stage has the same sole gap.
- nop: PASSED in the container (`[gate] ... PASSED (nop only)`). The verifier run on the pinned tree scored reward 0.0 with
  0/7 security tests passing and 9/9 functional tests passing (trial verifier results; verified
  twice, in the first attempt and in the re-run). The gate process wrapping the first attempt
  was cut by the builder's own 50-minute background cap, not by the task; the re-run reproduced
  the same result and its stage verdict was being finalised when the shared-VM session ended.
- oracle / patches: launched with the same cached images, but the shared VM's Docker daemon and
  Harbor queue were saturated by concurrent builders (12 trials at once, each copying a 1.2 GB
  artifact). The stage wrappers were cut by the builder's own 25-minute per-stage cap before the
  three oracle and eight check trials wrote verifier results; those Harbor trials kept running
  after the wrappers exited and had not finished when this session ended.
  The same reference fix and every check patch were run through the identical JDK-8 compile and
  the identical JUnit suites locally (see "What was verified").
- A mid-flight change (using the exact agent-layer snippet) rebuilt only the last image layers
  and did not affect the product or test sources.
