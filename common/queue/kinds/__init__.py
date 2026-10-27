"""Job kinds as plug-ins: one declaration per kind.

Each file in this folder declares one kind and registers it; folders named in queue.toml `[kinds] extra_dirs` (or the
CWEQ_KINDS_DIRS environment variable, ':'-separated) are loaded the same way. A new stage is a new file:

    from kinds import Kind, register

    def command(row, cfg):                 # argv of the existing script the worker runs (cwd = the repo root)
        return ["bash", "pipelines/x/run.sh", row["task"]]

    def check(task, args, t0, cfg):        # post-condition checks: [(name, ok, detail, needs_person)]
        ...

    def plan(conn, cfg, ctx, states, dry_run=False):   # optional: the jobs this kind wants, each reconcile pass
        ...

    register(Kind(name="x", command=command, check=check, plan=plan, priority=20, max_running=2,
                  reads=("tasks/<slug>/",), writes=("build/<slug>/x.json",)))

A declaration states what the queue needs to run the kind:
  command        (row, cfg) -> argv. None: the kind has no worker and never starts (gate).
  check          (task, args, t0, cfg) -> list of (name, ok, detail, needs_person); None: the exit code decides
                 (checks.py runs it after an ok exit; docs/RULES.md lists every check).
  plan           (conn, cfg, ctx, states, dry_run) -> list of reconcile reports; run at the end of each reconcile pass.
                 The built-in kinds are planned by reconcile.py, phase3.py, phase4.py, delivery.py and lintstep.py.
  reads, writes  the files the kind reads and writes (documentation; docs/WORK-QUEUE.md).
  light          bookkeeping: outside the total cap and the machine limits, no task slot, no start spacing.
  exclusive      runs alone on its task (no other job of the task at the same time).
  foreign        the taskstate process kind of the same work started outside the queue; counted against the caps
                 when count_foreign is set.
  priority, max_running, max_attempts, retry_exit_codes, ok_exit_codes, env, disk_floor
                 defaults; queue.toml overrides every one of them ([priority], [limits.max_running], ...).

config.load() merges the declared defaults under the TOML file, so the settings file stays the one source of the
values in force.
"""
import importlib
import importlib.util
import os
import pkgutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
QUEUE = HERE.parent
for _p in (str(QUEUE), str(QUEUE.parent)):          # common/queue and common/ (paths.py) for the kind files
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass
class Kind:
    name: str
    command: Optional[Callable] = None
    check: Optional[Callable] = None
    plan: Optional[Callable] = None
    reads: tuple = ()
    writes: tuple = ()
    light: bool = False
    exclusive: bool = False
    foreign: Optional[str] = None
    count_foreign: bool = False
    priority: Optional[int] = None
    max_running: Optional[int] = None
    max_attempts: Optional[int] = None
    retry_exit_codes: tuple = ()
    ok_exit_codes: tuple = ()
    env: dict = field(default_factory=dict)
    disk_floor: Optional[str] = None
    doc: str = ""
    source: str = ""                                  # the file that declared it


REGISTRY = {}
_loaded_files = set()
_builtins_loaded = False


def register(kind):
    """Add (or replace) a kind. Returns it, so a file can keep a reference."""
    if not kind.source:
        f = sys._getframe(1).f_globals.get("__file__", "")
        kind.source = str(Path(f).resolve()) if f else ""
    REGISTRY[kind.name] = kind
    return kind


def load_builtins():
    """Import every declaration in this folder (once)."""
    global _builtins_loaded
    if _builtins_loaded:
        return
    for m in sorted(pkgutil.iter_modules([str(HERE)]), key=lambda m: m.name):
        if not m.name.startswith("_"):
            importlib.import_module(f"kinds.{m.name}")
    _builtins_loaded = True


def load_dirs(dirs):
    """Load the *.py declarations in extra folders (once per file). Returns the names now registered."""
    for d in dirs or ():
        d = Path(os.path.expanduser(str(d)))
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            f = f.resolve()
            if f.name.startswith("_") or f in _loaded_files:
                continue
            spec = importlib.util.spec_from_file_location(f"cweq_kind_{abs(hash(str(f)))}_{f.stem}", f)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            _loaded_files.add(f)
    return names()


def load(extra_dirs=()):
    load_builtins()
    env = os.environ.get("CWEQ_KINDS_DIRS", "")
    load_dirs([*(extra_dirs or ()), *[x for x in env.split(":") if x]])
    return REGISTRY


def get(name):
    load_builtins()
    return REGISTRY.get(name)


def names():
    load_builtins()
    return tuple(REGISTRY)


def exclusive():
    load_builtins()
    return {k.name for k in REGISTRY.values() if k.exclusive}


def light():
    load_builtins()
    return {k.name for k in REGISTRY.values() if k.light}


def foreign_map():
    """taskstate process kind -> job kind (work started outside the queue that counts as this kind)."""
    load_builtins()
    return {k.foreign: k.name for k in REGISTRY.values() if k.foreign}


def planners():
    load_builtins()
    return [k for k in REGISTRY.values() if k.plan]


def defaults():
    """The declared defaults, shaped like the settings file (config.load merges the TOML file over them)."""
    load_builtins()
    out = {"priority": {}, "max_attempts": {}, "retry_exit_codes": {}, "ok_exit_codes": {}, "env": {},
           "limits": {"max_running": {}, "disk_floor": {}},
           "dispatch": {"light_kinds": [], "count_foreign": []}}
    for k in REGISTRY.values():
        if k.priority is not None:
            out["priority"][k.name] = k.priority
        if k.max_attempts is not None:
            out["max_attempts"][k.name] = k.max_attempts
        if k.max_running is not None and k.command is not None:
            out["limits"]["max_running"][k.name] = k.max_running
        if k.disk_floor:
            out["limits"]["disk_floor"][k.name] = k.disk_floor
        if k.retry_exit_codes:
            out["retry_exit_codes"][k.name] = list(k.retry_exit_codes)
        if k.ok_exit_codes:
            out["ok_exit_codes"][k.name] = list(k.ok_exit_codes)
        if k.env:
            out["env"][k.name] = dict(k.env)
        if k.light:
            out["dispatch"]["light_kinds"].append(k.name)
        if k.count_foreign:
            out["dispatch"]["count_foreign"].append(k.name)
    return out


# ---------- helpers for declarations

def trial_dir(cfg, args):
    """The trial folder a job's args name ({"trial": "<job>/<trial>"}), as a path string ('' when none)."""
    from pathlib import Path as _P
    return str(_P(cfg["jobs_dir"]) / args["trial"]) if args.get("trial") else ""


def check_from(name, **kw):
    """A check that calls checks.<name>(task, args, t0, cfg, **kw) (imported when the check runs)."""
    def fn(task, args, t0, cfg):
        import checks
        return getattr(checks, name)(task, args, t0, cfg, **kw)
    fn.__name__ = f"checks.{name}"
    return fn


def command_from(module, func="command"):
    """A command that calls <module>.<func>(row, cfg) (imported when the job starts)."""
    def fn(row, cfg):
        return getattr(importlib.import_module(module), func)(row, cfg)
    fn.__name__ = f"{module}.{func}"
    return fn


def enqueue(conn, cfg, kind, task, args, dry_run=False, depends_on=(), origin="reconciler"):
    """Queue one job of a kind with its settings' priority and attempts (for plan functions). Returns the job id, or
    None in a dry run."""
    import qdb
    if dry_run:
        return None
    jid, _ = qdb.enqueue(conn, kind, task, args, priority=cfg["priority"].get(kind, 0),
                         max_attempts=cfg["max_attempts"].get(kind, 1), depends_on=depends_on, origin=origin)
    return jid
