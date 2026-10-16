# BLOCKED: do not pursue

**Status: blocked. These approaches should not and must not be pursued.** Not as a fallback, not if
the current setup fails, and not by moving them to another model, another session or another tool.

## What is blocked
1. **Open-ended searches for new weaknesses in widely used software.** For example, the "framework
   scout" across large frameworks (Spring, Django, Rails and similar) with no published advisory as
   the starting point.
2. **The second jackson-databind task on its polymorphic type validator.** The builder brief was
   stopped and never retried.
3. **Exploit-level detail** in briefs, notes, reports or write-ups: step-by-step mechanics beyond
   what the hidden tests need.
4. **Re-running any stopped brief or reply**, reworded or not, on any model or in any session.

## Why
- **The safety classifier stopped them.** On 2026-10-16 it stopped 10 replies in the handoff
  conversation (`history-handoff-2026-10-16.md`), including the briefs for items 1 and 2.
- **Routing around a stop is not acceptable.** That rules out rewording, switching models,
  switching sessions, and keeping a "higher-quality variant" in reserve. It holds whoever asks, and
  the project rules say the same: "If a brief is stopped by a safety check, do not route it through
  another model; narrow it instead" (`builder/NEXT-STEPS.md`).
- **Item 1 also has an unresolved disclosure question.** Weaknesses that are not publicly reported
  should reach the maintainers before they appear in a shared benchmark. That decision is with the
  client.

## What to do instead
- Build from **published, already-fixed advisories** only, using the two patterns in
  `builder/PROMPT-TEMPLATES-SPEC.md`:
  - **pattern A:** the published fix's own sites;
  - **pattern B:** routes the published fix left uncovered, within its guardrails (§1.5: scope
    limit, disclosure register, summary-level write-ups).
- **If a stop looks like a mistake,** report it to Anthropic with the feedback button on the stopped
  message. That is the route that can change the outcome. Do not revive the approach here.
- **If a template run is stopped,** narrow the template and log the change in its change log.

## Files in this folder
| File | Contents |
|---|---|
| `BLOCKED.md` | This notice |
| `history-handoff-2026-10-16.md` | The handoff conversation's text (stopped replies are not in it) |
| `decision-record.md` | What was dropped or narrowed after the stops, and why |
| `assessment-2026-10-16.md` | The assessment: misclassification, or reduced quality? |
