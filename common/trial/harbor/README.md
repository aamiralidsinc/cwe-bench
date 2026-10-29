# Local patches to harbor (VM)

Harbor is installed with `uv tool` on the VM. These patches change its installed site-packages file:

```
~/.local/share/uv/tools/harbor/lib/python3.13/site-packages/harbor/environments/docker/docker.py
```

**A harbor reinstall or upgrade reverts both patches. Re-apply them afterwards.**

| Patch | Script | What it does | Why |
|---|---|---|---|
| A, 2026-10-20 (logging added 2026-10-29) | `patch_teardown.sh` (idempotent) | A non-zero exit from `docker compose down` no longer fails a run; since 2026-10-29 it is logged first as a warning (`compose down failed (rc N), ignored; ...`) in the trial's log | A teardown/network-removal race under concurrency failed runs whose tests had already finished. A failed `down` can leave the project's network behind, and leaked networks exhausted Docker's address pool on 2026-10-29 (reports/gate-compose-rca-20261029.md) |
| B, 2026-10-25 | `patch_probe_timeout.sh` (idempotent) | Raises the nftables kernel-probe timeout in `_egress_control_kernel_support()` from 30 s to 300 s | Under heavy load the probe timed out. Harbor then refused allowlist runs with "network_mode='allowlist' is not supported", and `trial.py` logged them as "session-ended-early … at ~37s". 27 starts were lost on 2026-10-24 |

`patch_teardown.sh` used to contain an old one-time fix to `gate_one_ds.sh` (its part B). That fix is in
`common/gate/gate_one_ds.sh`, so the 2026-10-29 version of the script patches harbor only.

**Check that both patches are present:**

```bash
D=~/.local/share/uv/tools/harbor/lib/python3.13/site-packages/harbor/environments/docker/docker.py
grep -n 'if "down" in full_command' "$D"     # patch A
grep -n 'compose down failed' "$D"           # patch A, logging (2026-10-29)
grep -n 'timeout=300' "$D"                   # patch B
```

**When a trial pair has no graded run,** grep its evidence for `allowlist` before anything else.
