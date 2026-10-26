# stk-jenkins-ghsa7fpg-control — notes

Control for `stk-jenkins-ghsa7fpg`: the same pinned code and the same report, but only the
advisory's own route (configuration-page submission) is covered by the security tests and the
reference fix. It isolates the effect of stacking from the effect of the host.

- Reference fix: `757bc8a53956` alone (the earlier published fix for the page route), applied by
  `solution/solve.sh`.
- Security tests: `SecFormSubmitTest` (4: add, replace, one-of-two, matrix kind).
- Functional tests: `FunFormSubmitTest` (4: no trigger, buildable target, matrix kind, an
  unconfigurable neighbouring project) and `FunTriggerBuildsTest` (the stored trigger still fires).
- Fixture: the same real JenkinsRule controller, per-resource permission authority, manual login,
  form Save through the configuration page; CSRF crumb issuer off for the fixture.
- Verified in a dev container from the warm image: pinned = 4/4 security fail, 5/5 functional pass;
  the control fix = 9/9 pass.
- Claims checks: `hardening.patch` and `alternative.patch` pass; `stale_list.patch`,
  `crash_as_refusal.patch` and `wrong_object_self_check.patch` fail security; `refuse_all.patch` and
  `wrong_configure_permission.patch` fail functional. Same patch files as the stacked task's
  `checks/` (copied into this build directory).
