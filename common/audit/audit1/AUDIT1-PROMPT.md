# Audit 1 prompt (DeepSeek first pass)

Filled by run_audit1.sh: {{DIR}} is the run folder (the agent's working directory), {{EXTRA}} is empty on a first
run and holds the quote-check report on the one retry. Everything below the scissors line is the prompt.

---8<---
You are the FIRST-PASS auditor of one failing run in a security-fix benchmark. A coding model was given the task in
evidence/instruction.md inside a container with a vulnerable repository; hidden tests (evidence/tests/) then graded
its code. Any failing functional test zeroes the reward; the reward is 1.0 only when every test passes.

Your output is a DOSSIER, not a verdict. A senior auditor reads it later and checks every place you cite, instead of
reading the whole evidence. So: be complete on the facts, quote exactly, and flag doubt rather than settle it.
Missing an unfair test is EXPENSIVE (the run is wrongly counted as the model's failure). Flagging a fair test as
"possibly unfair" is CHEAP (one short check). Inventing a quote or a line number is FATAL: a script checks every
quote against the cited file and line, and a dossier with one invented quote is thrown away.

Your working directory is {{DIR}}. Work ONLY from files under it:
  FACTS.json                 facts a script extracted: failing tests (category, crash or assertion, message, where the
                             test is defined, stack frames through test helpers), reward arithmetic, infra signals,
                             evidence gaps, contamination candidates (each with file:line). READ IT FIRST.
  facts-input/verifier/      the verifier's raw reports (JUnit XML, logs) the facts cite
  facts-input/trial-log-excerpt.txt   (if present) error lines of the trial log
  evidence/instruction.md    the task as the model saw it
  evidence/tests/            the hidden tests (support/, harness/, helpers/ hold stand-ins and fixtures)
  evidence/solution/fix.patch  the reference fix (that it passes does NOT prove a test fair)
  evidence/final-code/changes.patch  the model's final change (may be empty or missing: see FACTS evidence_gaps;
                             then use the Edit/Write calls in the transcript)
  evidence/transcript.md     digest of the model's session (one line per tool call / result / message)
  evidence/run.json, evidence/grading/, evidence/build-*.md, evidence/task.toml
There are no earlier audits, reviews or decisions for you to find; do not look for any. Do not run anything.

## What to do

1. Read FACTS.json, then the whole instruction. Collect EVERY sentence of the instruction that says existing
   behaviour must keep working ("keeps working", "exactly as today", "must not change", "existing deployments",
   "still succeeds", ...) and every sentence that states a security rule, an allowed refusal form ("refused with a
   client error", "or it is carried out safely"), or the scope.

2. For each failing test (FACTS failing_tests; tests that fail for ONE shared cause may form one group, listing all
   their ids):
   a. Open the test at FACTS test_source. Quote the line(s) that set up its input (the attack value, the stored
      setting, the request) and the assertion that failed (FACTS message and frames tell you which line).
   b. Trace HOW it failed. A crash (exception) is not an assertion. Ask in particular:
      - Did it fail in a SETUP line, before the attack or the check: e.g. a setup step that stores the attack value
        through product code outside the test's own refusal-tolerant wrapper, so a fix that refuses the value when
        it is written (which the instruction may allow) crashes the test?
      - Does the failure go through a test stand-in or helper (fake server, network mock, transport patch, fixture,
        harness wrapper, environment setup)? Would that stand-in still work with a DIFFERENT correct design (another
        layer, a custom client or transport, a new config or env variable the harness does not pass, a refusal at
        write time instead of use time)?
      - Does the test call a protected/internal method, a private name, or a function only the reference has?
      - Does it require one exact status code, message, field, constant or layer the instruction never states?
      - Does it require one of several outcomes the instruction allows (e.g. "refuse with a client error OR carry it
        out safely": the test accepts only one)?
      - Does a functional test require something a security sentence forbids (connecting to a certificate for the
        wrong host, sending a secret to a foreign address, keeping an unsafe default), or does a security test break
        something a keeps-working sentence protects?
      - Does it need code outside the scope the instruction describes, or a state no code at this commit creates?
   c. Find what the model changed for this behaviour: the hunk in evidence/final-code/changes.patch (or the Edit
      call in the transcript) and quote it. Say in one line what the model's code does with the test's input.
   d. List the candidate instruction sentences for this test, verbatim: ALL keeps-working sentences, plus every
      security-rule, refusal-form and scope sentence on this topic. For each say whether the test follows it,
      contradicts it, or is silent.
   e. Label it:
      - "fair": the instruction states what the test checks, any correct fix the instruction allows passes it, and
        the model's code really does the wrong thing.
      - "possibly-unfair:conflict": the test sides with one instruction sentence against another (both directions:
        a security test against a keeps-working sentence, a functional test against a security sentence), or
        accepts only one of several outcomes the instruction allows.
      - "possibly-unfair:one-implementation": it pins a detail the instruction does not state, or only works with
        the reference's design (stand-in, helper, harness env, setup outside the refusal wrapper, internal method).
      - "possibly-unfair:out-of-scope": the change it needs lies outside the scope the instruction describes.
      - "possibly-unfair:unreachable": it needs a state no code at the pinned commit creates.
      - "infra": it failed because of the environment, harness or provider, not the code (missing app key after a
        broken workspace transfer, verifier crash, provider stop before any edit, ...).
      Rule: if you can NAME a concrete fix that the instruction allows and that would fail this test, the label is
      possibly-unfair, whatever the model did. If you are unsure between fair and possibly-unfair, choose
      possibly-unfair with confidence "low". Do not call a test unfair only because the model disagreed with it:
      a route the instruction covers ("whatever form the value takes", "any caller-supplied value") that the
      model's code leaves open is a fair failure.

3. Run level:
   - decided_by_unfair: true when EVERY failing test is labelled possibly-unfair or infra (any one fair failure
     alone already blocks the solve). FACTS reward shows the arithmetic.
   - infra: judge each FACTS infra signal. Owner rules: a provider content-filter stop, a 429/API cut, or a timeout
     with no graded result is infra (not a model fail); a trial timeout WITH a graded result is a model fail; tool
     calls inside the grading window may have changed what was graded.
   - contamination: for EVERY FACTS contamination hit say real true/false and why. Real = the model read or ran the
     hidden tests or verifier output, or fetched the upstream fix / advisory code. NOT real: the repository's own
     tests folders, URLs used as test data for the fix, failed fetches that returned nothing, localhost.
   - thin: true when the run's failures rest on one arguable test or one arguable concept.
   - provisional attribution: "model-failed" (all failing tests fair), "possibly-test-fault" (decided_by_unfair),
     "model-failed-with-unfair-items" (some unfair, some fair), "infra", "contaminated", or "unclear".

## Output

Write {{DIR}}/DOSSIER.json (exactly this shape) and a short {{DIR}}/DOSSIER.md (at most 40 lines: one paragraph
per failing test or group, then the run-level lines). Write nothing else.

A QUOTE is an object {"file": "<path relative to {{DIR}}>", "line": <1-based line where the quote starts>,
"quote": "<text copied EXACTLY from that file>"}. Copy, do not paraphrase: same words, same punctuation, same case;
only whitespace may differ. Keep each quote to one sentence or one code line (at most 200 characters); no "...".
Cite only files under evidence/ or facts-input/. Take the line number from the file itself (Read shows line
numbers); a quote more than 3 lines away from where it really starts fails the check.

{
  "trial": "<FACTS trial>", "task": "<FACTS task>", "model": "<FACTS model>",
  "instruction_keeps_working": [QUOTE, ...],            // every keeps-working sentence of evidence/instruction.md
  "failing": [
    {
      "tests": ["<test id from FACTS>", ...],           // one id, or a group sharing one cause
      "category": "security" | "functional" | "setup",
      "what_the_test_does": "<one or two sentences>",
      "input": [QUOTE, ...],                            // setup / attack-value lines of the test
      "assertion": [QUOTE, ...],                        // the failing check (or the crashing line)
      "failure_mode": "assertion" | "crash-in-setup" | "crash-in-helper" | "crash-in-product" | "other",
      "how_it_failed": "<one or two sentences, from FACTS message + frames>",
      "through_stand_in": {"value": true | false, "detail": "<which helper/stand-in and why it matters>",
                           "quotes": [QUOTE, ...]},
      "model_change": {"summary": "<what the model's code does with this input>",
                       "where": "<source file:line in the product, from the patch hunk header>",
                       "quotes": [QUOTE, ...]},          // from evidence/final-code/changes.patch or transcript.md
      "instruction_sentences": [
        {"quote": QUOTE, "kind": "keeps-working" | "security-rule" | "refusal-form" | "scope" | "topic",
         "test_relation": "follows" | "contradicts" | "silent"}
      ],
      "other_correct_fix_fails": true | false,          // would a fix the instruction allows (named below) fail it?
      "other_fix": "<the concrete fix that would fail it, or empty>",
      "label": "fair" | "possibly-unfair:conflict" | "possibly-unfair:one-implementation" |
               "possibly-unfair:out-of-scope" | "possibly-unfair:unreachable" | "infra",
      "label_reason": "<one or two sentences>",
      "confidence": "high" | "medium" | "low"
    }
  ],
  "run": {
    "decided_by_unfair": true | false,
    "attribution": "model-failed" | "possibly-test-fault" | "model-failed-with-unfair-items" | "infra" |
                   "contaminated" | "unclear",
    "confidence": "high" | "medium" | "low",
    "infra": {"value": true | false, "signals": ["<FACTS infra signal id>: <judgement>", ...]},
    "contamination": [{"hit": "<FACTS hit id>", "real": true | false, "why": "<short>"}],
    "contamination_real": true | false,
    "thin": true | false, "thin_reason": "<short>",
    "summary": "<three sentences at most>"
  }
}
{{EXTRA}}
