"""Where one task stands, read from the files on disk and the process table. Nothing here writes anything.

This is the one reader the work queue uses to adopt the running pipeline (adopt.py) and to refuse work that is
already done (redo_reason). It reuses the readers the current pipeline relies on, so the two can never disagree:

    build finished?      the same rules as pipelines/router/scale_queue.py build_done()
    gate                 build/<slug>/ markers (.sound .unsound .gate_error .listing_fail .gate_passed) and the
                         gate fingerprint (common/gate/fingerprint.py: a SOUND gate on older files is stale)
    trials (launching)   common/trial/trial_state.py state(): none / incomplete / stuck / solved / failed
    verdicts (audited)   build/audit/ledger.md, written by common/audit/audit_results.py from the raw trial folders
    fairness, decision   common/fairness/fairness_verdict.py (FAIRNESS.md, HUMAN-DECISION.md)
    delivery             build/audit/delivered.tsv (the delivery register: slug, delivered name, client commit),
                         or a DELIVERED line in build/<slug>/HUMAN-DECISION.md
    running work         command lines of build, gate, re-gate, trial, fairness and repair processes

stage = the furthest point the task has reached; next = the one step that would move it on, or a reason it waits.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402
for sub in ("gate", "trial", "fairness"):
    sys.path.insert(0, str(paths.COMMON / sub))
import fairness_verdict  # noqa: E402
import fingerprint  # noqa: E402
import trial_state  # noqa: E402

MODELS = ("deepseek", "mimo")
LEDGER_MODEL_COL = {"deepseek": 3, "mimo": 4}          # | Track | Task | DeepSeek | MiMo | Verdict |
DELIVERED = re.compile(r"(?mi)^\s*DELIVERED\s*:\s*(.+)$")

# Stages, in pipeline order. A task is in exactly one.
STAGES = (
    "outside_batches",    # built before the scale batches (older markers), no verdict in the ledger: never scheduled
    "waiting_build",      # listed in a batch, no build started
    "building",           # a build process is running
    "build_interrupted",  # a build started, did not end, and nothing is running it
    "build_stopped",      # the build ended without a gate verdict (STOP, BUILD-INCOMPLETE, a builder decline)
    "gate_failed",        # .unsound / .gate_error: no trials
    "listing_fail",       # held at the listing check (stacking): a person decides
    "regating",           # a re-gate (or repair script) is running
    "held_repair",        # .hold-repair: a test repair is between its edit and its regrades
    "stale_gate",         # SOUND, but the files changed since: needs a re-gate before any trial
    "trialing",           # SOUND, at least one model's trials are running
    "waiting_trials",     # SOUND, a model still needs runs and none are running
    "trials_stuck",       # trial_state says stuck: a person looks
    "not_breaker",        # every model has a verdict and at least one solved: finished
    "awaiting_audit",     # both models failed; failing runs wait for their audit
    "awaiting_fairness",  # both failed and audited; no fairness verdict yet
    "fairness_not_ready", # fairness review NOT_READY: a person decides (repair or drop)
    "awaiting_decision",  # fairness READY: the owner records KEEP / REPAIR / DROP
    "kept",               # owner KEEP, not delivered yet
    "dropped",            # owner DROP (or REPAIR not yet started)
    "delivered",          # in the client repository
)
REDO_CHECKED = ("build", "gate", "trial_run")
FINISHED = ("outside_batches", "gate_failed", "build_stopped", "not_breaker", "dropped", "delivered")


def _read(p):
    try:
        return Path(p).read_text(errors="replace")
    except OSError:
        return ""


# ---------- inputs shared by every task (read once per pass)

def batches():
    """{slug: batch name} from pipelines/router/out/batches/*.txt (first batch wins)."""
    out = {}
    for f in sorted((paths.PIPELINES / "router" / "out" / "batches").glob("*.txt")):
        for line in _read(f).splitlines():
            s = line.split("#")[0].strip()
            if s:
                out.setdefault(s, f.stem)
    return out


def ledger():
    """{slug: {"track", "deepseek", "mimo", "verdict"}} from the 'All tasks' table of build/audit/ledger.md."""
    out, on = {}, False
    for line in _read(paths.BUILD / "audit" / "ledger.md").splitlines():
        if line.startswith("## "):
            on = line.strip() == "## All tasks"
            continue
        cells = [c.strip() for c in line.split("|")]
        if not on or len(cells) < 7 or cells[2] in ("Task", "---", ""):
            continue
        out[cells[2]] = {"track": cells[1], "deepseek": cells[3], "mimo": cells[4], "verdict": cells[5].strip("*")}
    return out


def ledger_model(cell):
    """A ledger cell -> solved | failed | partial | none (no graded run) | '' (not in the ledger)."""
    if not cell:
        return ""
    c = cell.lstrip("*").lower()
    if c.startswith("solved"):
        return "solved"
    if c.startswith("failed"):
        return "failed"
    if c.startswith("no graded run"):
        return "none"
    return "partial"                                   # "0/2 so far, needs 3"


def awaiting_audit(cell):
    m = re.search(r"\+(\d+) awaiting audit", cell or "")
    return int(m.group(1)) if m else 0


PROC_RULES = (   # (kind, regex over the joined command line; group 1 = slug, optional group 2 = model)
    ("build", re.compile(r"run_stack_pipeline\.sh (\S+)$")),
    ("build", re.compile(r"run_pipeline\.sh \S+ (\S+)$")),
    ("regate", re.compile(r"regate\.sh (\S+)(?: |$)")),
    ("trial", re.compile(r"trial\.py (\S+) --models (\w+)")),
    ("fairness", re.compile(r"run_fairness(?:_stack)?\.sh (\S+)(?: |$)")),
)


def running(proc_list, ignore_own=False):
    """{slug: [(kind, model or '', pid), ...]} for the pipeline processes running now (one entry per process).
    A repair script (pipelines/router/out/queue/*-repair.sh) is matched by the slug it sets (S=<slug>).
    ignore_own: leave out the queue's own workers and their children (CWEQ_JOB in the environment), so only the old
    scripts' work is counted."""
    out = {}
    for pid, argv, cwd, env in proc_list:
        if ignore_own and (env or {}).get("CWEQ_JOB"):
            continue
        cmd = " ".join(argv)
        if "taskstate" in cmd or "cweq" in cmd:
            continue
        for kind, rx in PROC_RULES:
            m = rx.search(cmd)
            if m:
                out.setdefault(m.group(1), []).append((kind, m.group(2) if rx.groups > 1 else "", pid))
                break
        else:
            m = re.search(r"(\S+-(?:repair|followup)\.sh)\b", cmd)
            if m and len(argv) >= 2 and argv[0].endswith("bash"):
                p = Path(m.group(1)) if Path(m.group(1)).is_absolute() else Path(cwd or paths.ROOT) / m.group(1)
                s = re.search(r"(?m)^\s*S=([A-Za-z0-9._-]+)", _read(p))
                if s:
                    out.setdefault(s.group(1), []).append(("repair", "", pid))
    return out


def deliveries():
    """{slug: "delivered_as client_commit date"} from build/audit/delivered.tsv (# lines are comments)."""
    out = {}
    for line in _read(paths.BUILD / "audit" / "delivered.tsv").splitlines():
        cells = line.split("\t")
        if line.startswith("#") or len(cells) < 2 or not cells[0].strip():
            continue
        out[cells[0].strip()] = " ".join(c.strip() for c in cells[1:] if c.strip())
    return out


def context(proc_list, ignore_own=False):
    return {"batches": batches(), "ledger": ledger(), "running": running(proc_list, ignore_own),
            "delivered": deliveries()}


def gate_sha16(slug):
    """First 16 hex of the sha256 the last SOUND gate recorded (the task version trials belong to), or 'legacy'."""
    try:
        return json.loads((paths.BUILD / slug / "gate_fingerprint.json").read_text()).get("sha256", "")[:16] or "legacy"
    except (OSError, ValueError):
        return "legacy"


# ---------- one task

def build_done(b):
    """scale_queue.py build_done(): True when the slug needs no (more) build work."""
    if any((b / m).is_file() for m in (".sound", ".listing_fail", ".hold-repair", ".gate_passed")):
        return True
    end, start = b / "end_utc.txt", b / "start_utc.txt"
    if end.is_file() and (not start.is_file() or _read(end).strip() >= _read(start).strip()):
        return True
    if any((b / m).is_file() for m in (".unsound", ".gate_error")):
        return True
    for logf in ("stack_pipeline.log", "pipeline.log"):
        t = _read(b / logf)
        if "STOP:" in t or "BUILD-INCOMPLETE" in t or "stopped/failed" in t:
            return True
    return False


def build_started(b):
    return any((b / f).exists() for f in ("start_utc.txt", "stack_pipeline.log", "pipeline.log", "manifest.json"))


def fp_state(slug):
    """current | stale | missing (gated before fingerprints existed: treated as current, as the scheduler does)."""
    rec = paths.BUILD / slug / "gate_fingerprint.json"
    if not rec.is_file():
        return "missing"
    try:
        return "current" if json.loads(rec.read_text()).get("sha256") == fingerprint.digest(slug)[0] else "stale"
    except (OSError, ValueError, Exception):           # an unreadable task tree counts as changed
        return "stale"


def read(slug, ctx):
    """Everything known about one task, and its stage and next step."""
    b = paths.BUILD / slug
    run = ctx["running"].get(slug, [])
    kinds = {k for k, _m, _p in run}
    led = ctx["ledger"].get(slug, {})
    t = {"task": slug, "batch": ctx["batches"].get(slug, ""), "pipeline": "stacking" if slug.startswith("stk-")
         else "sibling", "markers": sorted(m for m in (".sound", ".unsound", ".gate_error", ".listing_fail",
                                                         ".gate_passed", ".hold-repair") if (b / m).exists()),
         "running": [f"{k}{':' + m if m else ''} pid {p}" for k, m, p in run], "models": {},
         "ledger_verdict": led.get("verdict", ""), "fairness": "", "decision": "", "delivered": "", "notes": []}

    hd = fairness_verdict.human_decision(slug)
    dec_text = _read(b / "HUMAN-DECISION.md")
    if hd:
        t["decision"] = f"{hd[0]} {hd[1]}" + (" (stale)" if hd[2] else "")
    d = DELIVERED.search(dec_text)
    if d:
        t["delivered"] = d.group(1).strip()
    elif slug in ctx.get("delivered", {}):
        t["delivered"] = "register: " + ctx["delivered"][slug]
    if (b / "FAIRNESS.md").exists() or (b / "fairness_status.txt").exists():
        v, why = fairness_verdict.final(slug)
        t["fairness"] = f"{v}: {why}"

    for m in MODELS:
        s, graded, ungraded = trial_state.state(slug, m)
        t["models"][m] = {"launch": s, "graded": len(graded), "ungraded": ungraded,
                          "running": sum(1 for k, mm, _p in run if k == "trial" and mm == m),
                          "ledger": ledger_model(led.get(m, "")), "awaiting_audit": awaiting_audit(led.get(m, ""))}

    def done(stage, nxt):
        t["stage"], t["next"] = stage, nxt
        return t

    # Decisions and delivery first: they are final whatever the files below say.
    if t["delivered"]:
        return done("delivered", "nothing")
    if hd and not hd[2]:
        if hd[0] == "KEEP":
            return done("kept", "deliver (after the owner's KEEP)")
        return done("dropped", "nothing" if hd[0] == "DROP" else "repair by a person (decision REPAIR)")

    if "build" in kinds:
        return done("building", "wait: build running")
    # Outside the batch files with no SOUND marker: a task from before the scale run (other markers). The queue never
    # builds or gates it; the audited ledger, when it has the task, says where it stands.
    if not t["batch"] and ".sound" not in t["markers"] and not kinds:
        if slug in ctx["ledger"]:
            ms = t["models"]
            final = {m: ms[m]["ledger"] if ms[m]["ledger"] in ("solved", "failed") else "" for m in MODELS}
            if all(final.values()) or "solved" in final.values():       # one solve already rules a breaker out
                return verdict_stage(t, final, kinds, done)
            return done("outside_batches", "nothing: no verdict for " + ", ".join(m for m in MODELS if not final[m])
                        + " and not in a batch (a person adds it to a batch to schedule it)")
        return done("outside_batches", "nothing: not in a batch (a person adds it to a batch to schedule it)")
    if not build_started(b) and not t["markers"]:
        return done("waiting_build", "build" if t["batch"] else "nothing: not in any batch")
    if not build_done(b):
        return done("build_interrupted", "build (restart: the last build never ended)")
    if "regate" in kinds or "repair" in kinds:
        return done("regating", "wait: re-gate or repair running")
    if ".hold-repair" in t["markers"]:
        return done("held_repair", "wait: test repair in progress (re-gate, then regrade)")
    if ".listing_fail" in t["markers"] and ".sound" not in t["markers"]:
        return done("listing_fail", "a person decides (listing check)")
    if ".sound" not in t["markers"]:
        if ".unsound" in t["markers"] or ".gate_error" in t["markers"]:
            return done("gate_failed", "nothing")
        if ".gate_passed" in t["markers"]:
            return done("stale_gate", "regate (the last re-gate stopped before its result)")
        return done("build_stopped", "nothing")
    t["fp"] = fp_state(slug)
    if t["fp"] == "stale":
        return done("stale_gate", "regate (files changed since the SOUND gate)")

    ms = t["models"]
    # Verdict per model: the audited ledger when it has one, else the launch state.
    final = {m: (ms[m]["ledger"] if ms[m]["ledger"] in ("solved", "failed") else
                 ms[m]["launch"] if ms[m]["launch"] in ("solved", "failed") else "") for m in MODELS}
    if any(ms[m]["running"] for m in MODELS):
        return done("trialing", "wait: trials running (" +
                    ", ".join(f"{m} {ms[m]['running']}" for m in MODELS if ms[m]["running"]) + ")")
    if any(ms[m]["launch"] == "stuck" and not final[m] for m in MODELS):
        return done("trials_stuck", "a person looks (runs keep producing no result)")
    todo = [m for m in MODELS if not final[m]]
    if todo:
        return done("waiting_trials", "trial " + ", ".join(todo))
    return verdict_stage(t, final, kinds, done)


def verdict_stage(t, final, kinds, done):
    """Stage of a task whose models all have a verdict: finished, or a breaker on its way to the owner."""
    ms = t["models"]
    if any(final[m] == "solved" for m in MODELS):
        return done("not_breaker", "nothing")
    if any(ms[m]["awaiting_audit"] for m in MODELS) or "BREAKER" not in t["ledger_verdict"]:
        return done("awaiting_audit", "audit the failing runs")
    if "fairness" in kinds:
        return done("awaiting_fairness", "wait: fairness review running")
    if not t["fairness"] or t["fairness"].startswith("ERROR"):
        return done("awaiting_fairness", "fairness review")
    if t["fairness"].startswith("NOT_READY"):
        return done("fairness_not_ready", "a person decides (repair or drop)")
    return done("awaiting_decision", "owner records KEEP / REPAIR / DROP")


def slugs(ctx):
    """Every task the pipeline knows: batch entries, ledger rows, and task packages that have a build record."""
    s = set(ctx["batches"]) | set(ctx["ledger"])
    if paths.TASKS.is_dir():
        s |= {p.name for p in paths.TASKS.iterdir() if p.is_dir() and (paths.BUILD / p.name).is_dir()}
    return sorted(s)


# ---------- the never-redo rule

def redo_reason(kind, slug, args, ctx=None, t=None):
    """Why queuing (kind, slug, args) would repeat finished work, or None when it would not.
    build: the build already ran or is running. gate: the task is SOUND on its current files. trial_run: the model
    already has a verdict, or its runs are running. Re-gates, regrades and rescores are allowed: the reconciler only
    asks for them when the files changed after the last result (reconcile.py rules R1, R2)."""
    if kind not in REDO_CHECKED:
        return None
    if t is None:
        ctx = ctx or context([])
        t = read(slug, ctx)
    b = paths.BUILD / slug
    if kind == "build":
        if t["stage"] == "building":
            return "a build is running"
        if t["stage"] == "outside_batches":
            return "a task from before the scale batches; add it to a batch file first"
        if build_started(b) and build_done(b):
            return f"the build already ran (stage {t['stage']})"
        return None
    if kind == "gate":
        if ".sound" in t["markers"] and t.get("fp", fp_state(slug)) != "stale":
            return "SOUND on the current files"
        return None
    m = (args or {}).get("model")
    if t["stage"] in ("not_breaker", "awaiting_audit", "awaiting_fairness", "fairness_not_ready",
                      "awaiting_decision", "kept", "dropped", "delivered"):
        return f"trials are over (stage {t['stage']})"
    if m in t["models"]:
        mm = t["models"][m]
        if mm["running"]:
            return f"{m} trials are running"
        if mm["ledger"] in ("solved", "failed") or mm["launch"] in ("solved", "failed"):
            return f"{m} already has a verdict ({mm['ledger'] or mm['launch']})"
    return None
