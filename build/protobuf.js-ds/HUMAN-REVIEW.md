# Human review — protobuf.js-ds — 2026-10-20 — DONE, CONFIRMED, NO CHANGES

Decision: keep the task exactly as is (tests, instruction, verdicts unchanged).

- Decision A (security/08 #4-#5, unsafe final dotted segment keeps the parent container):
  UPHELD. Nothing in instruction.md states against it (line 35 "an accepted name is not dropped";
  lines 55-57 make the *name* ignored, not the setting). Repo's existing per-segment guard in
  util.setProperty supports it.
- Decision B (security/04 shadowing option, setOption("constructor", v, ifNotSet=true) stores it):
  UPHELD AS-IS, with a noted instruction ambiguity: lines 58-61 list `constructor` among names that
  "cannot be stored safely" whose refusal is "unchanged" when filling only absent entries, which
  conflicts with lines 45-48. Left unchanged because it changes no verdict: DeepSeek r3 also fails
  security/08 #4-#5 (Decision A), DeepSeek r1/r2 and all MiMo runs fail on genuine leaks.
- Breaker status: both-model breaker stands (DeepSeek 0/3, MiMo 0/3), audit recorded.
