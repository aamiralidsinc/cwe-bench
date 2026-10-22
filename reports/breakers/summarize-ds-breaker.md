# summarize-ds — a task the pipeline recorded as a both-model (DeepSeek V4.1 Flash + MiMo-V2.6-Pro) breaker

**Status of 2026-10-20.** This task is classified by the trial pipeline as a **both-model breaker**: both DeepSeek V4.1 Flash and MiMo-V2.6-Pro failed all 3 counted attempts and neither reached reward 1.0 (AUTO-STATE tick16/17, "sound both-fail"). Its DeepSeek pre-trial fairness review returned **GATE_A: READY** with **NEEDS_HUMAN_REVIEW: YES**.

Three caveats apply up front and are not yet closed:

1. **GATE_A: READY, NEEDS_HUMAN_REVIEW: YES.** Two doubtful "correct-fix" shapes were recorded for human confirmation (see §2). They were judged *not* natural correct fixes, so they did not set NOT_READY — but the human confirmation has not been made.
2. **No per-attempt transcript audit has been produced.** `build/audit_results.py` (the authoritative raw-trial reader) shows **no graded run** for this task, so the audit dimension is **not run** (not merely prepared-not-recorded). Everything in §3 and §4 is therefore provisional.
3. **The counted per-attempt scores are not recoverable from the VM's authoritative sources** (see §3 for exactly what is and is not present). The "both-fail" classification is carried from the pipeline's own tick notes; the raw trial folders, `auto_trial.out`, run logs, and `audit_results.py` row that the jackson report relies on are **all absent for this task**.

Sources read: `build/summarize-ds/manifest.json`, `tasks/summarize-ds/instruction.md`, `build/summarize-ds/FAIRNESS.md`, `build/summarize-ds/notes.md`, `build/summarize-ds/gate_report.partial.json`, `build/summarize-ds/checks/*.patch`, `build/pipeline/AUTO-STATE.md`, `build/pipeline/ledger_deepseek.tsv`, and a full scan of `~/.tb-graders/cwe/jobs` and `build/audit_results.py`.

## Summary

- **Result (as recorded by the pipeline, NOT independently re-derived here):** both target models failed all 3 counted attempts; neither reached reward 1.0.
  - **Per-attempt reward sequences: not available on the VM.** See §3 — no raw trial artifacts survive for this slug.
- The task is a real library with real gaps. It is `steipete/summarize` (a link-to-text/summary tool with a CLI/library API and a background daemon) at the commit before a published SSRF fix. The advisory's own flaw is combined with six further routes to the same rule. Pattern **A+B**, track **injected** (two of the seven routes are injected siblings; the rest are real unmodified upstream code or routes the published fix left open).
- **Vulnerability (CWE-918, server-side request forgery).** When the product summarizes a link, material it retrieves (a podcast feed, an HTML page) names further addresses, and the product opens connections to them with no check that the destination is a public internet address. An attacker-authored feed or page can therefore steer the product at loopback, private, link-local or metadata endpoints and have the non-public response returned in the result.
- Why both models are expected to fail (designed levers, §4): each route has a different plausible reason a solver dismisses or never reaches it ("the daemon already has an SSRF guard", "that's the generic HTML provider, not the podcast feature", "the enclosure is the audio the user asked to transcribe", "chapter titles are optional enrichment"), and several routes share one media helper so a per-call-site guard leaves a sibling caller open.

## 1. The task

**Vulnerability (CWE-918, SSRF).** `createLinkPreviewClient({ fetch }).fetchLinkContent(url)` (the public library API) and `POST /v1/summarize` (`mode=url`, `extractOnly`, served by `runDaemonServer` with an injected transport, the daemon API) both fetch attacker-influenced sub-URLs derived from the retrieved material, with no address check, no post-resolution / post-redirect re-check, and redirect-following left on.

**Base advisory:** GHSA-3VX2-VQX8-JXFG / CVE-2026-53782. Vulnerable (pinned) commit `cd3ee48fb24a54aa3a7653ffd84ae38616227377`, upstream fix `3c5522440c4833dde033e226baa39e6dda1dfc75`. The upstream fix closes only part of the surface; four of the seven routes below are routes it never touches, and two are injected siblings.

**What the task contains.** Seven real routes to one rule (the manifest's `traps`), all reachable through the two real entry points:

| Route | Pattern | Site | What leaks | Why a solver skips it |
|---|---|---|---|---|
| T1 base transcript (reported) | A | `podcast/rss-transcript.ts:53` | feed-declared transcript URL fetched (redirect follow, no address/DNS check) | none; it is the reported site. Lever: a one-shape fix misses the IPv6-literal, name-resolves-private and redirect-to-private shapes |
| T2 daemon blocklist | A (far) | `src/daemon/url-fetch-guard.ts:79-98` | a *second* copy of the blocklist misses IPv6 forms embedding an IPv4 address (NAT64, 6to4) and reserved ranges | "the daemon already has an SSRF guard"; it lives in `src/daemon`, not `packages/core` |
| T3 caption route | B | `generic-embedded.ts:64` | page `<track>` caption URL fetched and returned as transcript text | "that's the generic HTML provider, not the podcast feature the report names" |
| T4 enclosure media | B | `podcast/provider-flow.ts:41-84`, `podcast/media.ts:285-362` | feed enclosure media probe (HEAD) and download (GET) on a private address | "the enclosure is the episode audio the user asked to transcribe, not reflected text" |
| T5 injected chapters | B (injected) | `podcast/chapters.ts`, called from `provider-flow.ts:18` | feed-declared chapter-title JSON fetched (redirect follow, no check) | "chapter titles are optional enrichment, not transcript content" |
| T6 injected Spotify | B (injected) | `podcast/spotify.ts`, `spotify-flow.ts` | Spotify embed page's declared transcript URL fetched by the Spotify→iTunes flow | "the Spotify flow already fetches third-party feed data, so this looks like normal flow data" |
| T7 og:audio metadata | B (upstream-uncovered) | `provider-flow.ts:95-125` (`tryOgAudioTranscript`) → `media.ts:280-380` | feed-declared audio-metadata URL transcribed through the **shared** media helper | "declared audio is the episode audio the user asked to transcribe" — and a fix that guards the reported media call site leaves this reachable from a different caller through the same helper |

**Report given to the agent** (`instruction.md`, rewritten 2026-10-20 to state the rule once with no route, file, function, or count named). Shorthand used in the fairness file:
- **P** — no connection opened in the course of summarizing may target anything other than a public internet destination, both the asked-for address and every address named by retrieved material;
- **D** — the decision is made on the destination the connection would actually use, after name resolution and after any redirect, not on the supplied text;
- **F** — a refusal happens before the connection is opened and is visible (an error / absent optional result when used directly, a 4xx when run as a service), never reported as success;
- **L** — legitimate use keeps working exactly as today (public names, public IP literals including IPv6 forms whose embedded address is public, and public→public redirect chains);
- **N** — loopback, private, link-local, CGNAT, multicast, documentation and other non-public ranges are not public destinations.

**Hidden tests.** 11 security tests, mapped one group per route (T1: loopback, ULA IPv6, name→private, public→private redirect = 4; T2: NAT64, 6to4 = 2; T3/T4/T5/T6/T7: 1 each), plus 9 hidden functional tests (public name, public literal, public redirect, public caption, public enclosure, public chapters, public Spotify, daemon public page, daemon public-NAT64), plus **25 pristine project tests** across four upstream test files. Every security assertion is "no transport call to a non-public destination and no result derived from one"; daemon refusals accept **any** 4xx (never one exact status). Reward = the security pass fraction (out of 11), or **0 if any functional or project test fails**. (The 11th security test, `og_audio_private`, was added in the 2026-10-20 "v2" upgrade; the pre-upgrade gate log reads 10.)

## 2. How we know the task is fair

**Build gate (before any model ran), from `notes.md` / `gate_report.partial.json`:**

| Check | Result |
|---|---|
| Vulnerable (pinned+injected) tree | security 0/10, all functional + 25 project tests pass |
| Reference fix (`solution/fix.patch`) | reward 1.0, three times, identical |
| `pass_alt_fix.patch` (a single central guarded transport, a different shape from the reference) | 1.0 |
| `pass_hardening.patch` (transcript-entry guard plus per-sink guards, a different layer) | 1.0 |
| 10 `security_fail` wrong-fix patches (`sf_miss_base/caption/enclosure/chapters/spotify/daemon/og_audio`, `sf_media_head`, `sf_malformed_ipv6`, `sf_crash_as_refusal`) | each fails exactly its declared security test(s), all functional pass |
| 2 `functional_fail` wrong-fix patches (`ff_refuse_all`, `ff_overbroad_nat64`) | fail the functional tests as declared |

That the reference, a central-transport alt fix, and a different-layer hardening fix all score 1.0 is the fairness evidence that the grader is not tied to one guard layer. **Note (unlike the jackson report): there is no blind-fix patch here** — a from-the-report-only blind fix was *not* produced (it was an allowed-missing static-gate item), so the "a fresh model found every route" evidence that jackson has is **absent** for this task.

**DeepSeek pre-trial fairness review (`FAIRNESS.md`), verbatim verdict:**

> READY. Every hidden and project test is passable by a correct fix following the primary mechanism (destination check after resolution and after redirects, refusal visible): the reference, `pass_alt_fix` (central guarded transport) and `pass_hardening` (transcript-entry guard plus sinks) all pass, so the tests are not tied to one layer and no test demands one error class or bypasses a valid layer. The only doubtful "correct-fix" shapes are (i) a per-sink guard resolving with `dns.resolve*`, which ignores `/etc/hosts` and therefore fails the 25 project tests even though the hidden setup serves c-ares, and (ii) a dispatcher-only guard below the injectable transport. Neither is a natural correct fix under D ("the destination the connection would actually use") and the product's injectable-`fetch` boundary, so they do not set NOT READY; they are recorded for human confirmation.
>
> GATE_A: READY
> NEEDS_HUMAN_REVIEW: YES

Every hidden and project test was rated **low** (or low/medium for the one project-pinning test) risk against the instruction. The review also lists leniency gaps no test catches (fail-open on DNS error, non-http(s) schemes, IPv4-mapped IPv6 at a library sink, library refusals never asserted as success/failure, multi-hop redirects) and hint/wording items with generalized rewordings — all "quality to tighten", none a GATE_A reason.

**The two doubtful shapes for human confirmation** (recorded, not resolved):
- (i) a **per-sink guard that resolves with `dns.resolve*`** — the hidden setup serves c-ares, but the 25 project tests resolve only through `/etc/hosts`, so such a fix would fail them; judged not a natural correct fix under D and the injectable-`fetch` boundary.
- (ii) a **dispatcher-only guard below the injectable transport** — guards a layer beneath the intended `fetch` boundary.

The reviewer asks a human to confirm that neither is intended as a correct fix, and that the injectable `fetch` boundary is the intended guard layer.

## 3. Results — PROVISIONAL (per-attempt scores not recoverable on the VM)

**What the pipeline recorded.** AUTO-STATE marks summarize-ds a "sound both-fail" (tick16) and then a "both-model BREAKER (flag review), terminal" with "GATE_A READY, NEEDS_HUMAN_REVIEW:YES" (tick17), and lists it under "CONFIRMED/READY … summarize-ds(READY,rev)". The classification handed to this report — **both models failed all 3 counted attempts, neither reached 1.0** — is that recorded verdict.

**What is actually present on the VM for verification — nothing at the trial level:**

| Authoritative source (per our reading discipline) | summarize-ds |
|---|---|
| `build/summarize-ds/auto_trial.out` (the `ACCEPTED:` line) | **file does not exist** |
| `[trial-done summarize-ds …]` line in `build/pipeline/auto_trial.log` | **absent** (no match) |
| `build/summarize-ds/runs_deepseek.log` / `runs_mimo.log` | **do not exist** |
| per-run `results.json` under `build/summarize-ds/` | **none** |
| row in `build/audit_results.py` (rebuilt from 285 raw trials) | **no row at all** → "no graded run" |
| raw trial folders in `~/.tb-graders/cwe/jobs` | **none** (287 job dirs scanned; none for this slug, and none found by advisory/CVE/`steipete`/`ssrf`; its sibling `trivy-ds` deploys as `trivy-path-traversal-inj`, so renamed slugs were checked too) |
| `build/pipeline/ledger_deepseek.tsv` | only `summarize-ds  gate  sound` — **no trial line** |

So **no per-attempt reward sequence, per-test count, or route breakdown can be reported** for this task, and the `audit_results.py` reader — the one the memory discipline says verdicts must come from — currently shows this task as having no graded run. The reward values ("ds best … / mm best …") that AUTO-STATE prints for the *other* tick17 breakers (e.g. protobuf.js-ds) are **not** printed for summarize-ds; its line is only the words "sound both-fail". This should be resolved before the task is reported externally (see §6).

## 4. Why both models are expected to fail — PROVISIONAL (no transcript audit)

No per-attempt transcript audit exists, so this section is the task's **designed** failure mechanism (from `manifest.json` `traps` and `notes.md`), not observed model behaviour. Each route carries a distinct dismissal reason — the lever the designer expects to hold:

- **T2 daemon blocklist:** a correct-looking SSRF guard already exists in `src/daemon`, so a solver trusts it and never notices it misses NAT64 / 6to4 IPv6 forms that embed an IPv4 address. Distance (`src/daemon` vs `packages/core`) reinforces the dismissal.
- **T3 caption route:** lives in the generic HTML provider, not the podcast feature the report's example uses, so a solver who guards "the podcast sinks" leaves it open.
- **T4 enclosure / T7 og:audio:** both reach the **shared** media probe/download helper. T4 is dismissed as "the audio the user asked to transcribe"; T7 is reached from a *different caller* into the same helper, so a fix that guards T4's call site still leaves T7 open. This shared-helper coupling is the strongest single lever.
- **T5 chapters / T6 Spotify (injected siblings):** read as ordinary copied code ("optional enrichment", "normal Spotify flow data"); the upstream fix never touches these files, so there is nothing to copy from.
- **T1 (reported):** even the named route needs all four shapes (IPv6 literal, name→private, redirect→private, not just the loopback literal); a denylist on the supplied text misses them.

A correct fix makes the decision on the destination the connection would actually use (after resolution and redirect) at the injectable transport boundary, so one central guard covers every route (proved by `pass_alt_fix`). The expectation is that both models guard the obvious sinks and leave at least one route — most plausibly a shared-helper caller (T7) or the far daemon IPv6 forms (T2) — open, or over-block (`ff_overbroad_nat64`: rejecting the whole NAT64 prefix breaks the public-NAT64 functional test). **None of this is confirmed against transcripts; it is the design intent.**

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro; up to 3 counted attempts each, early-exit on a solve.
- Offline: the agent could reach only the model APIs; web tools disabled; the repository has no git history; hidden tests are copied in only after the agent stops.
- Reward = security pass fraction, 0 if any functional test fails, 1.0 = solve. Name resolution is deterministic (an `/etc/hosts` table plus a local DNS server); the real library API and the real daemon HTTP server are driven with an injected transport, `--network none`.
- What counts: a 3-hour timeout counts as a FAIL; an attempt cut off by a provider or network outage is not counted.

## 6. What is needed before this can be trusted or reported externally

1. **Recover or re-run the counted trial.** The both-fail classification currently has no surviving raw artifacts on the VM. Either locate the trial folders / `auto_trial.out` the tick notes were written from, or re-trial both models (3 counted runs each, early-exit on solve) so `build/audit_results.py` produces a real row.
2. **Run the per-attempt audit** (per-test results + transcript, via `postmortem.py prepare/record`) on each counted attempt, as every graded run requires, and confirm *which* route each model left open.
3. **Resolve NEEDS_HUMAN_REVIEW: YES** — a human confirms the two doubtful "correct-fix" shapes (the `dns.resolve*` per-sink guard, the dispatcher-only guard) are not intended correct fixes and that the injectable `fetch` boundary is the intended guard layer. Optionally apply the fairness "quality to tighten" items (close the five uncaught leniency gaps; rebuild the synthetic-looking `og_audio_private` fixture; serve the same DNS table to c-ares in the project-test run).
4. **Consider adding a blind fix** (regenerated on the built v2 image) and re-gating, to match the evidence bar the confirmed jackson-databind-sib2 breaker meets.
5. Only then classify as a confirmed both-model breaker. On the VM evidence available now it is a **pipeline-recorded, fairness-READY candidate whose counted trial cannot be independently verified**.

## Appendix: what is in the task package

| What | Contents | Present? |
|---|---|---|
| Task | report (`instruction.md`), environment (v2 image), reference fix (`solution/fix.patch`), hidden tests | yes |
| Validation | gate report (`gate_report.partial.json`), 12 wrong-fix patches + 2 pass patches (`checks/*.patch`), fairness review (`FAIRNESS.md`), build notes (`notes.md`) | yes |
| Blind fix | from-the-report-only fix proving the routes are findable blind | **no** (not produced) |
| Trials | per-attempt score, per-test results, final code, transcript audit | **no** (not recoverable on the VM) |
