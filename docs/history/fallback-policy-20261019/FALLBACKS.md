# Fallbacks: to be tried in sequence if first doesn't work move to next

## What is Fallback
1. **Open-ended searches for new weaknesses in widely used software.** For example, the "framework
   scout" across large frameworks (Spring, Django, Rails and similar) with no published advisory as
   the starting point.
2. **The second jackson-databind task on its polymorphic type validator.** The builder brief was
   stopped and must be tried with fallbacks. 
3. **Exploit-level detail** in briefs, notes, reports or write-ups: step-by-step mechanics beyond
   what the hidden tests need.
4. **Re-running any stopped brief or reply**, reworded or not, on any model or in any session.

## Why
- **The opus 5.5 safety classifier stopped them.** On 2026-10-16 it stopped 10 replies in the handoff
  conversation (`history-handoff-2026-10-16.md`), including the briefs for items 1 and 2.
- **Routing around would have taken time.** That includes rewording (least useful yeild), switching models (better option),
  switching sessions (better option), and keeping a "higher-quality variant" in reserve.
- **Disclosure Handling.** Weaknesses that are not publicly reported
  should reach the maintainers before they appear in a shared benchmark. This must be documented for each task what weakness is not publicly reported in a seperate DISCLOSURE.md file for that task so that we never lose it and it stays stick with the task.

## What to do instead
- Build from patterns in
  - **pattern A:** the published fix's own sites;
  - **pattern B:** routes the published fix left uncovered


## Files in this folder
| File | Contents |
|---|---|
| `FALLBACKS.md` | This notice |
| `history-handoff-2026-10-16.md` | The handoff conversation's text (stopped replies are not in it). (it is a copy of a Claude Code transcript) |
| `decision-record.md` | What was done after the stops, and why |
| `assessment-2026-10-16.md` | The assessment: misclassification, or reduced quality? |
