# Builder brief: stack MiMo-targeted traps onto a base that already beats DeepSeek (round 2)

You build ONE Harbor security-fix task. Read and follow `builder/BUILDER.md` in full, especially
3a–3j. This brief adds the round-2 goal and limits.

## Why this task exists
Goal: tasks where BOTH DeepSeek V4.1 Flash and MiMo-V2.6-Pro fail all 3 attempts with FINISHED runs
(timeouts never count), and every failure comes from the model, not from a task defect.
Your base already has a shape that DeepSeek fails consistently. MiMo solved it, because MiMo
probes: it runs the attack on each candidate path before deciding. Your job is to add 2–3 realistic
traps of DIFFERENT kinds that MiMo missed in about half of its round-1 runs. Then a correct fix
needs several independent judgements that a probe of the obvious path does not reveal.

Read first:
- `research/round1-analysis/B-failure-modes.md`: §2.2 (judgement, not search), §3a (ranked recipes),
  §3b (test shapes that caught each defect), §4 (wording rules).
- `ALGORITHM.md`: the "data producer off the check's path" paragraph.

MiMo-relevant shapes (round 1, n small): coupled visible binding next to the hidden one (both models
missed it ~30% of runs); a merged/defaults/inheritance route to the same sink (MiMo 1/2); a
neighbour-precedent authorisation on a proxy resource (MiMo 1/2); a parser differential on the
protected item's identity with a privileged fallback (MiMo 1/4); a shared helper whose sibling API
must keep its stated behaviour (MiMo 1/2). Caught by both, every time: encoding variants, extra
verbs, other protocols, other role/direction, anything the instruction names. Do not add those.

## Hard rules (the client audits fairness; any cheating gets the task rejected)
1. Every trap is code a real maintainer could plausibly have written, or a real pre-existing gap,
   in the real codebase, reachable through the real entry point, and visible to someone who reads
   the code near the relevant mechanism. No dead code, no obfuscation, no misleading comments, no
   names chosen to deceive.
2. Every trap is covered by an invariant stated in `instruction.md` (3i), or by standard expert
   security knowledge. Never name or paraphrase a trap's mechanism, file or route.
3. Tests are behavioural, accept ANY correct fix, and are written before any trial; never tune them
   to a model's patch. Each trap gets its own security test(s) (one per form), plus a functional
   test on the thing most tightly coupled to it (BUILDER 3g, B-failure-modes §3b).
4. A correct fix must stay reasonably small: one engineer, about an hour, no rewrite. MiMo is slow
   (median solve 60 min of a 2 h limit) and a timeout is not a result, so keep the total work under
   about 45 minutes for a careful engineer who knows where to look.
5. The reference fix (`solution/fix.patch`) closes the base flaw and every trap. Wrong-fix patches
   go in `checks/`: one `security_fail` per trap (the fix that misses only that trap), the
   catalogue classes (3h), and `functional_fail` for over-broad fixes.
6. Do NOT run DeepSeek or MiMo, do NOT run `build/trial.py` or `harness/run_trial.sh`, and do NOT
   write the `blind` patch or `FAIRNESS.md`: independent agents do those after you. Run the gate
   stages yourself: `python3 -I builder/gate.py SLUG --only static`, then `--only nop`,
   `--only oracle`, `--only patches`. Static will report the missing blind patch and FAIRNESS.md as
   problems; that is expected. All other static problems must be fixed.
7. Machine limits: one shared 8-CPU / 12 GB Docker VM, already running trials. Never prune Docker
   images or the build cache, never stop containers you did not start, and keep at most one Docker
   build or gate stage of your own running at a time.
8. Scratch work goes in `~/.tb-graders/cwe/work/SLUG/`. Edit only `tasks/SLUG/` and `build/SLUG/`.
9. Record in `build/SLUG/notes.md`: start/end UTC, each trap (`manifest.traps`: shape, file:line,
   covering tests, why it is realistic), what you verified, and what you could not.

## Lesson from marshmallow-readonly-sib (2026-10-16)
DeepSeek solved it in 10 minutes and found every trap within 2 minutes of starting: the whole
nesting logic is a few hundred lines in two files, so the ignored route sat right next to the code
the report leads to. The same class-A shape beat DeepSeek 6/6 on jackson-databind, where the ignored
route (`SettableAnyProperty`) is far from the view-handling code in a very large codebase, and its
absence reads as design. Require **distance**: the ignored route must live in a different file or
package from where the report's example lands, in a codebase large enough that reading everything
is not the natural first move. Small libraries are poor hosts for class A.

## Lesson from jackson-databind-readonly (2026-10-16)
Same codebase as sib2, same "protection ignored on one route" shape, yet DeepSeek solved it in
22 minutes: its very first repro already covered the catch-all route. The difference: READ_ONLY is
documented with no exceptions, so nothing invited a "this route is out of scope" reading. In sib2
upstream never supported views on any-setters, and DeepSeek said so ("upstream doesn't support it")
and left it open in every run. The ingredient that beats DeepSeek is a **reason to dismiss**: the
ignored route must be one a reasonable engineer could argue the protection never covered (an
unsupported combination, a neighbouring feature, a legacy path), while the stated invariant still
covers it unambiguously. Distance helps; the reason to dismiss is the main lever.

## DeepSeek shape 2: data producer off the check's path (Hadi, 2026-10-15)
Source: Hadi's DEEPSEEK_WEAKNESS_2026-10-15.md (in Hadi/mcp-ts-sdk-oauth-issuer-confusion_deepseek.zip;
credit him in notes). DeepSeek failed this 8/8 (3/3 on the real MCP TypeScript SDK, GHSA-6qxp-vccf-f47h),
always missing the same tests and never breaking functionality.
- **Shape:** the fix needs (1) the CHECK the report points at and (2) the DATA PRODUCER the check
  depends on (schema, serializer, parser, loader, constructor), in another file or package. The
  check does **not** call the producer: the data reaches the check on a separate path (saved and
  reloaded, deserialized from storage, rebuilt from config). If the check calls the producer
  directly, DeepSeek follows the call and fixes it (Hadi's Semaphore control), so verify this.
- **Why it works:** DeepSeek follows calls INTO the check and never asks where the check's data
  comes from. It keeps a fail-open branch ("field missing, allow") for compatibility, and it stops
  when the repo's own tests pass (none of them exercise save and reload).
- **Controls:** check-only broken → solved. One report sentence naming the second path → solved
  3/3. Removing misleading comments → still failed. So the report must describe impact through
  the check's path only and state the property abstractly ("including credentials saved
  earlier"), never name the producer or the reload path.
- **Avoid:** fixes where the check cannot compile without the producer change (that forces the
  find), and hidden tests that need a field or function name the model would have to guess.
- **MiMo solved Hadi's task** (it probes), so this shape alone is DeepSeek-only. Pair it with at
  least two MiMo traps of different kinds (coupled visible value; unsupported-combination route;
  merged/defaults route) as in jackson-databind-sib2.

## Lesson from better-auth-sso-endpoints (2026-10-16)
Hadi's shape on a real, published SSRF (GHSA-5rr4-8452-hf4v): DeepSeek solved it in 20 minutes,
finding all three traps. It did not trace save -> reload; it read the SSO route files whole, and a
grep landed on the registration branch. The "producer" here was the registration handler, which
is the attacker's own entry point, and the report must mention registering a provider to describe
the attack. Hadi's producer was hidden machinery (a zod schema stripping a field on reload) that
no report sentence needs to touch. Require that the producer is **infrastructure the attacker never
calls directly** (schema, serializer, cache, persistence mapper, config loader), not a request
handler. Request handlers get read wholesale.

## Report back (under 400 words)
Gate stage results; the traps with one line each; the new instruction's word count; every
unverified guess; any fairness concern you see yourself.
