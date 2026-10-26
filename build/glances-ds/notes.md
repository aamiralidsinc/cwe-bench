# glances-ds — build notes

- start UTC: 2026-10-24T03:34:45Z
- end UTC: 2026-10-24T04:27:51Z
- advisory: GHSA-4H34-V6R8-MMJC / CVE-2026-68520 / PYSEC-2026-3664 (nicolargo/glances)
- pinned: 3392c538adf3f41ec04045fd68ba86f6d7276cf6
- fix: 8d0f8276c2abd2e9d400bd6c84bdfba0dfcab065
- pattern: A+B, track: injected

## Security property (one statement, used by every route)

No configured credential (a password, a login name, an access token, or credentials
embedded inside a configured address) may appear in any response the service sends
without authentication, in whatever response it appears, and however the value is stored
or represented (a single value, one element of a list, or nested inside another value).

## Levers (each with a different reason to skip it)

1. **limits producer off the check's path — main, how-type.** `load_limits()`
   (glances/plugins/plugin/model.py:723) copies *every* key of the plugin's config
   section into `_limits`; `/api/4/all/limits` (glances/stats.py:420) and
   `/api/4/{plugin}/limits` (glances/outputs/glances_restful_api.py:1064) serve that
   copy raw. Real unmodified upstream. Reason to dismiss: they read as alert
   thresholds / monitoring statistics, not "the configuration endpoint" the report
   names. Shape: limit values are *lists* of strings (`ip_public_password` ->
   `["..."]`, `ports_web_1_url` -> `["https://user:pass@host"]`), so the published
   `secure_option()` scalar helper returns them unchanged even when it is applied.
2. **URL userinfo in a configured value — published fix, shape trap.** The project's
   existing protection filters key names only; a configured endpoint that carries
   `scheme://user:pass@host` is an ordinary setting to that filter.
3. **Ports plugin statistics — real Pattern B route, protection never existed.**
   `GlancesWebList.load()` (glances/web_list.py:51, 89-96) copies `web_N_url` and the
   `proxies` dict into the ports stats, served by `/api/4/ports`. Reason to dismiss:
   monitoring output the plugin is meant to show. Shape: the proxy is a *nested*
   `proxies` dict, so a shallow field-level redaction misses it.
4. **Coupled must-keep-working (not a trap on its own).** CPU/load `user_careful`,
   `user_warning`, `user_critical`, `user_log`, numeric limits, plain URLs, and
   argparse ints/floats/bools must keep their values and JSON types. A naive `user`
   substring regex or a blanket stringify breaks them (web UI thresholds,
   `/api/4/args` types).

## Injected siblings (2, placed where the published fix never touches)

- **I1 partial limits sanitizer (all/limits).** A maintainer added
  `_sanitize_limits()`: masks a limit *key* containing password/token/secret/api_key
  and leaves everything else alone. It sits only on the bulk route; the per-plugin
  route stays raw. Reason to dismiss: the bulk endpoint visibly masks the password
  key, so it looks handled; the per-plugin route reads like a thin wrapper. How-type:
  the masked value is a list (the plausible scalar approach would leave it), and the
  configured URL/proxy values are not key-matched at all.
- **I2 plugin settings route (`/api/4/{plugin}/settings`).** A per-plugin settings
  listing for the web UI with its *own* small key list (password/token/secret/...),
  no login-name pattern and no value-level check. Reason to dismiss: a plugin
  convenience view that already masks the obvious keys, not the configuration
  endpoint. How-type: a second, independently maintained implementation, so fixing
  the shared config helper does not touch it.

## Route coverage (security tests)

- `/api/4/config`, `/api/4/config/{section}`, `/api/4/config/{section}/{item}` (L2)
- `/api/4/all/limits` (L1 + I1)
- `/api/4/ip/limits`, `/api/4/ports/limits` (L1)
- `/api/4/ports` (L3)
- `/api/4/ip/settings`, `/api/4/ports/settings` (I2)
- functional: `/api/4/args`, `/api/4/args/{item}`, plus project tests
  tests/test_api.py and tests/test_plugin_ports.py

## Candidate list and why the picks won

Real upstream candidates found by reading the code and the screener's O8 list:

| id | site/route | real | built | reason |
|----|-----------|------|-------|--------|
| C1 | `/{plugin}/limits` raw limits copy | yes | yes (L1) | producer off the check's path; strongest how-type |
| C2 | `/all/limits` raw limits copy | yes | yes (L1) | same producer, bulk route the UI uses |
| C3 | ports stats `url` + nested `proxies` | yes | yes (L3) | protection never existed; nested shape; dismisses as monitoring output |
| C4 | MCP `glances://limits` resources | yes | not built | real, but needs the MCP SSE transport in the verifier; register only |
| C5 | XML-RPC `getAllLimits` (server mode) | yes | not built | real, but a separate legacy transport with its own mode; register only |
| C6 | `config*` secure view | yes (published) | yes (L2) | landing point; URL userinfo shape |
| C7 | `args*` sanitizer | yes (published) | functional only | verified not reachable: `-u` forces a password; `--client` cannot run the web server |
| C8 | exporter limits (`getAllLimitsAsDict` in exports) | yes | no | outbound, not a client-readable response |
| C9 | `serverslist` `uri`/`password` | yes, already sanitised | no | upstream already strips them |

Injected candidates:

| id | site | built | reason |
|----|------|-------|--------|
| I1 | `_sanitize_limits` on all/limits | yes | partial protection that looks complete; array values defeat the scalar check |
| I2 | `/{plugin}/settings` route | yes | far from the landing point; own key list; second implementation |
| I3 | `config/export` raw export | no | a "backup must be complete" argument and deleting the route could be called correct; duplicates C6 |
| I4 | ip stats expose the configured endpoint | no | same concept as C3 (plugin stats copy config); avoids two routes of one concept |
| I5 | diagnostics block on `/status` | no | no natural credential payload; would look planted |
| I6 | proxy-only leak with url redacted | no | that is a *fix*, not a gap |

Picks: I1 and I2 are the two hardest candidates that are still reachable through the
real HTTP entry point and covered by the property, with two different dismissals.
C4/C5 are recorded in the uncovered-route register as real but not built.

## Verified at the pinned commit (behavioural, real server)

- `GET /api/4/config` returns `[ip] public_username` in clear and the `public_api`
  URL userinfo in clear; `public_password` is masked.
- `GET /api/4/all/limits`, `/api/4/ip/limits`, `/api/4/ports/limits` return
  `ip_public_password`, `ip_public_username`, `ip_public_api`,
  `ports_web_1_url`, `ports_web_1_http_proxy` raw.
- `GET /api/4/ports` returns `url` and `proxies.http/https` raw.
- `GET /api/4/args` masks password/username/conf_file and keeps ints/floats/bools.

## Upstream latest (develop, read-only look on 2026-10-24)

The current develop branch (`security-audit-wave-2`, commit 7e77697) has rewritten the
producer: `get_limits()` now computes effective thresholds instead of copying the config
section, and `web_list.py` publishes a sanitised URL and keeps the scan URL/proxies out
of the stats. So `present_in_latest` is `no` for both real B routes; the legacy XML-RPC
server module is gone in latest, and the MCP limits resource uses the same rewritten
producer. The register records this.

## Things I could not verify / guesses

- Whether the two target models actually fail 3/3 (no trials run, per the build rules).
- `present_in_latest` for the real routes: only the pinned tree is available offline here.
- MCP/XML-RPC routes: reachable in principle, not driven by tests.

## Out of scope (one line)

`Config.get_value` backtick command expansion and the exporter/SQL sinks are outside this
advisory's disclosure property and were not pursued.

## Gate results

- static: PASS (2026-10-24)
- nop: PASS — security 16/16 fail on pinned+injection, functional 28/28 pass
- oracle: PASS — 3 runs, reward 1.0 each, security 16/16, functional 28/28
- patches: PASS (13/13 as declared)
  - security_fail: sf-published-only 7/0, sf-no-username 9/0, sf-no-url 12/0,
    sf-no-limits 3/0, sf-no-list-shape 3/0, sf-partial-limits 1/0,
    sf-no-ports 2/0, sf-no-settings 2/0 (security failures / functional failures)
  - functional_fail: ff-overbroad-user 0/3, ff-refuse-all 0/12, ff-crash-config 9/4
  - pass: pass-hardening 1.0, pass-alt-limits-filter 1.0
- final rerun with the frozen artifacts: static PASS; nop PASS (16 security fail, 28 functional pass); oracle PASS (3 runs, reward 1.0 each, 16 security / 28 functional)
