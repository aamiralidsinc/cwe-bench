# asyncssh-inv: instruction experiment (2026-10-16)

Same environment, tests, oracle and patch checks as asyncssh; only instruction.md was rewritten in system+invariant style (BUILDER.md 3i). Fairness map: FAIRNESS.md in this folder. The notes of the original task follow.

# asyncssh stacking task — build notes

Commit **C** = `f67234fb3c36242be0c5c9f29e1fdbbe544fc4e0` (parent of the
handshake fix `83e43f5`). Four real, co-present vulnerabilities, all reachable
at C through the public transport over a loopback socket, offline.

## What I verified
- Every exploit reproduces on a clean checkout of C and flips to safe after the
  upstream source fix (`solution/fix.patch`):
  - early USERAUTH to the server → `vulnerable` → `blocked`
  - early EXT_INFO to the client → `vulnerable` → `blocked`
  - username `../OUTSIDE` with a planted key → authenticates → rejected
    (`IllegalUserName`); the legit per-user lookup keeps working
  - SCP download of `../escaped_evil` → file escapes dst → rejected
    (`SFTPBadMessage`); legit `report.txt` download keeps working
  - channel `max_pktsize=0` → endpoint hangs → `ProtocolError` at channel open
- Full suite from source (CPython 3.9, editable install of C):
  - vulnerable C: 5 security FAIL, 5 functional PASS
  - oracle: 10 PASS (×2, identical, ~1.5s)
- Check patches (local, from source):
  - `subset_fix.patch` (drop the packet-size guard): security 1 fail
    (pktsize) / 4 pass, functional 5 pass → `security_fail`
  - `disable_feature.patch` (SCP name check rejects any `.`): functional 1 fail
    (legit download) / 4 pass, security 5 pass → `functional_fail`
  - `alt_correct_fix.patch`: 10 PASS → `pass`

## Honest caveats
- The oracle fix came banked as `/tmp/fix.patch`; I re-derived its before/after
  behaviour against C rather than trusting it. It applies cleanly (`git apply
  --check` and `patch -p1 --dry-run`) and its three touched files
  (config / connection / scp) have all their symbol dependencies present at C
  (`re`, `IllegalUserName`, `_scp_error`/`SFTPBadMessage`, `ProtocolError`).
- `alt_correct_fix.patch` rewrites the username, SCP-name and packet-size
  guards in a different correct form but keeps the handshake state-machine
  change identical to upstream — a hand-authored alternative for that state
  machine is not plausible to do safely, so the "independent fix" evidence
  covers 3 of the 4 vulns.
- The channel-DoS security test runs its scenario in a subprocess with a 30s
  wall-clock timeout (a vulnerable endpoint hangs in a synchronous loop and
  cannot be caught in-process). On vulnerable/subset runs this adds ~30s per
  security run; the fixed path returns in well under a second.
- Scratch work (clone, worktree at C, venv, exploit scripts, patch generation)
  is under `~/.tb-graders/cwe/work/asyncssh/`.

## 2026-10-16 test repair

Inputs: `build/audit/lenient_items_2026-10-16.txt` (5 `-- REC asyncssh` lines, no `==` items),
`research/own-runs/TEST-REPAIRS.md` § asyncssh, the five audit verdict.json files, plus the
caller's notes (SCP absolute/embedded, a 2nd injected message per direction, the "-1 packet size"
audit note). Only tests/ changed; instruction.md and solution/ unchanged.

### Items and decisions
| item (source) | decision |
|---|---|
| SCP absolute and embedded traversal `'/tmp/x'`, `'a/../../x'` (REC mimo-r1-n001) | **fixed**: `test_scp_download_absolute_path` (absolute name inside tmp, outside dst) and `test_scp_download_embedded_traversal` (`sub/../../embedded_escaped`; `dst/sub` pre-exists, since the kernel needs it to walk through). Both assert only "nothing written outside dst", so containment-check fixes pass too. Fair: the instruction says a name that points outside the destination must be rejected. |
| 2nd injected message type per direction, e.g. SERVICE_REQUEST or CHANNEL_OPEN (REC mimo-r1-n001) | **fixed with other types**. SERVICE_REQUEST and CHANNEL_OPEN pre-kex are *already* refused by C (no service expected yet -> ServiceNotAvailable; the "before auth complete" check covers >= 80), so tests with them pass on vulnerable code and prove nothing (checked: both PASSED on C). Used instead: `test_server_rejects_early_ext_info` (EXT_INFO toward the server; C processes it silently) and `test_client_rejects_early_userauth_success` (an auth-layer packet toward the client; C keeps the connection). Both are inside the instruction's wording (extension-information / authentication-layer packet, drop the connection). |
| "-1 packet size" audit note (REC deepseek-r11-n001: max_pktsize=0 + dropbear banner + compression) | **lenient, fixed**. On a peer whose version names dropbear with compression active, the library subtracts 1 from the advertised size, so an advertised 0 becomes -1; `== 0` / `if not x` guards placed after that adjustment miss it and the endpoint still spins (`buf[:-1]` leaves 1 byte, then empty packets forever; confirmed hang on C and on deepseek-r11's code). New `test_channel_zero_pktsize_dos_dropbear_compression`: the peer still advertises exactly 0 (the instruction's abuse); a guard on the raw advertised value also passes. Not unfair: compression is the library's default and the version string is peer-controlled. |
| Test demands rejection, not just "no hang" (audit note mimo-r1-n001; REC asks to state it) | **skip (already stated)**: instruction "What must hold afterwards" says "Each of the abuses above is rejected through the same public entry points". No instruction change. |
| pktsize in the other direction, server advertises 0 in OPEN_CONFIRMATION (REC mimo-r11-n001) | **fixed**: `test_channel_zero_pktsize_in_open_confirmation` (server created with max_pktsize=0, client sends stdin and must reject). Fair: the instruction says a peer advertising 0 hangs the endpoint; the confirmation is the peer advertising. |
| username variant `'~'` or `'${...}'` (REC mimo-r11-n001) | **skip**: at C the config does no env-var expansion and `~` is not expanded mid-path, so under the instructed template neither name leaves the key directory; refusing them is the upstream design, not the stated property. Added instead the fair sibling `test_authorized_keys_username_embedded_traversal` (`legit/../../OUTSIDE`). |
| final-code/changes.patch missing from postmortems; "fixes liftable from PyPI sdists" (RECs deepseek-r1-n001/n002, mimo-r1-n001) | **skip**: tooling / task-design notes, not test items. |

`_pktsize_scenario.py` now takes a mode (`open` default, `open-dropbear`, `confirm`); the
scenario still lets a connect-time error propagate (rc != 0 fails), only an asyncssh.Error from the
channel phase counts as "blocked". Security tests: 5 -> 12; functional unchanged (5).

### New patch checks (all `security_fail`, functional all pass; local run on C copies)
| patch | fails |
|---|---|
| `pktsize_eq_zero_only.patch` (reference with `== 0`) | dropbear_compression |
| `pktsize_open_only.patch` (no guard on open confirmation) | in_open_confirmation |
| `scp_leading_traversal_only.patch` (rejects only leading `../`) | absolute_path, embedded_traversal |
| `handshake_reported_types_only.patch` (pre-kex guard for the two reported types only) | server early_ext_info, client early_userauth_success |
| `username_leading_traversal_only.patch` (rejects only `..` / leading `../`) | username_embedded_traversal |

Existing checks still behave: subset_fix security_fail (now 3 pktsize tests), disable_feature
functional_fail, alt_correct_fix 1.0. Reference: 17/17 locally.

### Gate
`python3 build/slot.py 3 -- python3 -I builder/gate.py asyncssh` -> **PASSED** (2026-10-16 ~06:10 UTC):
nop 12 security fail / 5 functional pass; oracle 1.0 twice; all 8 patch checks as declared
(subset 0.75, disable_feature 0.0, alt_correct 1.0, eq_zero 0.9167, open_only 0.9167,
scp_leading 0.8333, handshake_reported_types and username_leading as declared). The first gate run
(~05:18-05:34 UTC) stopped at `scp_leading_traversal_only` with a Harbor infra error
("network_mode='allowlist' is not supported by EnvironmentType.DOCKER", the egress-control probe
under VM load); not a test result. Warnings only: no `hardening`/`blind` pass patches (pre-strict task).

### Regrade (only two trials have final-code/changes.patch; both were 1.0, no earlier regrade)
| trial | old | new | failing tests |
|---|---|---|---|
| asyncssh-deepseek-r11-20261015-193957-n001/asyncssh__emBowC5 | 1.0 | 0.9167 | test_pktsize_dos::test_channel_zero_pktsize_dos_dropbear_compression |
| asyncssh-mimo-r11-20261015-194029-n001/asyncssh__iEYziJe | 1.0 | 1.0 | - |

deepseek-r11 drop is a real defect: its guards are `if not send_pktsize: raise` placed *after* the
dropbear `send_pktsize -= 1` adjustment in both channel-open handlers, and the extra loop guard in
`_flush_send_buf` is `and self._send_pktsize` (truthy for -1). A peer with a dropbear version string
and default compression that advertises 0 gets -1 internally and the endpoint spins (reproduced
locally: hang until the 30 s timeout). The regrade ran 05:55 UTC, inside the disk-full window, but
its tests really ran (12+5 results, test-stdout complete), so it stands.
The first mimo-r11 regrade attempt failed at image build (apt, disk-full window) and wrote no
regrade dir; rerun 06:12 UTC -> 1.0.
Not regradable (no final-code/changes.patch): deepseek-r1 n001/n002, mimo-r1 040706/050806/102205.
