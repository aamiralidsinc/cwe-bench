"""divq core: the diversity experiment's work queue for GitHub Actions (see DESIGN.md).

The truth lives on disk (out/results/, the decrypted artifacts). The DB (out/divq.db) holds only work in flight
plus the track record; delete it and the next reconcile rebuilds the same jobs from the artifacts and the batch.

Every call that talks to GitHub takes an executor object (divq_gh.GH in production, a fake in the tests), so the
core has no GitHub dependency and is unit-tested offline. Python 3.11+ (tomllib). Standard library only.
"""
import csv, hashlib, json, os, shutil, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError as e:  # pragma: no cover
    raise SystemExit("divq needs Python 3.11+ (tomllib); run it with a 3.12 interpreter") from e

HERE = Path(__file__).resolve().parent          # diversity_population/pipeline
DIV = HERE.parent                               # diversity_population
ACTIVE = ("dispatched", "running")
WORKFLOW = {"build": "build", "trial_run": "trial"}


def utc(t=None):
    return datetime.fromtimestamp(t if t is not None else time.time(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def canon(d):
    return json.dumps(d or {}, sort_keys=True, separators=(",", ":"))


# ------------------------------------------------------------------ settings
class Settings:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get("DIVQ_SETTINGS") or HERE / "settings.toml")
        self.raw = self.path.read_bytes()
        self.data = tomllib.loads(self.raw.decode())
        self.hash = hashlib.sha256(self.raw).hexdigest()[:16]

    def get(self, *keys, default=None):
        d = self.data
        for k in keys:
            if not isinstance(d, dict) or k not in d:
                return default
            d = d[k]
        return d

    def p(self, key):
        v = os.path.expanduser(self.data["paths"][key])
        return Path(v) if os.path.isabs(v) else DIV / v

    def accounts(self, enabled_only=True):
        return [a for a in self.data.get("accounts", []) if a.get("enabled") or not enabled_only]


# ------------------------------------------------------------------ database
SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL, task TEXT NOT NULL, args TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL DEFAULT 'queued',
  attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 2,
  account TEXT, run_id TEXT, token TEXT, release TEXT, settings_hash TEXT,
  created TEXT NOT NULL, queued_at TEXT NOT NULL, dispatched_at TEXT, started TEXT, finished TEXT,
  gh_status TEXT, waited_sec REAL, result TEXT, checks TEXT, origin TEXT NOT NULL DEFAULT 'reconciler',
  UNIQUE(kind, task, args)
);
CREATE TABLE IF NOT EXISTS settings (hash TEXT PRIMARY KEY, file TEXT, text TEXT,
  first_loaded TEXT, last_loaded TEXT, loads INTEGER DEFAULT 0, loaded_by TEXT);
CREATE TABLE IF NOT EXISTS releases (id TEXT PRIMARY KEY, created TEXT, commit_sha TEXT, tasks INTEGER,
  payload TEXT, payload_bytes INTEGER, note TEXT);
CREATE TABLE IF NOT EXISTS release_log (ts TEXT, frm TEXT, too TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS limits (account TEXT PRIMARY KEY, lim INTEGER, changed_epoch REAL);
CREATE TABLE IF NOT EXISTS limit_log (ts TEXT, account TEXT, old INTEGER, new INTEGER, reason TEXT);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, task TEXT,
  payload TEXT, dedup TEXT UNIQUE, state TEXT DEFAULT 'open', action TEXT);
"""


def connect(path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA)
    return c


def kv_get(c, k, default=None):
    r = c.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
    return r["v"] if r else default


def kv_set(c, k, v):
    c.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, str(v)))


def record_settings(c, s, who):
    now = utc()
    c.execute("INSERT INTO settings(hash,file,text,first_loaded,last_loaded,loads,loaded_by) VALUES(?,?,?,?,?,1,?) "
              "ON CONFLICT(hash) DO UPDATE SET last_loaded=excluded.last_loaded, loads=loads+1, loaded_by=excluded.loaded_by",
              (s.hash, str(s.path), s.raw.decode(), now, now, who))


def event(c, kind, task="", payload=None, dedup=None):
    """One event per real change. The dedup key makes a repeated emit of the same change a no-op."""
    try:
        c.execute("INSERT INTO events(ts,kind,task,payload,dedup) VALUES(?,?,?,?,?)",
                  (utc(), kind, task, canon(payload), dedup or f"{kind}|{task}|{canon(payload)}"))
        return True
    except sqlite3.IntegrityError:
        return False


# ------------------------------------------------------------------ the batch
def read_batch(s):
    """Every chunk's tasks in chunk-then-score order, with a stable opaque id (d001.. by all_chunks row)."""
    out = []
    for i, r in enumerate(csv.DictReader(open(s.p("chunks") / "all_chunks.tsv"), delimiter="\t"), 1):
        out.append({"slug": r["slug"], "tid": f"d{i:03d}", "chunk": int(r["chunk"]), "order": int(r["order"]),
                    "entry_id": r["entry_id"], "pattern": r["pattern"], "repo": r["repo"],
                    "score": float(r["score_read"] or 0)})
    return out


def task_priority(s, t):
    chunks = s.get("dispatch", "chunks", default=[1])
    if t["chunk"] not in chunks:
        return None
    step = s.get("dispatch", "chunk_priority_step", default=100)
    return (len(chunks) - chunks.index(t["chunk"])) * step + (70 - t["order"])


# ------------------------------------------------------------------ results on disk = the truth
def read_results(s, slug):
    base = s.p("results") / slug
    out = {"build": None, "build_tokens": [], "runs": {}, "task_toml": None}
    for f in sorted((base / "build").glob("*/divq-result.json")):
        r = json.loads(f.read_text()); r["_dir"] = str(f.parent)
        out["build_tokens"].append(f.parent.name)
        if out["build"] is None or r.get("status") != "error":
            out["build"] = r
        tt = f.parent / "root" / "tasks" / slug / "task.toml"
        if tt.is_file():
            out["task_toml"] = str(tt)
    for f in sorted((base / "trials").glob("*/divq-result.json")):
        r = json.loads(f.read_text()); r["_dir"] = str(f.parent)
        out["runs"].setdefault(r.get("model"), []).append(r)
    return out


def task_resources(task_toml):
    if not task_toml:
        return None, None
    try:
        env = tomllib.loads(Path(task_toml).read_text()).get("environment") or {}
    except Exception:
        return None, None
    return env.get("cpus"), env.get("memory_mb")


def model_state(runs, n_runs):
    graded = [r["reward"] for r in runs if r.get("graded") and r.get("reward") is not None]
    if any(float(x) >= 1.0 for x in graded):
        return "solved", graded
    if len(graded) >= n_runs:
        return "failed", graded
    return "open", graded


def stage(s, t, res=None):
    """One stage per task, from files on disk only."""
    res = res or read_results(s, t["slug"])
    b = res["build"]
    if not b:
        return "waiting_build"
    if b.get("status") != "sound":
        return {"unsound": "unsound", "gate_error": "gate_error",
                "build_incomplete": "build_incomplete"}.get(b.get("status"), "build_error")
    cpus, mem = task_resources(res["task_toml"])
    if (cpus and cpus > s.get("runner", "cpus", default=4)) or (mem and mem > s.get("runner", "memory_mb", default=16000)):
        return "too_big_for_runner"
    states = [model_state(res["runs"].get(m, []), s.get("trial", "runs", default=3))[0]
              for m in s.get("trial", "models", default=["deepseek", "mimo"])]
    if states and all(v == "failed" for v in states):
        return "breaker_candidate"
    if states and all(v != "open" for v in states):
        return "done_not_breaker"
    return "trialing"


# ------------------------------------------------------------------ jobs / reconcile
def enqueue(c, s, kind, task, args=None, priority=0, origin="reconciler"):
    now = utc()
    ma = s.get("limits", "max_attempts", kind, default=2)
    return c.execute("INSERT OR IGNORE INTO jobs(kind,task,args,priority,max_attempts,created,queued_at,origin) "
                     "VALUES(?,?,?,?,?,?,?,?)", (kind, task, canon(args), priority, ma, now, now, origin)).rowcount == 1


def jobs_for(c, task, kind=None):
    if kind:
        return c.execute("SELECT * FROM jobs WHERE task=? AND kind=? ORDER BY id", (task, kind)).fetchall()
    return c.execute("SELECT * FROM jobs WHERE task=? ORDER BY id", (task,)).fetchall()


def reconcile(c, s, dry_run=False):
    """Derive jobs from disk. Idempotent: the same files always give the same set of jobs."""
    planned, terminal = [], ("unsound", "gate_error", "build_incomplete", "build_error",
                             "too_big_for_runner", "breaker_candidate", "done_not_breaker")
    for t in read_batch(s):
        pr = task_priority(s, t)
        if pr is None:
            continue
        res = read_results(s, t["slug"])
        stg = stage(s, t, res)
        mark = f"stage|{t['slug']}"
        if kv_get(c, mark) != stg and not dry_run:
            if kv_get(c, mark) is not None and stg in terminal:
                event(c, f"stage.{stg}", t["slug"], {"from": kv_get(c, mark)})
            kv_set(c, mark, stg)
        if stg == "waiting_build":
            seen = jobs_for(c, t["slug"], "build")
            if not any(j["state"] in ("queued",) + ACTIVE for j in seen) \
               and not any(j["state"] in ("done", "failed", "blocked") for j in seen):
                planned.append(("build", t["slug"], {"tid": t["tid"]}, pr))
        elif stg == "trialing":
            b = res["build"]
            for m in s.get("trial", "models", default=["deepseek", "mimo"]):
                ms, graded = model_state(res["runs"].get(m, []), s.get("trial", "runs", default=3))
                if ms != "open":
                    continue
                want = [1] if not graded else list(range(len(graded) + 1, s.get("trial", "runs", default=3) + 1))
                for n in want:
                    planned.append(("trial_run", t["slug"],
                                    {"tid": t["tid"], "model": m, "run": n, "fp": b.get("fingerprint", ""),
                                     "build_run": b.get("run_id"), "build_token": b.get("token"),
                                     "build_account": b.get("account")}, pr + 5))
    new = 0
    for kind, task, args, pr in planned:
        if not dry_run and enqueue(c, s, kind, task, args, pr):
            new += 1
    return planned, new


# ------------------------------------------------------------------ adaptive per-account limits
def account_limit(c, s, acct):
    r = c.execute("SELECT lim FROM limits WHERE account=?", (acct,)).fetchone()
    if r:
        return r["lim"]
    lim = s.get("adaptive", "initial", default=5)
    c.execute("INSERT OR IGNORE INTO limits(account,lim,changed_epoch) VALUES(?,?,0)", (acct, lim))
    return lim


def set_limit(c, acct, old, new, reason, now):
    c.execute("UPDATE limits SET lim=?, changed_epoch=? WHERE account=?", (new, now, acct))
    c.execute("INSERT INTO limit_log VALUES(?,?,?,?,?)", (utc(now), acct, old, new, reason))
    event(c, "limit.changed", acct, {"old": old, "new": new, "reason": reason}, dedup=f"limit|{acct}|{now}")


def adapt_limits(c, s, now=None, queued_work=True):
    """Lower to the running count when a run waits too long for a runner; raise one after a calm window.
    Lowering never stops a running job; it only admits fewer new ones."""
    now = now or time.time()
    a = {**{"min": 1, "max": 20, "queued_wait_min": 8, "raise_wait_min": 3, "raise_window_min": 30, "cooldown_min": 30},
         **(s.data.get("adaptive") or {})}
    for acct in [x["name"] for x in s.accounts()]:
        lim = account_limit(c, s, acct)
        changed = c.execute("SELECT changed_epoch FROM limits WHERE account=?", (acct,)).fetchone()["changed_epoch"]
        if now - changed < a["cooldown_min"] * 60:
            continue
        act = c.execute("SELECT * FROM jobs WHERE account=? AND state IN ('dispatched','running')", (acct,)).fetchall()
        running = sum(1 for j in act if j["gh_status"] == "in_progress")
        waiting_long = [j for j in act if (j["gh_status"] in (None, "queued", "pending", "waiting"))
                        and j["dispatched_at"] and now - epoch(j["dispatched_at"]) > a["queued_wait_min"] * 60]
        if waiting_long and lim > max(a["min"], running):
            set_limit(c, acct, lim, max(a["min"], running),
                      f"{len(waiting_long)} run(s) waited > {a['queued_wait_min']} min for a runner; {running} running", now)
            continue
        recent = c.execute("SELECT waited_sec FROM jobs WHERE account=? AND started IS NOT NULL AND started >= ?",
                           (acct, utc(now - a["raise_window_min"] * 60))).fetchall()
        calm = recent and all((r["waited_sec"] or 0) <= a["raise_wait_min"] * 60 for r in recent)
        if calm and len(act) >= lim and queued_work and lim < a["max"]:
            set_limit(c, acct, lim, lim + 1,
                      f"every run in the last {a['raise_window_min']} min got a runner within {a['raise_wait_min']} min; work waiting", now)


# ------------------------------------------------------------------ dispatch
def local_free_gb(path):
    return shutil.disk_usage(str(path)).free / 1024 ** 3


def effective_priority(s, j, now):
    return j["priority"] + s.get("dispatch", "aging_per_hour", default=1) * (now - epoch(j["queued_at"])) / 3600


def admission(c, s):
    if not s.get("dispatch", "enabled", default=True):
        return "dispatch is disabled in settings"
    if not s.accounts():
        return "no account is enabled (flip enabled=true in settings.toml for the accounts to use)"
    if not kv_get(c, "release.current"):
        return "no release is active (divq release build, then divq release activate)"
    root = s.p("results"); root = root if root.exists() else DIV
    free = local_free_gb(root)
    floor = s.get("dispatch", "local_disk_floor_gb", default=30)
    if free < floor:
        return f"local disk {free:.0f} GB is below the {floor} GB floor"
    return None


def running_on(c, acct):
    return c.execute("SELECT COUNT(*) n FROM jobs WHERE account=? AND state IN ('dispatched','running')", (acct,)).fetchone()["n"]


def pick_account(c, s, job):
    """A trial goes to the account that built the task (it pulls that build's artifact inside its own repo).
    A build goes to the enabled account with the most free slots."""
    if job["kind"] == "trial_run":
        ba = json.loads(job["args"]).get("build_account")
        names = [a["name"] for a in s.accounts()]
        if ba in names and running_on(c, ba) < account_limit(c, s, ba):
            return ba
        return None
    best, free = None, 0
    for a in s.accounts():
        slots = account_limit(c, s, a["name"]) - running_on(c, a["name"])
        if slots > free:
            best, free = a["name"], slots
    return best


def dispatch_once(c, s, ex, now=None, dry_run=False, max_new=None):
    now = now or time.time()
    why = admission(c, s)
    if why:
        return [], why
    started = []
    queued = sorted(c.execute("SELECT * FROM jobs WHERE state='queued'").fetchall(),
                    key=lambda j: -effective_priority(s, j, now))
    for j in queued:
        if max_new is not None and len(started) >= max_new:
            break
        cap = s.get("limits", "max_running", j["kind"], default=50)
        if c.execute("SELECT COUNT(*) n FROM jobs WHERE kind=? AND state IN ('dispatched','running')",
                     (j["kind"],)).fetchone()["n"] >= cap:
            continue
        acct = pick_account(c, s, j)
        if not acct:
            continue
        last = kv_get(c, f"last_dispatch|{acct}")
        if last and now - float(last) < s.get("dispatch", "spacing_sec", default=10):
            continue
        release = j["release"] or kv_get(c, "release.current")       # a retry keeps the release it first ran on
        token = f"j{j['id']}-a{j['attempts'] + 1}"
        args = json.loads(j["args"])
        inputs = {"job": token, "release": release, "tid": args["tid"],
                  "retention": str(s.get("dispatch", "artifact_retention_days", default=7))}
        if j["kind"] == "trial_run":
            inputs.update({"model": args["model"], "run": str(args["run"]),
                           "build_run": str(args.get("build_run") or ""), "build_token": args.get("build_token") or ""})
        if dry_run:
            started.append((j["id"], acct, token)); continue
        run_id = ex.dispatch(acct, WORKFLOW[j["kind"]], inputs)
        c.execute("UPDATE jobs SET state='dispatched', attempts=attempts+1, account=?, run_id=?, token=?, release=?, "
                  "settings_hash=?, dispatched_at=?, gh_status='queued' WHERE id=?",
                  (acct, str(run_id) if run_id else None, token, release, s.hash, utc(now), j["id"]))
        kv_set(c, f"last_dispatch|{acct}", now)
        started.append((j["id"], acct, token))
    return started, None


# ------------------------------------------------------------------ poll, fetch, close
def _fetch_and_decrypt(s, ex, j, args):
    """Download the job's artifact, decrypt into out/results/<slug>/{build|trials}/<token>/. Returns the dir or None."""
    import tarfile, tempfile, subprocess
    slug = j["task"]
    sub = "build" if j["kind"] == "build" else "trials"
    dest = s.p("results") / slug / sub / j["token"]
    if (dest / "divq-result.json").is_file():
        return dest                                   # already have it (idempotent)
    name = j["token"]
    attempts = s.get("dispatch", "fetch_attempts", default=5)
    backoff = s.get("dispatch", "fetch_backoff_sec", default=15)
    key_file = str(s.p("key_file"))
    for a in range(1, attempts + 1):
        with tempfile.TemporaryDirectory() as td:
            blob = ex.download_artifact(j["account"], j["run_id"], name, td)
            if blob and os.path.exists(blob):
                dest.mkdir(parents=True, exist_ok=True)
                dec = Path(td) / "out.tgz"
                r = subprocess.run(["gpg", "--batch", "--quiet", "--pinentry-mode", "loopback",
                                    "--passphrase-file", key_file, "-o", str(dec), "-d", blob], capture_output=True)
                if r.returncode == 0:
                    try:
                        with tarfile.open(dec) as tf:
                            tf.extractall(dest, filter="data")
                        if (dest / "divq-result.json").is_file():
                            return dest
                    except (tarfile.TarError, OSError):
                        pass
        time.sleep(backoff * a)
    return None


def run_checks(s, j, res_dir):
    """Post-condition checks. Each: (name, ok, detail, needs_person)."""
    out = []
    dr = res_dir / "divq-result.json"
    if not dr.is_file():
        return [("artifact", False, "no divq-result.json in the artifact", False)]
    r = json.loads(dr.read_text())
    if j["kind"] == "build":
        ok = r.get("status") in ("sound", "unsound", "gate_error", "build_incomplete")
        out.append(("gate_marker", ok, f"status={r.get('status')}", False))
    else:
        graded = r.get("graded")
        out.append(("run_result", graded or r.get("infra_reason") is not None,
                    f"graded={graded} reward={r.get('reward')} infra={r.get('infra_reason')}", False))
    return out


def poll_once(c, s, ex, now=None):
    """Advance every active job: follow its run, and on completion fetch + decrypt + check + close it."""
    now = now or time.time()
    closed = []
    for j in c.execute("SELECT * FROM jobs WHERE state IN ('dispatched','running')").fetchall():
        args = json.loads(j["args"])
        rid = j["run_id"]
        if not rid:
            rid = ex.find_run(j["account"], WORKFLOW[j["kind"]], j["token"])
            if rid:
                c.execute("UPDATE jobs SET run_id=? WHERE id=?", (str(rid), j["id"]))
            else:
                continue
        st = ex.run_status(j["account"], rid)        # (status, conclusion, started_at|None)
        status, conclusion, started_at = st
        if status == "in_progress" and j["gh_status"] != "in_progress":
            waited = (epoch(started_at) - epoch(j["dispatched_at"])) if (started_at and j["dispatched_at"]) else None
            c.execute("UPDATE jobs SET state='running', gh_status='in_progress', started=?, waited_sec=? WHERE id=?",
                      (started_at or utc(now), waited, j["id"]))
            continue
        if status != "completed":
            c.execute("UPDATE jobs SET gh_status=? WHERE id=?", (status, j["id"]))
            continue
        # the run finished: pull the result the task actually produced
        res_dir = _fetch_and_decrypt(s, ex, j, args)
        if res_dir is None:
            _fail_or_retry(c, s, j, "artifact not fetched/decrypted", now)
            closed.append((j["id"], "fetch-failed")); continue
        checks = run_checks(s, j, res_dir)
        bad = [x for x in checks if not x[1]]
        r = json.loads((res_dir / "divq-result.json").read_text())
        if bad:
            _fail_or_retry(c, s, j, "; ".join(f"{n}: {d}" for n, _, d, _ in bad), now, checks)
            closed.append((j["id"], "check-failed")); continue
        c.execute("UPDATE jobs SET state='done', gh_status='completed', finished=?, result=?, checks=? WHERE id=?",
                  (utc(now), (r.get("status") or r.get("summary") or "")[:300], canon(checks), j["id"]))
        event(c, "job.done", j["task"], {"kind": j["kind"], "token": j["token"], "result": r.get("status") or r.get("summary")})
        closed.append((j["id"], "done"))
    return closed


def _fail_or_retry(c, s, j, why, now, checks=None):
    if j["attempts"] < j["max_attempts"]:
        c.execute("UPDATE jobs SET state='queued', account=NULL, run_id=NULL, token=NULL, gh_status=NULL, "
                  "dispatched_at=NULL, result=? WHERE id=?", (f"retry: {why}"[:300], j["id"]))
    else:
        c.execute("UPDATE jobs SET state='blocked', finished=?, result=?, checks=? WHERE id=?",
                  (utc(now), f"blocked after {j['attempts']} attempts: {why}"[:300], canon(checks or []), j["id"]))
        event(c, "job.blocked", j["task"], {"kind": j["kind"], "why": why})


def status_counts(c):
    rows = c.execute("SELECT kind, state, COUNT(*) n FROM jobs GROUP BY kind, state").fetchall()
    out = {}
    for r in rows:
        out.setdefault(r["kind"], {})[r["state"]] = r["n"]
    return out
