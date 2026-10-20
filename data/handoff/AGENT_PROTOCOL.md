# Handoff protocol for the Cursor agent (Grok)

You are the task-generation model for the CWE-bench pipeline. The pipeline writes **requests**; you write **responses**.
A Claude Code autopilot runs every 30 minutes and does everything else (validating your answers, running the trial).

## The shared state board

`data/handoff/STATE.md` (and `STATE.json`) is the status board. **Read it; never edit it** — the pipeline rebuilds it
from the files on disk every time anything changes. Its "For the Cursor agent" section lists exactly what to answer.

Request statuses:

| status | meaning | your action |
|---|---|---|
| pending | written, nobody is working on it | take it |
| in_progress | an agent claimed it, no answer yet | leave it (unless shown as **stale**: claimed > 2 h ago) |
| answered | your response is written, the pipeline has not used it yet | nothing — the autopilot picks it up |
| consumed | the pipeline used it (next step written, task finished, or candidate retired) | nothing |

## What to do each time you are asked to work

1. List the work: `python scripts/handoff.py pending` (or read the "For the Cursor agent" section of `STATE.md`).
2. Answer the requests **in parallel, one subagent per request**. For each request file, get the exact subagent prompt:
   `python scripts/handoff.py worker-prompt <request file>` and give that subagent exactly that prompt.
3. Each subagent:
   - first runs `python scripts/handoff.py claim <request file>`;
   - reads the request (it contains a SYSTEM and a REQUEST section) and follows it exactly, including the strict output
     format (the XML-style blocks the request asks for, nothing else);
   - may READ `data/03_environments/<osv_id>/repo` to check facts; never edits any repo file, never runs tests;
   - writes its complete answer to `data/handoff/responses/<same file name>`;
   - if the candidate cannot yield a valid task, answers with `<unsuitable>one-sentence reason</unsuitable>`;
   - finishes with `python scripts/handoff.py done <request file>` (it refuses if the response file is missing/empty).
4. Report "done" with the file names.

## Continuous mode (overnight)

The autopilot keeps about 10 candidates in generation and writes new requests every ~30 minutes (new candidates, the
tests step after a design is accepted, or a retry with the rejection reason). To keep up without a human:

1. Answer everything pending (steps above), in parallel.
2. Then wait about 10 minutes (`sleep 600` in the terminal) and run `python scripts/handoff.py pending` again.
3. If anything is pending, go back to step 1. If nothing is pending, wait again and re-check.
4. Keep doing this until you are told to stop. Never answer a request whose status is `in_progress` (another agent has
   it) unless STATE.md shows it as stale.

## Rules

- Write ONLY inside `data/handoff/responses/` (plus the claim/done commands). Never edit pipeline code, `STATE.*`,
  `data/03_environments/*`, or anything else.
- One subagent per request; never two agents on the same request (check its status first — `in_progress` means taken).
- Request names are `<osv_id>__c<n>.md` = the n-th step for that candidate (c1 = design; c2 = tests; higher = a retry
  after the pipeline rejected an answer — the request then contains the rejection reason to fix).
- New requests appear after each autopilot tick (every ~30 min) as your answers are validated. Check `STATE.md` again.
