# stk-nuclei-ghsajpvm — build notes

Start (UTC): 2026-10-23T02:58Z (this build job). End (UTC): see the report.

The task tree and the manifest had been lost after the 2026-10-22/23 attempt (task directory gone,
manifest gone, control task gone). This build recovered the verified task sources from the gate job
copy, regenerated the reference patch from the work checkout (5 files; the recovered solution patch
was the four-file missing-shadow check patch by mistake), reconstructed the manifest, rebuilt the
control task, and re-ran every gate stage.

## What the task is

Stacked H3b on projectdiscovery/nuclei, pinned at `b0998529` (the parent of the first published fix
`d2217320`). Protected data: text that entered from the scan target. Outcome: it is never rendered
or evaluated as template source against a map that holds process environment variables (`-ev`).
One general property in the report covers every route.

## Levers (one line each)

- **T1 — DAST/fuzz payload pipeline** (`pkg/fuzz/parts.go:194-199`, concept 1). Payload rendered,
  target-derived value substituted, result rendered again. Dismissal: the map looks like CLI
  variables; the second render reads as an interactsh helper.
- **T3 — interactsh sweep** (`pkg/fuzz/execute.go:222-258`, concept 1). Every fuzz value is
  evaluated, including request parts and internal-extractor values. Dismissal: interactsh-only
  helper that appears disabled.
- **T7 — ordinary response chaining** (`pkg/protocols/common/expressions/expressions.go:45-53`,
  concept 2). Placeholders substituted before expressions are collected, so substituted text is
  rescanned. Dismissal: ordinary chaining is a template feature and the report reads as DAST-only.
- **T5 — legacy placeholder pass** (`pkg/protocols/common/replacer/replacer.go:13-20`, concept 3).
  The legacy form is substituted in a second pass over the first pass's output. Dismissal: internal
  legacy syntax, so a brace-only fix looks sufficient.
- **S1 — declared-variable merge** (`pkg/protocols/common/variables/variables.go:80-95,114-140`,
  concept 4). A caller-supplied value that shadows a declared variable is rendered as template text.
  Dismissal: declared variables are legitimately overridable, so the merge reads as precedence.

Concepts: 4 independent edit sites: `{T1,T3}`, `{T7}`, `{T5}`, `{S1}`.
DeepSeek-type: T3, T7. MiMo-type: T5, S1 (T1 is both).

## Local verification (this session, Go 1.27.2 on the host)

Built the pinned tree, the reference, and every check patch, then ran the hidden Go modules locally
against a 127.0.0.1 target:

| variant | security | functional |
|---|---|---|
| pinned | 0/5 | 13/13 |
| reference (5 files) | 5/5 | 13/13 |
| sf-no-fuzz (reference minus fuzz fixes) | 3/5 (both fuzz tests fail) | 13/13 |
| sf-no-echo (minus expressions ordering) | 2/5 | 13/13 |
| sf-no-marker (minus single-pass renderer) | 3/5 (both legacy tests fail) | 13/13 |
| sf-no-shadow (minus variables merge) | 4/5 (shadow test fails) | 13/13 |
| upstream_first_fix (A's first commit alone) | 1/5 | 13/13 |
| upstream_fix (A+B equivalents) | 3/5 (legacy pair fails) | 13/13 |
| ff-refuse-all | 5/5 | 12/13 (`TestFuzzTargetMarkerValueStaysLiteral`) |
| pass-alt / pass-hardening | 5/5 | 13/13 |
| reference minus only the interactsh-sweep hunk | 3/5 (both fuzz tests fail) | not run |

Removing only the execute.go sweep hunk from the reference still leaves both fuzz security tests
failing, so the sweep route (T3) is exercised with `-ni` and is independently needed.

Control suite (4 fuzz-shape tests): pinned 0/4 and 13/13; control reference (expressions + fuzz
single render) 4/4 and 13/13; expressions-only fix 0/4 and 13/13; full stacked reference 4/4 and
13/13; ff-refuse-all 4/4 and 12/13.

Project tests for the affected packages pass at the pinned commit and on the reference:
`go test ./pkg/fuzz/... ./pkg/protocols/common/expressions/... ./pkg/protocols/common/replacer/...
./pkg/protocols/common/variables/...`.

The pinned tree holds none of the advisories' regression tests (`d2217320` added the integration
test and expressions test; they are absent at the pin).

## Control task

`stk-nuclei-ghsajpvm-control`: same pinned code, same instruction, same functional suite; the
security suite has the four advisory-route payload shapes only; its reference is the fuzz-path fix
(expressions ordering + fuzz single render, 3 files).

## History checks

- `upstream_first_fix.patch` (fix A's first commit, expressions only): expect fail — local 1/5.
- `upstream_fix.patch` (all published fixes as equivalents on this tree): expect fail — local 3/5.

The published commits cannot be applied literally: `ccbfb12` is based on a much newer tree and
`6c803c74` is a later descendant; `upstream_fix.patch` is the equivalent set on this tree.

## Not verified / guesses

- T4 (headless action-argument ordering) was dropped: its route needs a Chromium runtime and is
  slow and flaky under the 2-CPU verifier.
- `present_in_latest` for T3 is `unknown`; T5/T7/S1 were checked against a built v3.10.0 tree.
- `go vet`/`golangci-lint` were not run; only the affected package tests and builds.

## Gate

See REPORT.md (written at the end of this build).
