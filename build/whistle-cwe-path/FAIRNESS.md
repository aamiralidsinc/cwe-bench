# FAIRNESS review — whistle-cwe-path

Reviewer did not write the tests. Inputs read: instruction.md, tests/{security,functional}/run.js,
tests/support/{harness,junit}.js, tests/test.sh, tests/score.py, solution/fix.patch, manifest.json,
notes.md, checks/*.patch. Nothing was run. The upstream source tree is not checked out locally, so
claims about `biz/webui/lib/index.js` (that it already references `common.WHISTLE_UID_HEADER` /
`common.getTempFile` and sends `config.uid`) come from notes.md and could not be checked here.

## 1. Per-test table

Shared dependency: every functional test sends the credential through `H.authHeaders`, which reads
the header name from `require('lib/util/common.js').WHISTLE_UID_HEADER`. If that export is missing
(as it is at the pinned commit), **no header is sent**, so every authorized request goes out
anonymous.

| Test | Asserts | Fairness basis | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security::unauthenticated read of a file outside the working area is refused | GET temp/get?filename=<abs> with no header: marker not in body, status 4xx | Req. prop. 1 ("must be refused … client error … no data"); Observed problem example | no | low |
| security::unauthenticated read of a stored item is refused | Same for a 64-hex stored handle | Prop. 1 "regardless of … whether the target is an ordinary stored item" | no | low |
| security::unauthenticated read via the list form is refused | ?files=<hex>: no raw/base64 marker, 4xx | Prop. 1 "regardless of which … operation"; "every operation the component exposes" | no | low |
| security::unauthenticated access to the stored-session index is refused | GET saved/list no header → 4xx | Observed problem ("saved-capture listing"); prop. 1 | no | low |
| security::unauthenticated access to request history is refused | GET /cgi-bin/history no header → 4xx | "every operation the component exposes"; "serves captured traffic" | no (a per-route fix that misses it is a wrong fix by the instruction) | low |
| functional::authorized load of a file by full path works | Authorized GET filename=<abs outside> returns content | Prop. 2 "loading a file by its full path … may not be … made to depend on where the file sits" | **maybe**: a correct gate that keeps the header name in service.js (or hard-codes a string) and doesn't export `WHISTLE_UID_HEADER` from lib/util/common.js fails this, since the harness sends no header | **medium** |
| functional::authorized read of a stored item works | Authorized GET filename=<hex> returns content | Prop. 2 | maybe (same header-export coupling) | medium |
| functional::authorized read via the list form works | Authorized ?files=<hex> → JSON `list` of base64 containing content | Prop. 2 "batch form" (existing response shape) | maybe (same coupling) | medium |
| functional::authorized creation of a stored item works | Authorized POST temp/create → `ec:0`, `filepath` | Prop. 2 "creating a new stored item" | maybe (same coupling) | medium |
| functional::authorized create then read round-trips the content | create → strip `temp/` → GET returns content | Prop. 2 | maybe (same coupling) | medium |
| functional::authorized access to the stored-session index works | Authorized saved/list → `ec:0` | Prop. 2 "listing saved captures" | maybe (same coupling) | medium |

Why only medium and not high: the UI code is said to already call `common.WHISTLE_UID_HEADER`. A
careful engineer who honours the token "every call the panel makes … already carries" has to define
that export, or the real panel stops working. Because the harness reads the name from the product,
the header's value/spelling is not hard-coded. Still, nothing in the instruction tells the solver that
an existing panel-side contract fixes where the name must live. A solver can write a sound gate (for
example a local constant in service.js) that passes 5/5 security and gets reward 0. The six
functional tests all fail together on this one point, so the shared root cause is effectively
**high** impact.

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| T1 server-wide gate | Gate only `/cgi-bin/temp` (fix at the reported endpoint) | Yes: security saved/list + history (`checks/gate_temp_get_only.patch`) |
| T1 (variant) | Gate only the 3 tested route prefixes (temp, saved, history) | **No.** Other routes (`/service/*` forward, `service/save`, anything else) stay open |
| T1 (variant) | Method-scoped gate (`app.get('*', gate)`) / reads-only gate | **No.** All security tests are GET. Unauthenticated `POST /cgi-bin/temp/create` (a disk write, which the instruction forbids: "no change on disk") is never tested. Manifest marks `reads_only` "n/a", but a solver can write a GET-only gate |
| Credential check | Presence-only check (`if (!req.headers[H])`) or truthiness | **No.** No test sends a wrong-valued token. A gate that accepts any non-empty header passes everything |
| Credential check | Wrong comparison source (e.g. compare to `clientId`) | Caught by the functional tests (authorized calls refused) |
| Refusal shape | Throw in middleware → 500 | Yes: 4xx check (`checks/crash_refusal.patch`) |
| Refuse-all | 403 everything | Yes: functional (`checks/refuse_all.patch`) |
| T2 full-path feature | Confine filename to temp dir / basename | Yes: functional full-path (`checks/confine_to_tempdir.patch`) |
| Header hygiene | Don't strip the uid header before `/service/*` forwarding (token leaks to forwarded target) | No (hardening-level; low) |

Wrong fixes no test catches: presence-only token check; GET-only / reads-only gate; route-allow-list
gate covering just the tested routes; not stripping the credential header.

Also: manifest `patch_checks` lists `blind.patch`, but `checks/blind.patch` does not exist. The gate
already reports this.

## 3. Hints in instruction.md

- "every call the panel makes to it already carries a token that identifies the call as coming from the tool itself": names the mechanism and the fix (gate on the existing token). Fairness may need it, but it largely defuses T1. Neutral: "The panel is the only intended client of this interface."
- "The background component must act only on requests that prove they come from the tool itself … present the tool's own identifying token": states the fix approach. Acceptable as a property, but together with the above it gives T1 away.
- "regardless of which item, path, or operation … ordinary stored item or something far outside the storage area": paraphrases the variant list (abs path, stored item). Neutral: "regardless of what the request asks for."
- "Stored items and the saved-capture listing come back the same way": names variants 2 and 4. Neutral: "Other data the component holds is exposed the same way."
- "reading a stored item by its handle and through the batch form that fetches several at once … loading a file by its full path … None of these may be narrowed … or made to depend on where the file sits": spells out T2 and the list-form variant. Fairness needs T2 stated, but "made to depend on where the file sits" names the trap's wrong fix. Neutral: "All existing panel functionality, including loading arbitrary files the operator selects, must keep working unchanged."

## 4. Realism

- T1: real upstream fix (server-wide uid gate), reachable through the real entry point (module export → hagent server → loopback HTTP). Not planted.
- T2: real feature at the real sink. Not planted.
- The pinned tree's UI referencing undefined `common.WHISTLE_UID_HEADER` / `common.getTempFile` is real upstream state (a half-landed fix), not contrived. But it is a strong in-repo pointer to the fix, and the UI's own no-login temp/get path throws at this commit. Acceptable; noted.
- `getTempFile` / regex widening in the reference fix is untested (correctly so; see notes).

## 5. Verdict: NOT READY

Required changes:
1. **Add a security test with a wrong-valued credential** (header present, value ≠ uid → 4xx, no data). Add `checks/presence_only.patch` (gate on header presence) with expect `security_fail`.
2. **Add a security test for a non-GET operation**: unauthenticated `POST /cgi-bin/temp/create` → 4xx and no new file in `tempDir`. Add `checks/gate_get_only.patch` (`app.get('*', gate)`) with expect `security_fail`. Fix the manifest's `reads_only: n/a`.
3. **Header-name coupling**: either add an instruction sentence such as "The panel already relies on a specific, existing contract for how it identifies itself to this component; honour that contract rather than inventing a new one," or make the harness fall back so a correct gate with a different constant location doesn't zero the reward. Also confirm in Docker that `biz/webui` really references `common.WHISTLE_UID_HEADER` and sends `config.uid` (could not be verified here).
4. Create the missing `checks/blind.patch`.
5. Recommended: soften the hint sentences in §3, keeping an explicit but neutral T2 must-keep-working sentence.
