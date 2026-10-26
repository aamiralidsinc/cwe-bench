# stk-ultrajson-480-control — build notes

- start: 2026-10-26T02:20:32Z
- end: (set at the end of the build)

Control for `stk-ultrajson-480`. The pinned code, the Dockerfiles and `instruction.md` are the same
byte for byte (the control has its own canary GUID in the image files); only the security tests and
the reference are narrowed to the advisory's own route.

## What differs from the stacked task

- Reference: the published fix only (`169eaf`), i.e. the three encoder arms (continuation byte,
  end-of-buffer bound, >U+10FFFF range). No decoder change and no key-branch test.
- Security tests (16): bytes values with a bad continuation byte, values truncated at the end of the
  buffer, and complete 4-byte values above U+10FFFF. Object keys and both decoder routes are absent.
- Functional tests: the same 32 functional cases and the same pristine project module and fixtures
  as the stacked task (411 cases after the free-threading test is filtered by name; the project's
  runner-only conftest is not copied, for the pytest 8.4 option-registration reason in the stacked
  task's notes).

## Verified

- `control_miss_range.patch` (the encoder continuation/bound fix without the range check) leaves the
  four range security tests failing and every functional test passing.
- `control_overbroad.patch` (the reference plus an ASCII-only bytes policy) breaks 23 functional
  tests while every security test passes.
- The reference applies with `patch -p1`, compiles, and scores 16/16 security and 411/411 functional.
- Static gate passes; `instruction.md` is identical to the stacked task's (check_stack rule 13).

## Could not verify

- Same limits as the stacked task's notes: the full advisory text was not available, and the
  decoder follow-up `d801f77` is outside this control's reference by design.
