# Docker hang on klavis-vm: root cause and fix

Date: 2026-10-24. Machine: klavis-vm (GCP n2d-standard-64, 64 CPU, 251 GB RAM, 5 TB disk).
Status: **fixed and verified on synthetic load and on the real build workload.**

## Summary

The repeated Docker "spike" (Docker stops answering, builds and gates fail with "Docker daemon is
not running", the box sits at ~40% CPU) was not a CPU, disk, memory or network limit. It is a known
deadlock in gRPC, the library Docker uses to talk to containerd:
[grpc-go #9330](https://github.com/grpc/grpc-go/issues/9330), a P0 regression since grpc-go v1.82.1.

Docker 29.9.1 is built with grpc-go v1.84.0 and containerd 2.4.2 with v1.83.2; both are affected.
No grpc-go release contains the fix yet, so we applied the documented workaround. With it, the
machine ran 52 real build/gate jobs at once with no hang, and a synthetic test far above the
trigger point ran clean.

Running fewer builds at once (the old "≤16 Docker jobs" rule) never fixed anything. It only made
the deadlock less likely.

## What happens

1. Docker sends all of its work to containerd over **one** gRPC connection on a Unix socket.
2. grpc-go v1.82.1 added a flood-protection limit: when more than 100 bookkeeping items are queued
   on a connection, that side stops reading until its writer drains the queue.
3. Under bursts of many simultaneous calls, both sides hit the limit while their writers are blocked
   on a full socket buffer. Each side waits for the other to read; neither does. The connection is
   stuck forever.
4. Every Docker API call then hangs (`docker ps`, builds, `compose`). Builder agents react by starting
   their own private root `dockerd` daemons, which adds load.

**What creates the burst:** the image store held 2,362 images (9,395 blobs). With the containerd
image store, every `docker images`, `docker compose` run and build-layer commit checks every image
in parallel, so a handful of these commands at once becomes hundreds of gRPC calls. At the hang
(05:57 UTC) there were 20 `docker images` calls in flight (from builder agents) and 45 hung
`docker compose` runs (from gates). That is why the hang showed up at 16, 24 or 40 builds: the
trigger is coinciding image commands times store size, not container count. It also explains why
gating seemed to set it off.

## Evidence

Captured live during the 05:57 hang (files on the VM in `/home/mara/spike/`):

- `dockerd-goroutines-0609.log`: 519 containerd calls stuck waiting for a reply (309 `content.Info`,
  83 `images.Get`, 49 content reads). Docker's gRPC writer was blocked writing to the socket and its
  reader was stopped by the throttle, both for 12 minutes.
- `containerd-goroutines-0611.log`: containerd idle. None of those calls reached it; its own writer
  was blocked as well.
- Kernel socket queues on the Docker↔containerd connection: 130 KB unread on Docker's side and 40 KB
  unread on containerd's side. Neither side was reading.

## Proof

| Test | Calls in flight at once | Result |
|---|---|---|
| Real hang, 05:57 | 519 | deadlock |
| Synthetic, unchanged config, 40 workers | 1,359 | deadlock in ~30 s, same signature |
| Synthetic, fix applied, 40 workers, 15 min | not measured | no deadlock; Docker answered in 56 ms median, 79 ms max |
| Synthetic, fix applied, 120 workers, 8 min | 3,800–8,000 | no deadlock; never throttled |
| **Real workload, fix applied, 52 jobs, 07:40–10:45** | **peak 437** | **no deadlock; 52 of 52 gates passed** |

The synthetic test (`/home/mara/spike/stress.sh`) runs parallel `docker images`, image inspects and
small classic builds that commit layers, which is the same fan-out as the real workload.

Real workload (52 frozen jobs resumed from saved agent sessions, 5–20 s stagger):

- CPU: 56% average, 88% p95, 99% peak (≥80% for 12% of the run, mostly once gates went parallel).
- Docker response: 510 ms median, 7.6 s p99, 13.3 s max. The slow moments were all at 95–100% CPU,
  when Docker had to compete with ~100 compile jobs. Docker always answered. The CPU-priority change
  below targets this.
- 0 private `dockerd` daemons started by agents (23 in the 40 minutes before the fix).

## The fix (machine-wide, persistent, reversible)

Script: `/home/mara/spike/apply_fix.sh` (undo: `apply_fix.sh revert`).

1. **gRPC throttle limit 100 → 10,000** (the maximum grpc-go allows) for both daemons:
   `/etc/systemd/system/{docker,containerd}.service.d/grpc-throttle.conf`
   ```
   [Service]
   Environment=GRPC_GO_EXPERIMENTAL_CONTROL_BUFFER_THROTTLE_LIMIT=10000
   ```
2. **Default socket buffers 208 KB → 4 MB**, so the Unix-socket writer blocks far less often:
   `/etc/sysctl.d/90-grpc-unix-sockbuf.conf`
   ```
   net.core.wmem_default = 4194304
   net.core.rmem_default = 4194304
   net.core.wmem_max = 8388608
   net.core.rmem_max = 8388608
   ```
3. **CPU priority for Docker and containerd:** `CPUWeight=1000` (default 100), applied with
   `systemctl set-property`, so the daemons stay responsive when the CPU is full.
   Undo: `bash /home/mara/spike/run.sh cpu-priority-revert`.

Margin: the 10,000 limit is not unlimited. The 120-worker test reached 8,000 calls in flight; the
real workload peaked at 437, so there is wide headroom but not infinite.

**Permanent fix:** upgrade Docker and containerd once they ship with a grpc-go release containing
PR #9431 / commit c0ef498 (merged 2026-09-24, not released as of 2026-10-24). Then the throttle
environment variable can be removed.

## Other changes made today

- **Gates run in parallel within each stage** (`builder/gate.py`, function `run_parallel`). A gate
  is 12 Harbor trials: 1 nop, 3 oracle, ~8 patch checks. Previously they ran one after another
  (~45 min per gate). Now nop runs first, then the oracle runs together, then all patch checks
  together. That makes ~15 min per gate. The verdict is unchanged: errors surface in the same order
  as the sequential loop. `GATE_PARALLEL=N` caps the width. Old version:
  `builder/gate.py.bak-seq-20261024T084432Z`. **This file is shared, so stacking gates also run in
  parallel now.**
- **Root disk mounted without online `discard`** (`mount -o remount,nodiscard /`; weekly `fstrim.timer`
  reports freed space instead). Not in `/etc/fstab`, so a reboot restores `discard`.
- **Old guard retired:** the "shims > 45 or ≤ 16 Docker jobs" wedge guard was a false alarm and itself
  capped concurrency near 16 (the 40% CPU plateau). The monitor now alarms at 300 shims.

## Notes for the stacking pipeline

- No Docker-related concurrency cap is needed any more. Stagger starts (5–20 s) as before.
- Gate time is now dominated by 3 sequential waves of trials, each capped at 2 CPUs per container by
  Harbor, plus Docker container start-up.
- Both batches share one Docker image store. **Do not clean images by name pattern**: the earlier
  "remove sibling images" cleanup would now delete this batch's 50 `-ds` images. All 219 `stk-`
  images are intact.
- The build prompt should forbid builder agents from starting their own `dockerd`. It hasn't
  happened since the fix, but agents did it during every hang.
- The parked sibling-injection batch (69 gate-sound tasks of 74) lives under `-ds` slugs in
  `tasks/`, `build/` and `~/.tb-graders/cwe/work/`. Leave it in place.

## Files

| What | Where (VM) |
|---|---|
| Fix script | `/home/mara/spike/apply_fix.sh` |
| Stress test | `/home/mara/spike/stress.sh` |
| Monitor (2 s metrics, auto-snapshots) | `/home/mara/spike/monitor.py`, `monitor.csv`, `snapshots/` |
| Goroutine dumps of the hang | `/home/mara/spike/dockerd-goroutines-0609.log`, `containerd-goroutines-0611.log` |
| Stress results | `/home/mara/spike/stress-unfixed-070932/`, `stress-fixed40-071220/`, `stress-fixed120-072909/` |
| Locked backup of the frozen workload | `/home/mara/spike/freeze-20261024T063624Z/` (`chattr +i`) |
