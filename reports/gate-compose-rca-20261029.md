# Gate compose failures on klavis-vm: root cause (2026-10-29)

Investigated 18:35–19:00 UTC on klavis-vm. Working files on the VM: `~/scratch/rca/`.

## Root cause

**Docker has run out of network subnets.** Since 10-20, Harbor runs have leaked their compose networks, and
the leaked networks now hold almost the whole address pool.

- **The pool.** `daemon.json` sets one pool, `172.16.0.0/12` split into `/24`s. That is **4,096 networks**
  at most, and each bridge network takes one `/24`.
- **The leak.** At 18:36 there were **3,926 networks**. **3,754** of them had no container attached in any
  state (running, exited, created or dead). All but two were Harbor run networks
  (`<task>__<id>__env_default` 1,905 and `<task>__<id>__verifier__trial_default` 1,847).
- **What is left.** That leaves about **150–200 subnets** for everything that is running.
- **When it breaks.** When enough gate trials start at once, the free `/24`s run out. Every
  `docker compose up` in that second then fails at its first step, creating the network:

```
Network stk-vm2-ghsa3vgf__denksyt__env_default Creating
Network ... Error Error response from daemon: all predefined address pools have been fully subnetted
failed to create network stk-vm2-ghsa3vgf__denksyt__env_default: Error response from daemon: all predefined address pools have been fully subnetted
```

The command exits with code 1 at once. It is not a timeout, a deadlock or a slow daemon. The same message is
behind all three GATE-ERRORs:

| Gate | Failing check | Failing compose project |
|---|---|---|
| stk-vm2-ghsa3vgf | chk-miss_inventory | `__env` |
| stk-filesystem-spec-92 | chk-crash_on_templates | `__verifier__trial` |
| stk-swig-7564 | chk-miss_basepath | `__env` |

Each of the 4 infra attempts of each gate failed on this message.

### Why the networks leak

The network is removed only by `docker compose down`. Several paths remove the containers but never call
`down`, so the network stays forever:

1. **Agent trials (the largest source, about 59%).**
   - `common/trial/run_trial.sh:85` passes `--ek keep_containers=true`, so Harbor's `stop()` runs only
     `compose stop`.
   - `trial.py remove_container()` then runs `docker rm -f` on `…__env-main-1` (and on a
     `-netguard-1` sidecar, a name that no longer exists).
   - The egress sidecar and the verifier containers stay behind as exited containers. `hourly_cleanup.sh`
     step 1 later removes them with `docker rm -v`.
   - Nothing ever removes the networks. Each agent trial leaks **2** networks.
   - Evidence: 1,139 of the 1,905 leaked `__env` networks and 1,066 of the 1,847 leaked
     `__verifier__trial` networks belong to trials listed in `build/audit/kept_containers.tsv`.
   - Live example at 18:37:24: `kirby-s2__buz66pn__env-main-1` was destroyed alone. Its sidecar and verifier
     containers stayed exited, and both networks remained.
2. **Killed or stopped runs** (`identity.stop`, `throttle_gates.py`, gate timeouts and kills). These remove
   containers with `docker rm -f` and do not run `down`.
3. **Ignored `down` failures.** `common/trial/harbor/patch_teardown.sh` patched Harbor so that a non-zero
   `compose down` returns silently. A teardown that fails at network removal leaves the network, and no log
   says so.
4. **No network cleanup anywhere.**
   - `gate.py` dropped its network prune on 2026-10-20. Its comment says: *"daemon.json now gives
     172.16.0.0/12 in /24 pools (~4096 networks), so address-pool exhaustion is no longer a risk"*.
   - `trial.py`'s prune is off unless `CWE_NET_PRUNE=1`.
   - `hourly_cleanup.sh` removes containers and images but never networks.

### Timeline

The first table counts networks that still exist and were created before each time. That is a lower bound on
the total, but leaked networks never go away, so it tracks the leak closely.

| Time (UTC) | Networks (lower bound) |
|---|---|
| 10-20 | 2 |
| 10-22 | 96 |
| 10-24 | 551 |
| 10-26 | 983 |
| 10-27 | 1,743 |
| 10-28 00:00 | 2,313 |
| 10-29 00:00 | 3,553 |
| 10-29 06:00 | 3,819 |
| 10-29 16:30 | 3,865 (about 230 /24s free) |

| Time (UTC) | Event |
|---|---|
| 16:27–16:31 | Gate slots raised to 36/64/12 and the build cap to 40. More gate trials run at once. |
| 16:56 | First "fully subnetted" evidence of the session. |
| 17:25:35 – 18:20:20 | **258 gate trial starts failed** with this error. They came in bursts: up to 15 in the same second (for example 17:59:53 ×12, 18:10:19 ×15, 18:12:05 ×15, 18:19:46 ×10). |
| 18:20 – 19:00 | 0 failures. Peak network count 3,946 (2-second sampler). Fewer gate trials ran at once. |

Leaks per day, by network creation date:

| 10-20 | 10-21 | 10-22 | 10-23 | 10-24 | 10-25 | 10-26 | 10-27 | 10-28 | 10-29 so far |
|---|---|---|---|---|---|---|---|---|---|
| 15 | 79 | 208 | 247 | 246 | 184 | 699 | 529 | 1,234 | 313 |

The leak is still running: the live event stream showed 174 network creates against 170 destroys in 21
minutes.

### Concurrency

Gate trials running at once, rebuilt from the `started_at`/`finished_at` fields in the gate-jobs
`result.json` files, compared with the failure bursts:

| Time window | Gate trials running at once | Failures |
|---|---|---|
| 17:26 | 61 | 17:25–17:27 |
| 17:48 | 64 | 17:47–17:48 |
| 17:52 | 66 | 17:51 |
| 18:00 | 66 | 17:59–18:00 |
| 18:12 | 62 | 18:10–18:12 |
| 18:16–18:18 | 61–63 | 18:15–18:20 |
| 18:20–18:50 | at most about 54 | none |

On top of the gate trials, about 70 `harbor run` processes were live (68 gates and 3 agent trials at 18:55),
along with 40–56 `docker compose` and 8–15 `docker build` processes.

A gate trial holds up to 2 networks at once: its `__env` project and, while it verifies, its
`__verifier__trial` project. The 18:36 snapshot showed what was holding networks besides the leak:

| Networks in use | Count |
|---|---|
| With running containers | 123 |
| With only exited containers | 39 |
| With only "created" containers | 27 |

With about 3,870 leaked networks permanently held, a burst of about 200 live networks fills the pool. Docker's
allocator (moby `defaultipam.allocatePredefinedPool`) searches every gap in the pool before it gives up, so
this error means the pool really was full at that instant.

### Why it hits the patches stage

`gate.py run_parallel` starts all patch checks of a stage together (`GATE_PARALLEL=all`). That is about 8–12
trials per gate, each creating an `__env` network and then a `__verifier__trial` network. The patches stage is
therefore each gate's widest burst of network creates, and it lines up with other gates' bursts.

The stage fails if any one check fails, and an infra retry reruns the whole stage. So under exhaustion, a
10-check stage is far less likely to get through 4 attempts than nop (1 trial) or oracle (3 trials).

nop and oracle trials hit the same error too: 52 nop and 19 oracle evidence files today, against 36 for
patches. They recover more often only because they run fewer trials.

The gate's classifier has no pattern for this message, so it shows as
`[unclassified infrastructure error]`.

## Ruled out

| Suspect | Finding |
|---|---|
| gRPC deadlock (docker-fix.md) | Docker API answered in 37–80 ms on every 30-second sample (18:37–18:58). The error is an immediate daemon reply, not a hang. |
| Client and compose timeouts | `COMPOSE_HTTP_TIMEOUT=300`, `DOCKER_CLIENT_TIMEOUT=300` and `DOCKER_BUILDKIT=0` are set in the environment of the live `harbor run -p /tmp/gate-…` processes (checked in `/proc/<pid>/environ`). The failure is not a timeout. |
| Bulk `docker rmi` (`~/scratch/imgdel.sh`, from 18:25) | Failures stopped at 18:20, before it started, and there were none while it ran. |
| Hourly cleanup | Not a direct cause: it never touches networks. Passes have run back to back since 16:59 and now take 30–50 min (53–163 GB build cache, about 300 dangling images each). There were 22 `failed to delete container from containerd: DeadlineExceeded` at 17:50. That can slow teardowns, but it does not explain the error. |
| Subnet overlap with host routes | All 3,911 bridges are distinct `/24`s inside 172.16/12. The only other 172.x routes are `docker0` (172.16.0.0/24) and `privdocker0` (172.31.250.0/24). There is no private-dockerd activity in the kernel log today. |
| Port allocation, nofile, pids, inotify, disk | No related errors. Limits: nofile 1,048,576; `pid_max` 4,194,304; inotify instances 8,192; file handles 32,768 in use. Disk has 645 GB or more free. |
| iptables lock | No lock errors. But 3,900 bridges mean about 20,000 iptables rules (`iptables-save` gives 20,063 lines), so every network create or delete rewrites a large ruleset. Cleaning up the leak also helps here. |

Side observation, not the cause: the docker journal logs about 1,000 `healthcheck failed … only one
connection allowed` warnings per day. They have done so since 10-25, at the same rate before and after
16:30.

## What I applied

Only read-only observation. I started three samplers, which are my own processes:

- `~/scratch/rca/sampler.sh`, every 30 s: compose, build and harbor process counts, network count, and
  `docker version` latency. Log: `sampler.log`.
- `~/scratch/rca/fast.sh`, every 2 s: the count of 172.x bridge routes. It stops itself after 40 min.
  Log: `fast.log`.
- A `docker events` logger for network and container events. Log: `events.log`.

I also created and removed one probe network, which got 172.16.208.0/24.

**Not applied: removing the leaked networks.** The permission system blocked the run, so it waits for the
owner's go. The script is ready: `~/scratch/rca/netclean.sh`.

- **What it removes.** Only networks that meet all of these:
  - named `…__env_default` or `…__verifier__trial_default`, with a compose project label;
  - created more than 2 h ago;
  - not referenced by any container in any state. The script re-reads `docker ps -a` every 100 networks.
- **Docker's own guard.** Docker also refuses `network rm` on any network with an attached endpoint.
- **How it runs.** One network at a time with a 0.2 s pause, so live network creates are not starved. Each
  removal is logged to `netclean.log`.
- **Expected effect.** It frees about 3,700 `/24`s and about 18,000 iptables rules. No Docker or containerd
  restart and no release are needed.

How to run it:

```
cd ~/scratch/rca && MAX=20 ./netclean.sh && tail netclean.log   # trial batch
setsid nohup ./netclean.sh >/dev/null 2>&1 < /dev/null &        # then the rest
```

## Fixes, ranked by impact and risk

### 1. Remove the leaked networks now (no restart, no release; owner's go)

Run `~/scratch/rca/netclean.sh` as above. This alone ends the failures for weeks at the current leak rate,
which has been up to about 1,200 a day.

### 2. Stop the leak: clean networks in `hourly_cleanup.sh` (pipeline code; release)

This is the permanent guard. It covers every leak path above, including ones not yet known.

```diff
--- a/common/util/hourly_cleanup.sh
+++ b/common/util/hourly_cleanup.sh
@@ pass() {
   xargs -a /tmp/hc-containers.$$ -r -P 8 -n 20 sh -c 'timeout 300 docker rm -v "$@" > /dev/null 2>&1; true' _
   log "  stopped containers removed: $(wc -l < /tmp/hc-containers.$$)"
+  # 1b. leaked Harbor compose networks (reports/gate-compose-rca-20261029.md). Trials run with keep_containers=true
+  #     (compose stop only), and step 1 / trial.py / identity.stop remove containers with `docker rm`, which never
+  #     removes the project's network; each network holds one /24 of daemon.json's 4096 and the pool ran out on
+  #     2026-10-29. Only Harbor run projects (__env / __verifier__trial), created > 2 h ago, that no container in
+  #     any state references; Docker itself refuses a network with an attached endpoint. Serial, to spare live creates.
+  timeout 600 docker ps -a --format '{{.Networks}}' 2>/dev/null | tr ',' '\n' | sort -u > /tmp/hc-netsused.$$
+  local ncut; ncut=$(date -u -d '-2 hours' '+%Y-%m-%d %H:%M:%S')
+  timeout 300 docker network ls --filter label=com.docker.compose.project --format '{{.Name}}	{{.CreatedAt}}' 2>/dev/null |
+    awk -F'\t' -v c="$ncut" 'substr($2,1,19) < c && $1 ~ /__(env|verifier__trial)_default$/ {print $1}' |
+    grep -vxF -f /tmp/hc-netsused.$$ | grep -viE "$keep" > /tmp/hc-nets.$$
+  timeout 1800 xargs -a /tmp/hc-nets.$$ -r -n 20 sh -c 'timeout 300 docker network rm "$@" > /dev/null 2>&1; true' _
+  log "  leaked compose networks removed (attempted): $(wc -l < /tmp/hc-nets.$$); networks now: $(timeout 120 docker network ls -q | wc -l)"
+  rm -f /tmp/hc-netsused.$$ /tmp/hc-nets.$$
   # 2. per-run images older than 1 h
```

### 3. Stop the leak at its biggest source: `trial.py` (pipeline code; release)

`remove_container` should remove the whole compose project of the trial: the egress sidecar, the verifier
project's containers and both networks.

```diff
--- a/common/trial/trial.py
+++ b/common/trial/trial.py
@@ def remove_container(container):
     subprocess.run(["docker", "rm", "-f", container], capture_output=True)
     subprocess.run(["docker", "rm", "-f", container.replace("-main-1", "-netguard-1")], capture_output=True)
     if image and not image.startswith("cwe-reuse/"):   # shared per-task image: aged out by hourly_cleanup.sh
         subprocess.run(["docker", "rmi", image], capture_output=True)   # fails harmlessly if shared
+    # Harbor ran with keep_containers=true (compose stop only): the egress sidecar, the separate verifier's
+    # containers and both compose networks are still there. Each network holds one /24 of the 4096-network pool
+    # (reports/gate-compose-rca-20261029.md), so remove the whole project, as `compose down` would.
+    env = container.removesuffix("-main-1")                          # <trial>__env
+    for proj in (env, env.removesuffix("__env") + "__verifier__trial"):
+        ids = subprocess.run(["docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={proj}"],
+                             capture_output=True, text=True).stdout.split()
+        if ids:
+            subprocess.run(["docker", "rm", "-f", *ids], capture_output=True)
+        subprocess.run(["docker", "network", "rm", f"{proj}_default"], capture_output=True)
```

The same pattern belongs in two more places:

- `common/queue/identity.py` `stop()`: after `rm -f` of the job's containers, run `docker network rm` on
  their projects' `_default` networks.
- `pipelines/router/throttle_gates.py`: the same.

Fix 2 catches these anyway, about 2 h later.

### 4. Name the error and retry it in place (pipeline code; release; low risk)

This only reduces the damage while the pool is tight. It does not fix anything.

```diff
--- a/common/gate/gate.py
+++ b/common/gate/gate.py
@@ INFRA_SIGNATURES = [
     (r"network \S+ not found", "docker network vanished between create and attach"),
+    (r"all predefined address pools have been fully subnetted",
+     "docker address pool exhausted (leaked compose networks; reports/gate-compose-rca-20261029.md)"),
```

Optionally, add `"fully subnetted"` to `RETRYABLE` with a 30–60 s randomized backoff. Under exhaustion the
pool frees up within seconds, as trials finish, so an in-place retry of the one trial would save the whole
stage.

### 5. Make ignored `down` failures visible (Harbor patch; low risk)

Have the `patch_teardown.sh` branch log before it returns. Then leaks from failed teardowns show up in
`trial.log`.

```diff
-            if "down" in full_command:
-                return result  # teardown is best-effort; a network-removal race must not fail a completed run
+            if "down" in full_command:
+                self.logger.warning(f"compose down failed (rc {result.return_code}), ignored: {(result.stdout or '')[-500:]}")
+                return result  # teardown is best-effort; a network-removal race must not fail a completed run
```

### 6. More address space (`daemon.json`; needs a dockerd restart; owner decision; not needed after fixes 1 and 2)

The minimal change is a smaller subnet size in the same range:

```diff
   "default-address-pools": [
-    { "base": "172.16.0.0/12", "size": 24 }
+    { "base": "172.16.0.0/12", "size": 26 }
   ],
```

- **What it gives.** 16,384 networks of 62 hosts each, which is plenty for main plus sidecar. Existing `/24`s
  stay as they are.
- **What to avoid.** Do not add a `10.x` pool: the VM sits in GCP's `10.128.0.0/9` range, and the host
  already has `10.45`, `10.60`, `10.61`, `10.78`, `10.99`, `10.111`, `10.151` and `10.180` routes.
- **The cost.** More networks also mean more iptables rules. Fixing the leak is better than making room for
  it.

### Not recommended

Lowering gate parallelism or capping container starts. The load is not the problem. It only crosses a
ceiling that the leak keeps lowering.

## Evidence files (VM)

| File | Contents |
|---|---|
| `~/scratch/rca/nets.tsv`, `ctrs.tsv`, `unused_nets.tsv` | Network and container snapshots at 18:36, and the 3,754 networks with no container |
| `~/scratch/rca/subnets.txt` | Subnet of every network: 3,911 distinct `/24`s |
| `~/scratch/rca/occ2.txt` | 258 exact failure times from the gate-jobs `result.json` files |
| `~/scratch/rca/events.log`, `sampler.log`, `fast.log` | Live events and samples from 18:37 |
| `~/cwe-bench/build/{stk-vm2-ghsa3vgf,stk-filesystem-spec-92,stk-swig-7564}/evidence/*gate-patches*` | Full compose output of the failures |
