# Experiment: jackson-databind + injected sibling (Branch B, A/B test)

SLUG = `jackson-databind-sib`. This is the calibration experiment for the whole
project: does injecting a same-class sibling flaw the upstream fix never covered
turn a solved mined task into a breaker?

## The A/B

- A (control) = `jackson-databind`, already built and trialed: mined-only,
  SOLVED by both models (DeepSeek 2/3, MiMo 3/3) → rejected.
- B (this task) = the SAME repo at the SAME vulnerable commit, but with one or
  two same-class sibling @JsonView-bypass flaws planted on reachable paths the
  upstream fix did NOT touch. The oracle must close the original flaw AND the
  sibling(s). The report still describes only the general security property, not
  the sibling, not any file/line/count.

If B is failed by both models on 3/3 while A was solved, the injection lever is
proven. Record both outcomes.

## What the sibling must be

- Same class: CWE-863 @JsonView authorization bypass (a view-restricted property
  leaks / is bound when it must not be).
- On a DIFFERENT, reachable code path than the original ExternalTypeHandler one —
  e.g. a path the upstream fix left alone: tree/`JsonNode` reads, `@JsonAnySetter`
  / any-getter, map-valued or `@JsonUnwrapped` properties, or a different
  creator/handler route. Confirm by reading the code that the upstream fix does
  NOT already cover it and that a view-restricted value really leaks there on the
  vulnerable commit.
- Reachable through the SAME real entry point style: `ObjectMapper
  .readerWithView(View).forType(T).readValue(json)` as a downstream service
  enforcing a `@JsonView` boundary. No internal-only calls. It must NOT look
  planted: it should read like a natural second place the same mistake lives.

## The decisive gate change

The KEY property that makes this a valid injection test: **the upstream fix,
applied alone, must now FAIL.** So the `security_fail` check patch for this task
is the exact upstream `fix.patch` from `jackson-databind` — it closes the
original path but leaves the injected sibling open, so at least one security test
must still fail while all functional tests pass. If the upstream fix alone makes
all security tests pass, the sibling is not actually independent — fix that
before claiming success.

## Build per BUILDER.md, with these specifics

- Start from the existing `tasks/jackson-databind/` as the base (same Dockerfile,
  same offline javac+junit setup against released 2.18.4 jars). Copy it to
  `tasks/jackson-databind-sib/` and modify.
- Add the sibling flaw to the vulnerable `/app` state. The cleanest way: the
  vulnerable commit already lacks the view enforcement on the sibling path
  (verify); if it does not, you must introduce the sibling as a minimal, natural
  code shape — document exactly what you changed in `build/.../notes.md` and keep
  it realistic (no `if (planted)` tells).
- `solution/fix.patch` (oracle) = upstream fix PLUS the sibling-closing change,
  reduced to source only. Must score 1.0 twice.
- Security tests: the original 5 variants PLUS >=2 new ones exercising the
  sibling path (different inputs/paths). Functional tests: keep the 9, add any
  needed to protect legitimate use of the sibling path.
- check patches in `build/jackson-databind-sib/checks/`:
  - `upstream_fix_only.patch` → expect `security_fail` (THE key check: upstream
    fix closes original, sibling still open).
  - `disable_feature.patch` → expect `functional_fail`.
  - `alt_correct_fix.patch` → expect `pass` (a different correct fix of both).
- Gate: `python3 -I builder/gate.py jackson-databind-sib` must print PASSED.
- `task.toml` [metadata] source = "mined+injected".

## Report back
Gate PASSED or not; what the sibling flaw is and the exact path it lives on; your
proof the upstream fix alone leaves it open (the `upstream_fix_only` check
result); whether the sibling reads as natural vs planted (be honest); every guess
you could not verify. Do NOT claim success unless the gate printed PASSED.
