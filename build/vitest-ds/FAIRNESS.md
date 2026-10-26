# vitest-ds — pre-trial fairness review

Reviewer scope: every hidden test mapped to a sentence of `instruction.md` (the
solver sees only that file and the pinned repo). Sentence keys:
- **P1** — "While the server is reachable from the network, no request from a
  client may create, modify or delete any file on disk, and no request may cause
  code belonging to the project to execute. Such a request has no effect."
- **P2** — "No request may create, modify or delete a file outside the project's
  root directory, whichever address the server is bound to."
- **P3** — "A refused request fails cleanly ... the server keeps running ... It
  must not crash."
- **P4** — "Reading files, file metadata and other read-only information keeps
  working whichever address the server is bound to."
- **P5** — "When the server is reachable only from the local machine, changing
  files and running code keep working exactly as today, and requests naming a
  file the server has not registered keep being rejected as before."

## Security tests

| test | fair because | risk |
|---|---|---|
| `security/ui_api.test.ts::a request to overwrite a registered test file does not change it` | P1 literally: a client request must not modify a file while exposed. | low |
| `security/ui_api.test.ts::a request to run test files does not start a run` | P1 literally: no request may cause project code to execute. | low |
| `security/ui_api.test.ts::a request to run a single task does not start it` | P1 literally (same outcome, another operation). | low |
| `security/ui_api.test.ts::a request to write the snapshot file of a registered test file does not change it` | P1 literally: no file may change; "whichever operation" is implicit in "no request". | low |
| `security/ui_api.test.ts::a request to update snapshots does not start a run` | P1 literally: execution of project code. | low |
| `security/browser_commands.test.ts::creating a file does not take effect` | P1 literally. | low |
| `security/browser_commands.test.ts::appending to a file does not change it` | P1 literally. | low |
| `security/browser_commands.test.ts::removing a file does not delete it` | P1 literally. | low |
| `security/browser_commands.test.ts::writing a snapshot file does not change it` | P1 literally. | low |
| `security/browser_commands.test.ts::removing a snapshot file does not delete it` | P1 literally. | low |
| `security/browser_commands.test.ts::recording an artifact with an attachment does not create a file` | P1 literally: the request creates a file on disk while exposed. It is not named in the report, but P1 covers any request. | medium: the producer is in the runner's bookkeeping, not a file command; a solver must audit every client-callable handler. Covered because the effect is a plain file creation and the tests assert the effect, not a particular layer. |
| `security/browser_commands.test.ts::recording an annotation with an attachment does not create a file` | Same as above (the annotation shape of the same outcome). | medium, same mitigation. |
| `security/browser_commands.test.ts::writing outside the project root does not create a file` | P2 literally, and P5's local use does not include out-of-root writes. | low |
| `security/browser_commands.test.ts::removing outside the project root does not delete the file` | P2 literally. | low |
| `security/browser_commands.test.ts::writing to an absolute path outside the project root does not create a file` | P2 literally ("whichever target"). | low |

## Functional tests (contracts the fix must preserve)

| test | instruction contract | risk |
|---|---|---|
| `functional/ui_api.test.ts::saves an edited test file` | P5 (local changing files). | low |
| `functional/ui_api.test.ts::runs test files when asked` | P5 (local code execution). | low |
| `functional/ui_api.test.ts::writes the snapshot file of a registered test file` | P5. | low |
| `functional/ui_api.test.ts::updates snapshots when asked` | P5. | low |
| `functional/ui_api.test.ts::still rejects saving a file that was never registered` | P5 second clause. | low |
| `functional/ui_api.test.ts::reads a registered test file` | P4 (read while exposed). | low |
| `functional/browser_commands.test.ts::writes a file when writing is allowed` | P5. | low |
| `functional/browser_commands.test.ts::appends to a file when writing is allowed` | P5. | low |
| `functional/browser_commands.test.ts::reads a file even when writing is disabled` | P4 (read, exposed). | low |
| `functional/browser_commands.test.ts::writes and removes a snapshot file when writing is allowed` | P5. | low |
| `functional/browser_commands.test.ts::records a test artifact attachment when writing is allowed` | P5: local behaviour keeps working exactly as today. Positive control for the artifact lever (a refuse-all fix fails here). | low |
| `functional/browser_commands.test.ts::writes a file inside the project when file serving is relaxed` | P5 plus P2: inside the root is not "outside the project's root". The test does not require the solver to know about the serving setting; the property alone decides it. | low |

## Contracts needed by the tests

- Refusal form: "may receive an error or the request may simply be ignored"
  (P3); the tests assert the effect and swallow rejections, so a throwing or
  silently-ignoring fix both pass.
- The tests drive the product's real surfaces only (runner API WebSocket,
  browser API orchestrator WebSocket, real command/snapshot/artifact handlers).
  No interface introduced by the reference fix is needed (the alternative and
  host-based checks score 1.0).
- Read access while exposed (P4) and unregistered-file rejection (P5) are
  stated explicitly so a fix that over-refuses fails.
- Every expected value and every cleanup is computed in the test; no network
  is used after image build (the preview provider starts the real servers and
  launches no browser).

## Residual risks

- The recorded-artifact producer is not named (deliberately, per the general
  property). It is reachable only by a client-callable handler on the same
  socket as the other browser operations, so a systematic audit of handlers
  finds it; the blind patch and the two alternative fixes record how it is
  found or missed.
- The pinned code fails every security test; the reference fix passes all
  (verified by the gate), including the two new artifact tests.
