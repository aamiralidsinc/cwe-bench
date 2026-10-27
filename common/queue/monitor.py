"""Resource monitor: samples the machine every minute into the queue database, forecasts when disk runs out, and raises
threshold alerts. The dispatcher's admission reads the latest sample (procs.headroom when none is fresh).

    python3 common/queue/cweq.py monitor [--once] [--dry-run]

Each sample (table `metrics`):
  cpu_busy_pct       share of CPU time not idle since the previous sample (/proc/stat)
  load1              1-minute load average
  mem_available_gb, swap_used_gb
  free_disk_gb, root_inode_pct   the repository's file system
  tmp_inode_pct      /tmp inodes in use
  containers, containers_running, images, build_cache_gb   Docker. The image count (`docker images -q`, every
                     images_every_sec) and the build cache (`docker system df`, every docker_df_every_sec; it can take
                     many minutes on a large image store) run in the background and are stopped after their timeouts;
                     samples carry their last results
  jobs               JSON {kind: running} for queue jobs plus work started by other launchers ("+kind")
  disk_burn_gb_h     free-disk loss per hour over the last [monitor] window_min (least squares; negative = growing)
  disk_floor_h       hours until free disk reaches limits.min_free_disk_gb at that rate (NULL when not shrinking)
  inode_burn_pct_h, inode_full_h   the same for root inodes, towards 100 %

Alerts (table `monitor_alerts`): a row when a value crosses its [monitor] threshold (state 'raised') and when it comes
back (state 'cleared'); nothing is written while it stays on the same side. A disk forecast below
[monitor] disk_floor_within_h also queues one extra `cleanup` job per UTC hour.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qdb  # noqa: E402

SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
    ts                 TEXT PRIMARY KEY,         -- UTC
    epoch              REAL NOT NULL,
    cpu_busy_pct       REAL, load1 REAL, mem_available_gb REAL, swap_used_gb REAL,
    free_disk_gb       REAL, root_inode_pct REAL, tmp_inode_pct REAL,
    containers         INTEGER, containers_running INTEGER, images INTEGER, build_cache_gb REAL,
    jobs               TEXT,                     -- JSON {kind: running}
    disk_burn_gb_h     REAL, disk_floor_h REAL, inode_burn_pct_h REAL, inode_full_h REAL
);
CREATE INDEX IF NOT EXISTS metrics_epoch ON metrics (epoch);
CREATE TABLE IF NOT EXISTS monitor_alerts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    name       TEXT NOT NULL,                    -- the threshold, e.g. disk_free_low
    state      TEXT NOT NULL CHECK (state IN ('raised', 'cleared')),
    value      REAL,
    threshold  REAL,
    message    TEXT
);
"""

DEFAULTS = {"tick_sec": 60, "window_min": 60, "fresh_sec": 120, "images_every_sec": 600, "images_timeout_sec": 300,
            "docker_df_every_sec": 3600, "docker_timeout_sec": 1800, "once_wait_sec": 120,
            "retention_days": 7, "disk_free_gb_warn": 300, "load_warn": 200, "mem_available_gb_warn": 40,
            "tmp_inode_pct_warn": 85, "root_inode_pct_warn": 85, "disk_floor_within_h": 6, "inode_full_within_h": 12,
            "cleanup_on_forecast": True}
METRIC_COLS = ("cpu_busy_pct", "load1", "mem_available_gb", "swap_used_gb", "free_disk_gb", "root_inode_pct",
               "tmp_inode_pct", "containers", "containers_running", "images", "build_cache_gb", "jobs",
               "disk_burn_gb_h", "disk_floor_h", "inode_burn_pct_h", "inode_full_h")


def settings(cfg):
    return {**DEFAULTS, **(cfg.get("monitor") or {})}


def ensure_schema(conn):
    conn.executescript(SCHEMA)


def has_table(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


# ---------- sampling (each reader returns None where the machine cannot tell)

def cpu_times():
    """(busy, total) jiffies from /proc/stat, or None."""
    try:
        f = open("/proc/stat").readline().split()[1:]
        v = [int(x) for x in f]
        idle = v[3] + (v[4] if len(v) > 4 else 0)            # idle + iowait
        return sum(v) - idle, sum(v)
    except (OSError, ValueError, IndexError):
        return None


def meminfo():
    out = {}
    try:
        for line in open("/proc/meminfo"):
            k, v = line.split(":", 1)
            out[k] = int(v.split()[0]) / 2**20             # kB -> GB
    except (OSError, ValueError):
        return None, None
    swap = out.get("SwapTotal", 0) - out.get("SwapFree", 0) if "SwapTotal" in out else None
    return (round(out["MemAvailable"], 1) if "MemAvailable" in out else None,
            round(swap, 1) if swap is not None else None)


def inode_pct(path):
    try:
        st = os.statvfs(path)
        return round(100 * (st.f_files - st.f_ffree) / st.f_files, 1) if st.f_files else None
    except OSError:
        return None


def run(cmd, timeout):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


SIZE = re.compile(r"([\d.]+)\s*([kKMGTP]?)B")
UNIT = {"": 1 / 2**30, "k": 1 / 2**20, "K": 1 / 2**20, "M": 1 / 2**10, "G": 1, "T": 2**10, "P": 2**20}


def size_gb(text):
    m = SIZE.search(text or "")
    return round(float(m.group(1)) * UNIT[m.group(2)], 1) if m else None


def docker_counts(timeout=20):
    """(containers, running) from `docker ps`, cheap."""
    a = run(["docker", "ps", "-aq"], timeout)
    r = run(["docker", "ps", "-q"], timeout)
    return (len(a.split()) if a is not None else None, len(r.split()) if r is not None else None)


DF_CMD = ["docker", "system", "df", "--format", "{{json .}}"]
IMAGES_CMD = ["sh", "-c", "docker images -q | wc -l"]


def parse_count(out):
    try:
        return int((out or "").strip().split()[-1])
    except (ValueError, IndexError):
        return None


def parse_df(out):
    """(images, build_cache_gb) from `docker system df --format json` output."""
    images = cache = None
    for line in (out or "").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("Type") == "Images":
            images = int(d.get("TotalCount") or 0)
        elif d.get("Type") == "Build Cache":
            cache = size_gb(d.get("Size"))
    return images, cache


def jobs_running(conn, proc_list=None):
    """{kind: n} for queue jobs leased/running, plus {"+kind": n} for work other launchers started."""
    out = {}
    if has_table(conn, "jobs"):
        for r in conn.execute("SELECT kind, COUNT(*) n FROM jobs WHERE state IN ('leased','running') GROUP BY kind"):
            out[r["kind"]] = r["n"]
    try:
        import procs
        import taskstate
        plist = procs.list_processes() if proc_list is None else proc_list
        for runs in taskstate.running(plist, ignore_own=True).values():
            for kind, _m, _p in runs:
                out["+" + kind] = out.get("+" + kind, 0) + 1
    except Exception:                                     # the counts are a convenience, never a reason to stop
        pass
    return out


def burn(points):
    """Least-squares slope of (epoch, value) in units per hour; None with fewer than 3 points or a span < 5 min."""
    pts = [(t, v) for t, v in points if v is not None]
    if len(pts) < 3 or pts[-1][0] - pts[0][0] < 300:
        return None
    n = len(pts)
    mt = sum(t for t, _ in pts) / n
    mv = sum(v for _, v in pts) / n
    den = sum((t - mt) ** 2 for t, _ in pts)
    return None if den == 0 else sum((t - mt) * (v - mv) for t, v in pts) / den * 3600


class Monitor:
    def __init__(self, conn, cfg, root, proc_list=None, now=time.time, docker=True, wait_df=False):
        self.conn, self.cfg, self.root = conn, cfg, str(root)
        self.s = settings(cfg)
        self.proc_list, self.now, self.docker = proc_list, now, docker
        self.wait_df = wait_df                            # one-shot runs wait briefly for the Docker probes; the loop never
        self.prev_cpu = None
        self.probes = {}                                  # name -> [proc, started, last_start]
        self.last = {}                                    # last known Docker values between probe runs

    def probe_specs(self):
        """name -> (command, every_sec, timeout_sec, apply(out)). Slow Docker reads run in the background."""
        def images(out):
            n = parse_count(out)
            if n is not None:
                self.last["images"] = n

        def df(out):
            _imgs, cache = parse_df(out)
            if cache is not None:
                self.last["build_cache_gb"] = cache
        return {"images": (IMAGES_CMD, self.s["images_every_sec"], self.s["images_timeout_sec"], images),
                "df": (DF_CMD, self.s["docker_df_every_sec"], self.s["docker_timeout_sec"], df)}

    def poll_probes(self, t):
        """Start each probe when due; collect results when done; stop a probe after its timeout. One-shot runs
        (wait_df) wait up to once_wait_sec for each probe."""
        for name, (cmd, every, timeout, apply) in self.probe_specs().items():
            st = self.probes.setdefault(name, [None, 0.0, None])
            if st[0] is None and (st[2] is None or t - st[2] >= every):
                try:
                    st[0] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    st[1] = st[2] = t
                except OSError:
                    st[2] = t
                    continue
            proc = st[0]
            if proc is None:
                continue
            if self.wait_df:
                try:
                    proc.wait(timeout=min(self.s["once_wait_sec"], timeout))
                except subprocess.TimeoutExpired:
                    pass
            if proc.poll() is not None:
                out = proc.stdout.read() if proc.returncode == 0 else ""
                proc.stdout.close()
                apply(out)
                st[0] = None
            elif self.wait_df or t - st[1] > timeout:
                proc.kill()
                proc.wait()
                proc.stdout.close()
                st[0] = None

    def sample(self):
        """One sample dict (not written)."""
        t = self.now()
        m = {"ts": qdb.utc(t), "epoch": t}
        cur = cpu_times()
        if cur and self.prev_cpu is None:                 # first sample: measure over one second
            time.sleep(1)
            self.prev_cpu, cur = cur, cpu_times()
        if cur and self.prev_cpu and cur[1] > self.prev_cpu[1]:
            m["cpu_busy_pct"] = round(100 * (cur[0] - self.prev_cpu[0]) / (cur[1] - self.prev_cpu[1]), 1)
        self.prev_cpu = cur
        try:
            m["load1"] = round(os.getloadavg()[0], 1)
        except OSError:
            pass
        m["mem_available_gb"], m["swap_used_gb"] = meminfo()
        try:
            m["free_disk_gb"] = round(shutil.disk_usage(self.root).free / 2**30, 1)
        except OSError:
            pass
        m["root_inode_pct"] = inode_pct(self.root)
        m["tmp_inode_pct"] = inode_pct("/tmp")
        if self.docker:
            m["containers"], m["containers_running"] = docker_counts()
            self.poll_probes(t)
            m.update(self.last)
        m["jobs"] = json.dumps(jobs_running(self.conn, self.proc_list), sort_keys=True)
        self.forecast(m)
        return m

    def history(self, since):
        if not has_table(self.conn, "metrics"):
            return []
        return self.conn.execute("SELECT epoch, free_disk_gb, root_inode_pct FROM metrics WHERE epoch >= ? "
                                 "ORDER BY epoch", (since,)).fetchall()

    def forecast(self, m):
        hist = [(r["epoch"], r["free_disk_gb"], r["root_inode_pct"]) for r in
                self.history(m["epoch"] - 60 * self.s["window_min"])] + [(m["epoch"], m.get("free_disk_gb"),
                                                                           m.get("root_inode_pct"))]
        slope = burn([(t, d) for t, d, _ in hist])
        if slope is not None:
            m["disk_burn_gb_h"] = round(-slope, 2)
            floor = self.cfg["limits"]["min_free_disk_gb"]
            if slope < 0 and m.get("free_disk_gb") is not None:
                m["disk_floor_h"] = round(max(0.0, (m["free_disk_gb"] - floor) / -slope), 2)
        islope = burn([(t, i) for t, _, i in hist])
        if islope is not None:
            m["inode_burn_pct_h"] = round(islope, 3)
            if islope > 0 and m.get("root_inode_pct") is not None:
                m["inode_full_h"] = round((100 - m["root_inode_pct"]) / islope, 2)

    def checks(self, m):
        """[(name, bad?, value, threshold, message)] for every threshold that can be judged."""
        s, out = self.s, []

        def add(name, value, thr, bad, msg):
            out.append((name, bool(bad), value, thr, msg))      # value None: not judged bad (a forecast may be absent)
        add("disk_free_low", m.get("free_disk_gb"), s["disk_free_gb_warn"],
            m.get("free_disk_gb") is not None and m["free_disk_gb"] < s["disk_free_gb_warn"],
            f"free disk {m.get('free_disk_gb')} GB below {s['disk_free_gb_warn']} GB")
        add("disk_floor_soon", m.get("disk_floor_h"), s["disk_floor_within_h"],
            m.get("disk_floor_h") is not None and m["disk_floor_h"] < s["disk_floor_within_h"],
            f"free disk reaches the {self.cfg['limits']['min_free_disk_gb']} GB floor in {m.get('disk_floor_h')} h "
            f"at {m.get('disk_burn_gb_h')} GB/h")
        add("load_high", m.get("load1"), s["load_warn"], m.get("load1") is not None and m["load1"] > s["load_warn"],
            f"load {m.get('load1')} above {s['load_warn']}")
        add("memory_low", m.get("mem_available_gb"), s["mem_available_gb_warn"],
            m.get("mem_available_gb") is not None and m["mem_available_gb"] < s["mem_available_gb_warn"],
            f"memory available {m.get('mem_available_gb')} GB below {s['mem_available_gb_warn']} GB")
        add("tmp_inodes_high", m.get("tmp_inode_pct"), s["tmp_inode_pct_warn"],
            m.get("tmp_inode_pct") is not None and m["tmp_inode_pct"] > s["tmp_inode_pct_warn"],
            f"/tmp inodes {m.get('tmp_inode_pct')}% above {s['tmp_inode_pct_warn']}%")
        add("root_inodes_high", m.get("root_inode_pct"), s["root_inode_pct_warn"],
            m.get("root_inode_pct") is not None and m["root_inode_pct"] > s["root_inode_pct_warn"],
            f"root inodes {m.get('root_inode_pct')}% above {s['root_inode_pct_warn']}%")
        add("inodes_full_soon", m.get("inode_full_h"), s["inode_full_within_h"],
            m.get("inode_full_h") is not None and m["inode_full_h"] < s["inode_full_within_h"],
            f"root inodes full in {m.get('inode_full_h')} h")
        return out

    def raised(self):
        """{name: True} for alerts whose last row is 'raised'."""
        if not has_table(self.conn, "monitor_alerts"):
            return {}
        rows = self.conn.execute("SELECT name, state FROM monitor_alerts WHERE id IN "
                                 "(SELECT MAX(id) FROM monitor_alerts GROUP BY name)").fetchall()
        return {r["name"]: r["state"] == "raised" for r in rows}

    def alerts(self, m):
        """[(name, state, value, threshold, message)] for the crossings of this sample."""
        was = self.raised()
        out = []
        for name, bad, value, thr, msg in self.checks(m):
            if bad and not was.get(name):
                out.append((name, "raised", value, thr, msg))
            elif not bad and was.get(name):
                out.append((name, "cleared", value, thr, f"{name} cleared: now {value} (threshold {thr})"))
        return out

    def responses(self, m):
        """Jobs to queue: one extra cleanup per UTC hour while disk is forecast to reach its floor soon."""
        if not self.s["cleanup_on_forecast"] or m.get("disk_floor_h") is None \
                or m["disk_floor_h"] >= self.s["disk_floor_within_h"]:
            return []
        return [{"kind": "cleanup", "task": "_machine", "args": {"hour": m["ts"][:13], "extra": "disk forecast"}}]

    def tick(self, dry_run=False):
        """Sample, forecast, alert, respond. Returns {"sample", "alerts", "queued"}; writes nothing on a dry run."""
        m = self.sample()
        al = self.alerts(m)
        resp = self.responses(m)
        if dry_run:
            return {"sample": m, "alerts": al, "queued": [(None, r) for r in resp]}
        ensure_schema(self.conn)
        cols = ["ts", "epoch"] + [c for c in METRIC_COLS if c in m]
        with qdb.tx(self.conn):
            self.conn.execute(f"INSERT OR REPLACE INTO metrics ({', '.join(cols)}) VALUES "
                              f"({', '.join('?' * len(cols))})", [m[c] for c in cols])
            for name, state, value, thr, msg in al:
                self.conn.execute("INSERT INTO monitor_alerts (ts, name, state, value, threshold, message) "
                                  "VALUES (?,?,?,?,?,?)", (m["ts"], name, state, value, thr, msg))
            self.conn.execute("DELETE FROM metrics WHERE epoch < ?", (m["epoch"] - 86400 * self.s["retention_days"],))
        queued = []
        for r in resp:
            jid, created = qdb.enqueue(self.conn, r["kind"], r["task"], r["args"],
                                       priority=self.cfg["priority"].get(r["kind"], 0),
                                       max_attempts=self.cfg["max_attempts"].get(r["kind"], 1), origin="monitor")
            queued.append((jid if created else None, r))
        return {"sample": m, "alerts": al, "queued": queued}


def latest(conn):
    if not has_table(conn, "metrics"):
        return None
    return conn.execute("SELECT * FROM metrics ORDER BY epoch DESC LIMIT 1").fetchone()


def fresh_headroom(conn, cfg, now=None):
    """The admission values from the latest sample when it is younger than [monitor] fresh_sec, else None."""
    try:
        row = latest(conn)
    except Exception:
        return None
    now = time.time() if now is None else now
    if row is None or now - row["epoch"] > settings(cfg)["fresh_sec"]:
        return None
    return {"free_disk_gb": row["free_disk_gb"], "load": row["load1"], "mem_available_gb": row["mem_available_gb"],
            "tmp_inode_pct": row["tmp_inode_pct"]}


def line(m):
    """One printable line for a sample."""
    f = lambda k, u="": "-" if m.get(k) is None else f"{m[k]}{u}"   # noqa: E731
    return (f"{m['ts']} cpu {f('cpu_busy_pct', '%')} load {f('load1')} mem {f('mem_available_gb', 'G')} "
            f"swap {f('swap_used_gb', 'G')} disk {f('free_disk_gb', 'G')} (burn {f('disk_burn_gb_h', 'G/h')}, floor in "
            f"{f('disk_floor_h', 'h')}) inodes {f('root_inode_pct', '%')} /tmp {f('tmp_inode_pct', '%')} containers "
            f"{f('containers_running')}/{f('containers')} images {f('images')} cache {f('build_cache_gb', 'G')} "
            f"jobs {m.get('jobs', '{}')}")
