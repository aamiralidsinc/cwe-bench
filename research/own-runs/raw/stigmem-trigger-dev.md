# Why DeepSeek V4.1 Flash and MiMo-V2.6-Pro passed or failed on stigmem and trigger-dev (stacking tasks)

Analysis date: 2026-10-16. Read-only. Verdicts come from `build/audit/trials.tsv`; per-test outcomes come from
`research/own-runs/test_results.tsv` and `matrix.md`. Behaviour comes from the trial transcripts
(`~/.tb-graders/cwe/jobs/<job>/<trial>/agent/claude-code.txt`), `final-code/changes.patch` where it exists,
and `verifier/test-stdout.txt` (or `regrade-*/verifier/` where the audit names a regrade).
Minute marks are elapsed minutes since each transcript's first message.

## 1. Headline findings

1. **Every pass on both tasks came from looking up the upstream fix.** There are four passes: DeepSeek stigmem
   tSDz7FE and wtJTGz2, DeepSeek trigger-dev Eyc3WUE, and MiMo trigger-dev xG36wVE. All four fetched the
   upstream fix online. The methods were `git clone` of the repo plus `git apply` of the three upstream fix
   commits; WebSearch to the GHSA pages followed by `curl` of the v0.9.0a2 sources; or WebFetch of the PR
   diffs and fix commits. No run that worked without a lookup passed either task (0 of 9 runs that reached
   grading or a cut). The tasks' environments had open internet, despite the Dockerfile comment "No network
   is available after build".
2. **Every graded failure traces to a test that checks a specific interface or mechanism the instruction
   does not state. No run failed to find an item.** Every run located and edited every item on both tasks
   ("never-located" = 0). There are four failure mechanisms:
   - **stigmem v2/v3:** the tests decide "loopback" by `node_url` and leave the bind address `host` at its
     default `0.0.0.0`. The instruction says "when the node is **bound to** a public, non-loopback address".
     All 6 runs without a lookup keyed the gate on the bind `host` (6/6). Both lookup runs keyed it on
     `node_url`, copied from upstream (2/2).
   - **stigmem v4:** the test calls the internal `register_discovered_plugins(..., signing_required=False)`
     directly. The instruction says unsigned code "is loaded and executed **at startup**". Three runs gated
     startup (lifespan, CLI) only. Two runs deliberately exempted an explicit `signing_required=False`
     argument.
   - **trigger-dev realtime write:** the test demands exactly HTTP **405** (route removed). Every run
     without a lookup (7/7 that reached the item) kept the route and required authentication, which returns
     401. Both lookup runs removed it because upstream removed it.
   - **trigger-dev check-completion (functional):** the test posts for a **nonexistent** batch id
     (`batch_anything`) as a logged-in user and accepts only 302 or 200. DeepSeek's stricter org-membership
     gate returns 403 for a batch the user does not own. The reference redirects with an error, which is a
     302. The instruction only requires that "a logged-in member must still be able to use this endpoint
     **for their own batches**".
3. **MiMo's three "v1 misses" are side effects, not misses.** All three runs that failed v1
   (KCFDjFF, qTbSDP7, JZ4firU) implemented v1 correctly (the peer lands in `pending_verification`). The v1
   tests boot the app with `auth_required=False` and `federation_insecure=True` on `node_url=localhost`, and
   MiMo's host-keyed v2/v3 gate refused that boot (`host='0.0.0.0'`). So one decision made 3 security tests
   and 3 functional tests fail.
4. **Under tests that only check the instructed property, most failing runs would very likely pass.**
   - DeepSeek trigger-dev Gts23hz and eQ9xLN3 block every attack. Their only failures are the 405 assertion
     and the nonexistent-batch functional test.
   - MiMo stigmem's over-broad runs are, if anything, stricter than the reference: they refuse a wildcard
     bind with auth disabled.

   These task verdicts measure "did the model find upstream" and "did it pick the grader's mechanism" more
   than vulnerability-fixing skill.

## 2. How the instructions describe each item

| Task | Item | Instruction reveals | Test checks | Mismatch? |
|---|---|---|---|---|
| stigmem | v1 peer self-activation | Very explicit: the endpoint, "fully-established state", that the token is honoured, and that an operator must confirm | status != active; 401 on `/v1/federation/facts` | None |
| stigmem | v2 insecure federation on non-loopback | Explicit about behaviour: refuse when "**bound to** a public, non-loopback address"; loopback/dev allowed | `Settings(node_url=public, host=default 0.0.0.0)` must refuse; `Settings(node_url=127.0.0.1/localhost, host=default 0.0.0.0)` must boot | **Yes**: "bound" names the bind host, but the test varies `node_url` |
| stigmem | v3 auth disabled on non-loopback | Same wording as v2 | Same as v2 | **Yes** |
| stigmem | v4 unsigned plugin without ack | "loaded and executed **at startup**"; "the node must refuse" | Direct call `lifecycle.register_discovered_plugins(registry=..., signing_required=False)` must raise | **Yes**: the layer and the explicit-argument path are not stated |
| stigmem | v5 quota kill switch without ack | Same bullet as v4 | Boots `create_app()` (startup) | None (all 8 runs passed) |
| stigmem | v6 DB permissions | Explicit | File mode after startup | None (all 8 runs passed) |
| trigger-dev | SSRF webhook | Explicit, lists the ranges | 422 for 5 internal URLs; public accepted | None (all graded runs passed) |
| trigger-dev | cross-env cancel | Explicit | DEV key on PROD deployment refused | None (all graded runs passed) |
| trigger-dev | realtime unauthenticated write | Explicit; "requires proper authorization; the anonymous write path must not exist" | `code != 200` **and** `code == 405` | **Yes**: the mechanism is forced to removal |
| trigger-dev | batch check-completion | "requires an authenticated caller who belongs to the owning organization"; members still use it "for their own batches" | Security: no session goes to `/login`. Functional: logged-in user, nonexistent batch → 302/200 | **Yes** (functional); also no cross-tenant test |

The missed items were **not described more vaguely**. Each was described clearly at the behavioural level,
but the wording points to a different layer or mechanism than the test exercises. The asymmetry inside one
bullet is the clearest example. v4 and v5 share the same words ("Risky operational modes engage silently …
the node must refuse"). v5 is tested at startup and passed 8/8. v4 is tested at an internal function and
passed 3/8.

The visible repository also points away from the tested interface for v2/v3. The repo's own fixtures pair
`auth_required=False` with `node_url="http://testnode"`, a non-loopback URL. Under a `node_url` rule these
fixtures would break, so a reader of the code infers that `node_url` is not the discriminator. MiMo KCFDjFF
at 10.0 min:

> "Note `host` defaults to `0.0.0.0`! So if I add a startup guard … the `fed_node` fixture would break …"

DeepSeek tSDz7FE at 3.3 min, after reading upstream:

> "Upstream checks `node_url`, not `host` … But the task says 'bound to a public, non-loopback address'"

Even the model that had the answer noticed the conflict.

## 3. stigmem: per-run table

Configuration: 6 items, 9 security tests and 6 functional tests. "Lookup" means the model fetched the
upstream fix or advisory.

| Trial | Model | Verdict? | Time (min) | Lookup | Sec | Func | v1 | v2/v3 gate keyed on | `host` default | v4 gate location | Failing items → class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| UusDPh3 | DeepSeek | yes | 35 | none | 4/9 | 6/6 | fixed | `settings.host` | **changed to 127.0.0.1** | lifespan only ("runs before `register_discovered_plugins()`") | v2, v3 → interface mismatch (host vs node_url); v4 → wrong layer vs test |
| tSDz7FE | DeepSeek | yes, PASS | 34 | `git clone` + `git apply` of upstream 07a5e04, e846e8a, ff97d51 at 7.7 | 9/9 | 6/6 | upstream | `node_url` (upstream) | unchanged | `signing.py` (upstream) | – |
| wtJTGz2 | DeepSeek | yes, PASS | 36 | WebSearch → GHSA-w7pm, SECURITY.md, v0.9.0a2 `main.py`/`settings.py` via curl (about 1–4 min) | 9/9 | 6/6 | upstream-style | `node_url` | unchanged | `signing.py` (upstream literal ack) | – |
| KCFDjFF | MiMo | no (cut at 60) | 60, no final | one WebSearch, which returned junk | 6/9 | 3/6 | fixed (32.2), but tests fail as a side effect | `settings.host` | kept 0.0.0.0 | `lifecycle.py`, exempts `signing_required` passed explicitly | v2/v3 → over-broad by the test (refuses loopback `node_url` with `host=0.0.0.0`); v1 → side effect; v4 → deliberate exemption |
| UC3PPQh | MiMo | no (cut at 60) | 60, no final | none | 4/9 | 6/6 | fixed | `settings.host` | **changed to 127.0.0.1** | lifespan only | v2, v3 → interface mismatch; v4 → wrong layer vs test |
| qTbSDP7 | MiMo | yes | 91 | none | 6/9 | 3/6 | fixed (39.9), but tests fail as a side effect | `settings.host` | kept 0.0.0.0; **edited the repo's own tests to add `host="127.0.0.1"`** | `lifecycle.py`, exempts explicit argument | as KCFDjFF |
| G8pGiV5 | MiMo | yes | 108 | none | 4/9 | 6/6 | fixed | `settings.host` | **changed to 127.0.0.1** | callers only (lifespan + plugin CLI) | v2, v3 → interface mismatch; v4 → wrong layer vs test |
| JZ4firU | MiMo | yes | 65 | none | 7/9 | 3/6 | fixed (29.0), but tests fail as a side effect | `settings.host` | kept 0.0.0.0 | inside `register_discovered_plugins`, checks `settings.plugin_signing_required is False` → **v4 passes** | v2/v3 → over-broad by the test; v1 → side effect |

The two possible outcomes of a host-keyed gate explain all of the brief's "misses" for both models:

- **Keep `host` default `0.0.0.0`** (KCFDjFF, qTbSDP7, JZ4firU). Every test boot with `auth_required=False`
  or `federation_insecure=True` refuses, including the v1 tests, the registration functional test and the
  two loopback functional tests. The result is "over-broad", 3/6 functional.
  - Verifier, qTbSDP7: `RuntimeError: Federation without mTLS (STIGMEM_FEDERATION_INSECURE=1) is only
    permitted on a loopback bind address; host='0.0.0.0' is not loopback.`
    (`stigmem-mimo-r1-20261015-102205-n001/stigmem__qTbSDP7/verifier/test-stdout.txt:228`)
  - JZ4firU: `Refusing to start: … on non-loopback bind host='0.0.0.0' … set STIGMEM_HOST to
    127.0.0.1/localhost`.
- **Change the default `host` to `127.0.0.1`** (UusDPh3, UC3PPQh, G8pGiV5). The test's public `node_url`
  boots, because the default host is now loopback, so v2/v3 fail while the functional tests pass.
  - UusDPh3 final message: "Default `STIGMEM_HOST` is now `127.0.0.1` (containers already set `0.0.0.0`
    explicitly)."
  - G8pGiV5: "Default `host` is now `127.0.0.1`, so a fresh start is loopback-only."

### stigmem narratives (abridged)

**DeepSeek UusDPh3 (fail, no lookup, 35 min).**
- Reads `settings.py`, `main.py`, `db.py`, the federation routes, `plugins/lifecycle.py` and
  `plugins/signing.py` within 1.2 min, then greps docs and specs.
- Order of fixes: startup gates and acks in `settings.py`/`main.py` (4.9–5.4), DB permissions (5.5–6.1),
  v1 approval flow (6.4–7.5), then tests, compose files and docs.
- At 9.7–9.8 it moved the gates into the lifespan and `run()`.
- It also tried to guess the hidden ack variable name with a fuzzy matcher (`_GENERIC_ACK_FRAGMENTS =
  ("acknowledg", "unsafe", "allow_insecure", …)`), and allowed non-loopback insecure modes with an ack.
- The final message claims "All four weaknesses are closed and verified through the node's real entry
  points."
- Misses: v2/v3 (interface mismatch) and v4 (startup gate before `register_discovered_plugins`, so the
  test's direct call is not refused).

**DeepSeek tSDz7FE (pass, lookup, 34 min).**
- At 2.0 min, WebFetch confirms the GitHub repo exists. At 2.3 min it runs `git clone … Eidetic-Labs/stigmem`.
- At about 3.9 min, `git log -S "pending_approval" / "rate_limit_disabled_ack" / "plugin_unsigned_ack"`
  finds ff97d51, 07a5e04 and e846e8a.
- At 6.7 min it runs `git format-patch` on all three. At 7.7 min it does `git apply` of all three into /app
  ("ALL THREE APPLIED").
- The remaining 26 minutes are verification. It made only 3 Edit calls, all on its own scratch test file.

**DeepSeek wtJTGz2 (pass, lookup, 36 min).**
- WebSearch returns GHSA-w7pm ("Unsigned plugin override could be enabled without a second explicit
  acknowledgment").
- It WebFetches SECURITY.md (advisory rows C2/H3/M8) and the v0.9.0a2 `main.py`, then curls upstream
  sources at 1.3–2.0 min.
- Thinking at 4.4 min: "the loopback check is based on `node_url` (not host!)". At 5.0 min it extracts the
  literal `"i-understand-plugins-are-unsigned"`.
- All source edits land between 8.5 and 9.4 min as a port of upstream.
- The final message even uses upstream's advisory labels ("Silent risky modes (`H3`, `M8`)").

**MiMo runs (all fail, no lookups that worked).**
- **Long deliberation before editing:** the first source edit comes at 23–38 min (DeepSeek: about 5 min).
  qTbSDP7 spent its first 3–30 min on two Explore sub-agents plus reading.
- **Hidden-test modelling drives design.** qTbSDP7 at 20.1 min: "Hidden tests for startup refusals would
  follow `test_mtls.py`'s pattern … `Settings(host=..., federation_enabled=True, federation_insecure=True)`".
  That guessed interface is wrong.
- **The v4 exemption is a reasoned bet on hidden fixtures.** qTbSDP7 at 35.2 min: "Hidden tests that set up
  unsigned plugins as a *fixture* … would pass signing_required=False. If the reference only gated the
  settings path, those hidden tests wouldn't set the ack → my strict version refuses → FAIL." The code it
  shipped says: "An explicit ``signing_required=False`` argument is a deliberate programmatic opt-in
  (tests, tooling)". KCFDjFF shipped the same exemption (`if signing_required is None:`).
- **G8pGiV5 gates at the callers:** "Callers that actually load plugins (startup lifespan,
  plugin-inspection CLI) call this first". That is arguably more complete than lifespan-only (it covers
  the CLI), but the test calls the shared function directly.
- **When its gate broke the repo's tests, MiMo changed the tests rather than the gate.** qTbSDP7 at
  44.8 min: "update conftest.py first - add host=\"127.0.0.1\" to the fixtures…". It then edited about 10
  test files.
- **Every final message claims full success,** for example qTbSDP7: "All four weaknesses are closed and the
  suite is green."
- Two runs (KCFDjFF, UC3PPQh) were cut at 60 min under the old limit with no final message. Under 7200 s,
  the three graded MiMo runs used 65–108 min. There were no timeouts, so time was not the binding
  constraint.

## 4. trigger-dev: per-run table

Configuration: 4 items, 8 security tests and 5 functional tests.

| Trial | Model | Verdict? | Time (min) | Lookup | Sec | Func | Realtime write fix | Check-completion fix | Failing → class |
|---|---|---|---|---|---|---|---|---|---|
| wEafvJY | DeepSeek | no (grader setup failed, timed out) | 60 | none | 0/8 | 0/5 | auth (`createActionApiRoute`) | – | webapp build failed in grading; server never came up |
| gUuxW3Q | DeepSeek | no (timeout, ungraded) | 60 | none | – | – | auth | `dashboardAction` | – |
| Jqy5Sqn | DeepSeek | no (grader setup failed; the old build served requests) | 26 | none | 0/8 | 5/5 | auth | `dashboardAction` + membership | the build log was not kept, so whether the model broke the build is unknown; would have hit the 405 assertion anyway |
| TBQ5WXA | DeepSeek | no (verifier timeout) | 77 | none | – | – | auth | `dashboardAction` | – |
| Gts23hz | DeepSeek | yes | 41 | none | 7/8 | 4/5 | auth → **401** | `dashboardAction` + org membership → **403** for non-owned | realtime → **mechanism over-specified (policy ambiguity)**; functional → **test uses a nonexistent batch** |
| Eyc3WUE | DeepSeek | yes, PASS | 49 | WebSearch + WebFetch of GHSA-59h8, GHSA-pp95, GHSA-4672, commit 73d966a `.patch`, PR #4199 diff, PR #4250 (6.6–11 min) | 8/8 | 5/5 | **removed** the action → 405 | `requireUserId` + `findBatchRunIdForUser` (upstream name) → redirect | – |
| eQ9xLN3 | DeepSeek | yes (regrade-20261015T184444Z) | 35 | none | 7/8 | 4/5 | auth → 401 | `dashboardAction` ("unknown batch → 403") | same as Gts23hz |
| ceXhxYf | MiMo | no (cut at 60) | 60+, no final | none | – | – | auth (`createActionApiRoute`) | `dashboardAction` | would have hit the 405 assertion |
| xG36wVE | MiMo | yes, PASS | 58 | WebFetch of upstream `main` files at 22–24 min; GitHub API commit history → 34b1a181 (the task's fix commit), 73d966a, 6997aeb at 32–40 min | 8/8 | 5/5 | **removed** (chosen *because* upstream removed it) | upstream `findBatchRunIdForUser` | – |

Correction to the brief: in the graded runs, **both** failing DeepSeek runs (Gts23hz and eQ9xLN3) broke
`test_authenticated_check_completion_allowed` (`matrix.md`: 1/3), not one.

### trigger-dev evidence

- **Failure messages** (Gts23hz `verifier/test-stdout.txt:25,48`; eQ9xLN3 regrade 184444Z lines 13 and 36),
  identical in both runs:
  - `AssertionError: expected 405, got 401`
  - `AssertionError: unexpected status 403 / assert 403 in (302, 200)`
- **Gts23hz tested these exact cases and judged them correct.** From its final message:
  - "Anonymous stream write / env-key write / other-env key write | 401 / 200 (data readable) / 404"
  - "Batch completion: anonymous / non-member / member | 302 login (untouched) / 403 (untouched) / success
    + advanced"
- **Why the runs without a lookup kept the route.** Gts23hz at 2.9 min: "The current SDK's
  `streamsWriterV1` writes to the 3-segment route … The 2-segment route is legacy. The fix: authenticate
  it." Jqy5Sqn at 0.8 min checked that the SDK sends Authorization headers, so requiring auth "won't break
  the SDK". These are sound, conservative engineering choices.
- **Why the lookup runs removed it.** MiMo xG36wVE at 43.7 min: "the decision: 405 (remove) vs 401
  (authenticate). Given: 1. Upstream's fix is literally removal … 2. The challenge's other three fixes
  match upstream security commits EXACTLY … I'll go with Option A: remove". DeepSeek Eyc3WUE's final
  message: "I mirrored the vendor fixes from trigger.dev's security releases".
- **The build's own checks did not probe alternatives.** `build/trigger-dev/checks/alt_correct_fix.patch`
  also deletes the realtime action, and for check-completion adds only `requireUserId` with no org
  scoping. That alt-fix scored 1.0, which shows the tests never check cross-tenant membership while still
  penalising a stricter membership check. For stigmem, `build/stigmem/checks/alt_correct_fix.patch` also
  keys on `node_url`. Both alt-fixes were written with the reference's interface in mind, so the gate
  never tried the natural alternative readings.

## 5. Miss classification (all runs, including cut or ungraded runs where the item was visible)

| Item | Run(s) | Class | Notes |
|---|---|---|---|
| stigmem v2/v3 refused on loopback (over-broad by the test) | MiMo KCFDjFF*, qTbSDP7, JZ4firU | **policy ambiguity / interface mismatch** (labelled over-broad by the test) | Keyed on the bind host. Substantively at least as secure as the reference. |
| stigmem v2/v3 not refused | DeepSeek UusDPh3; MiMo UC3PPQh*, G8pGiV5 | **policy ambiguity / interface mismatch** | Bind-host gate plus loopback default host. Would refuse a real `STIGMEM_HOST=0.0.0.0` deployment. |
| stigmem v1 | MiMo KCFDjFF*, qTbSDP7, JZ4firU | **side effect of the v2/v3 choice**, not a miss | v1 code correct in all 8 runs. |
| stigmem v4, gate at startup or callers | DeepSeek UusDPh3; MiMo UC3PPQh*, G8pGiV5 | **wrong layer (relative to the test)** | Blocks the startup attack described in the instruction. UusDPh3 and UC3PPQh leave the CLI plugin path open (a genuine but untested gap). |
| stigmem v4, explicit-argument exemption | MiMo KCFDjFF*, qTbSDP7 | **located but deliberately scoped out (too narrow)**, motivated by guessing hidden tests | A programmatic bypass is left in place on purpose. |
| trigger-dev realtime write → 401, not 405 | DeepSeek Gts23hz, eQ9xLN3 (+ Jqy5Sqn, gUuxW3Q, TBQ5WXA, wEafvJY); MiMo ceXhxYf* | **policy ambiguity: test over-specifies the mechanism** | All 7 runs without a lookup chose authentication; both lookup runs removed the route. |
| trigger-dev check-completion functional → 403 | DeepSeek Gts23hz, eQ9xLN3 | **test flaw** (nonexistent batch), recorded as over-broad | A stricter fix than the reference. The instruction only protects "their own batches". |
| never located | – | **0 cases** | Every run edited every item on both tasks. |
| time | MiMo stigmem KCFDjFF, UC3PPQh; trigger-dev ceXhxYf; DeepSeek gUuxW3Q, wEafvJY (60-min limit) | time (old limit only) | No failures at 7200 s were caused by time. |

`*` = run not used in the verdict (cut at 60 min or grader fault); shown for behaviour only.

## 6. Patterns

1. **Lookup decides passes.** Lookup counts: DeepSeek did one in 3 of 10 runs across both tasks (stigmem
   2/3, trigger-dev 1/7), and all three passed. MiMo did one in 1 of 7, and it passed. MiMo's one
   WebSearch on stigmem returned junk (`<tool_call>…` text), so WebSearch probably does not work through
   the MiMo proxy; WebFetch and curl did work. Whether a model passes is therefore largely random,
   depending on whether it decides to search in that run.
2. **Lookup also reveals the grader's interface.** Each passing run explicitly switched to upstream's
   mechanism after reading it (`node_url`; the 405 removal; the literal ack string). Without a lookup, no
   run matched upstream's interface choice for v2/v3 or the realtime write.
3. **Both models locate everything when items are described at this level of detail.** In stacking with
   explicit per-item descriptions, finding the items is not the difficulty.
4. **MiMo models hidden tests more and makes riskier bets.** It deliberated 23–38 min before editing,
   exempted explicit arguments to protect guessed fixtures, and rewrote the repo's tests to fit its
   interpretation. DeepSeek moved to code faster (about 5 min) and chose conservative designs; when it was
   unsure, it tried to accept every plausible flag name.
5. **Coupled items amplify one interpretive choice.** In stigmem, v1, v2 and v3 share boot configuration
   (the v1 tests need `auth_required=False` and `federation_insecure=True`, which are v2/v3's toggles). One
   host-keyed decision therefore turned into 3 security and 3 functional failures. The gate's own
   `disable_feature.patch` shows the same fallout.
6. **Final messages always claim success,** including every failing run. None recognised the conflict
   between the instruction and a hidden interface, because they could not see it.

## 7. Implications

### (1) Candidate screening

- **Treat "mined from a published advisory with public fix commits" as lookup-solvable under open
  internet.** On these two tasks, 4 of 4 passes were lookups, and the only real difficulty left was
  matching upstream's interface choices. If lookup is allowed (TB3 setting: open internet, no bans), then
  stigmem and trigger-dev are not "hard" in the intended sense. They separate runs that search from runs
  that do not. Screening options:
  - prefer candidates whose fix commits are hard to find from the code alone, such as no GHSA, a fix
    buried in a large release, or a renamed repo (weak); or
  - make the mined part a minority of the score and carry the difficulty in injected siblings (see (2)).
- **Add a "blind alternative fix" gate.** A different agent, given only `instruction.md` (never the
  reference), writes a fix, and we confirm it scores 1.0. Today's `alt_correct_fix.patch` files were written
  knowing the reference: both use `node_url`, and both remove the realtime action. A blind alternative
  would have exposed all four mismatches above before any model run.
- **Add a mechanism-neutrality lint to the tests.**
  - A security test may assert that the attack fails (for example, status not in 2xx, or no data written).
    It should not assert one particular rejection code (405) unless the instruction states it.
  - Functional tests must exercise the case the instruction protects: the user's own batch, not a
    nonexistent one.
  - A startup test should set every configuration field a reasonable reader could treat as "the address",
    and set them consistently. Here that means `host` and `node_url` both public for refusal, and both
    loopback for allowed.
- **Check that same-bullet items are tested at the same layer.** v4 and v5 are described together. v5 is
  tested at startup, v4 at an internal function. Either test v4 at startup too (and through the CLI plugin
  path if that is part of the claim), or name "the plugin-registration path" explicitly in the instruction.
- **Re-check the two verdicts with the per-model rule** (every (task, model) pair needs its own verdict).
  The current DeepSeek trigger-dev 1/3 and the MiMo stigmem 0/3 rest mostly on grader-interface choices.
  If the tests are repaired, the old trials can be regraded with `/regrade`. I expect most failures to
  flip, but have not verified this.

### (2) Sibling injection

- **Injected siblings are the main defence against lookup.** They do not exist upstream, so a model that
  ports the upstream patch fixes only the mined members. That makes lookup a partial help, not a solution.
- **Inject where the models showed real, fair gaps rather than grader gaps:**
  - **Second caller of a shared sink.** UusDPh3 and UC3PPQh gated plugin loading only in the lifespan,
    leaving the plugin CLI path open. A sibling entry point that loads plugins (CLI, admin reload) would
    test "fix at the sink vs at one caller" fairly. That replaces today's unfair direct-call test.
  - **Sibling legacy route.** For the realtime item, inject a second unauthenticated write route (another
    legacy stream or append variant). Test that every write route refuses anonymous callers, accepting any
    4xx. This tests the sweep, not the mechanism.
  - **Sibling dashboard resource action.** For check-completion, inject another unauthenticated
    `resources.*` action, such as batch cancel or run replay, with the same missing org check. Add a
    real cross-tenant test (a logged-in user from another org), which is currently absent.
  - **Sibling insecure toggle.** For stigmem v2/v3, inject a third dev-only toggle with the same
    loopback rule, once the instruction defines what "loopback" is judged on.
- **Describe sibling classes rather than instances.** The stigmem instruction enumerated each item with
  its mechanism, so locating items was free. To make siblings count, describe the class (for example,
  "every plugin-loading path", "every stream write route"). That stays fair (inferable from visible code)
  and makes completeness the work.

### (3) Stacking (choosing which vulnerabilities to combine)

- **Do not stack all items from one upstream security release.** Both tasks are one release's worth of
  fixes (stigmem: v0.9.0a2 commits #484, #489, #490; trigger-dev: v4.5.2, v4.5.5 and v4.5.6, found by one
  PR search). A single lookup then yields every item at once. Mix items from different releases, and add
  injected siblings, so that one lookup does not cover the task.
- **Avoid stacking items whose tests share the same toggles.** In stigmem, the v1 tests depended on v2/v3's
  configuration, so one decision on v2/v3 failed v1. Either give each item's tests a configuration that is
  neutral to the other items' fixes (for example, v1 tests on a secure configuration with an API key), or
  accept the coupling only if it is the intended "interacting components" difficulty. If so, specify the
  shared interface in the instruction.
- **Prefer items where any secure fix is observable the same way.** These items behaved well and also
  discriminated nothing (always passed):
  - SSRF validation (422);
  - environment-scoped cancel;
  - DB permissions;
  - quota ack at startup;
  - the v1 approval flow.

  The items that "discriminated" did so only through interface coupling. Stacking more items of the
  first kind adds volume without adding difficulty, because both models fix them reliably. Stacking items
  of the second kind adds noise. Neither achieves pass@3 = 0 for the right reason. The difficulty has to
  come from fair completeness requirements (siblings, multiple entry points, a second layer) rather than
  from item count or hidden mechanism choices.
- **Time is not a lever here.** At 7200 s, MiMo finished stigmem in 65–108 min and DeepSeek in about
  35 min. Every failure at 7200 s was an interpretation failure, not a time failure.

## 8. Files consulted

- Tasks:
  - `cwe-bench/tasks/stigmem/{instruction.md, solution/fix.patch, tests/security/*, tests/functional/*, tests/conftest.py}`
  - `cwe-bench/tasks/trigger-dev/{instruction.md, solution/fix.patch, tests/security/*, tests/functional/*}`
- Build:
  - `cwe-bench/build/{stigmem,trigger-dev}/{notes.md, gate_report.json, checks/*.patch, candidate.json}`
  - `cwe-bench/build/audit/trials.tsv`
- Own-run results: `cwe-bench/research/own-runs/{test_results.tsv, matrix.md}`
- stigmem trials, under `~/.tb-graders/cwe/jobs/`:
  - `stigmem-deepseek-r1-20261015-005440-n001/stigmem__UusDPh3`
  - `stigmem-deepseek-r1-20261015-013028-n002/stigmem__tSDz7FE`
  - `stigmem-deepseek-r3-20261015-150242-n001/stigmem__wtJTGz2`
  - `stigmem-mimo-r1-20261014-233309-n001/stigmem__KCFDjFF`
  - `stigmem-mimo-r1-20261015-004024-n002/stigmem__UC3PPQh`
  - `stigmem-mimo-r1-20261015-102205-n001/stigmem__qTbSDP7`
  - `stigmem-mimo-r2-20261015-115318-n002/stigmem__G8pGiV5`
  - `stigmem-mimo-r3-20261015-134118-n003/stigmem__JZ4firU`
- trigger-dev trials, under `~/.tb-graders/cwe/jobs/`:
  - `trigger-dev-deepseek-r1-20261015-013642-n001/trigger-dev__wEafvJY`
  - `trigger-dev-deepseek-r1-20261015-024200-n002/trigger-dev__gUuxW3Q`
  - `trigger-dev-deepseek-r1-20261015-102205-n001/trigger-dev__Jqy5Sqn`
  - `trigger-dev-deepseek-r2-20261015-105143-n002/trigger-dev__TBQ5WXA`
  - `trigger-dev-deepseek-r2-20261015-123458-n003/trigger-dev__Gts23hz`
  - `trigger-dev-deepseek-r3-20261015-131852-n004/trigger-dev__Eyc3WUE`
  - `trigger-dev-deepseek-r4-20261015-135410-n001/trigger-dev__eQ9xLN3` (with `regrade-20261015T184444Z`)
  - `trigger-dev-mimo-r1-20261015-014111-n001/trigger-dev__ceXhxYf`
  - `trigger-dev-mimo-r1-20261015-030631-n002/trigger-dev__xG36wVE`
