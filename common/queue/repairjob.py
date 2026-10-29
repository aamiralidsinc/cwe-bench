#!/usr/bin/env python3
"""The repair job (kinds/repair.py): one audit-driven, test-only repair of one task, done by DeepSeek.

    common/launch/drive.sh deepseek python3 -I common/queue/repairjob.py <slug> [--job ID] [--config FILE]
                                                                         [--finding JSON]

The fairfix step as a queue job (history: common/queue/repairstep.py and docs/WORK-QUEUE.md). The hold protocol is
code here, never the agent's:
  1. the finding: the task's current one (repairstep.findings), or the owner's own (--finding with text or a JSON
     object: a manual enqueue). A reconciler key that no longer matches -> exit 4, nothing touched.
  2. the hold: .sound -> .hold-repair (or a new .hold-repair), with a text naming the job.
  3. wait until no other work of the task runs (trials, re-gates, regrades, builds, reviews: queue jobs and old
     scripts, read from the process table, never by pgrep). After [repair] wait_sec the hold goes back as it was
     -> exit 75 (blocked for a person: max_attempts 1, a repair is never restarted on its own).
  4. build/<slug>/trial_summary.md (common/trial/trial_summary.py, the input the owner gave the hardening step),
     then the inputs folder build/<slug>/repair-inputs-<UTC>/: FINDING.md / FINDING.json, runs/<run>/ (per-test
     results and failure messages of every graded run, its final diff, transcript excerpts) and INPUTS.md.
  5. a backup of everything the agent may touch (tests/, solution/, environment/, instruction.md, task.toml,
     manifest.json, checks/, notes.md) in the inputs folder.
  6. the agent: the fairfix script in repair mode (REPAIR_INPUTS=<folder>): pipelines/sibling/10-fairfix/
     run_fairfix.sh or pipelines/stacking/8-fairfix/run_fairfix_stack.sh, brief common/fairness/REPAIR-BRIEF.md.
  7. checks in code: the agent finished; instruction.md, task.toml and environment/ unchanged; the gated files
     changed; a new repaired-tests-* / removed-tests-* folder with README.md; a history/<date>-repair*.md written;
     the static gate stage still passes; notes.md edits reverted (history/ holds the record).
  8. ok: the changed test files touched, the hold kept (its text: waiting for the re-gate and regrades), the re-gate
     queued with the same key as reconcile rule R1 (so a task gated before fingerprints existed is re-gated too),
     JOB-RESULT.json -> exit 0. The reconciler then regrades every graded run (R2) and lifts the hold (R6).
     Not ok: the originals restored from the backup (root-owned leftovers removed through a container), the
     agent's repair folder moved to <inputs>/failed/, the hold kept with the reason, JOB-RESULT.json -> exit 1;
     exit 3 when the agent made no repair (OUTCOME.json says no_repair_needed or could_not_repair).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402
sys.path.insert(0, str(paths.COMMON / "gate"))
import fingerprint  # noqa: E402

import markers  # noqa: E402
import procs  # noqa: E402
import qdb  # noqa: E402
import repairstep  # noqa: E402

EXIT_REPAIRED, EXIT_FAILED, EXIT_NO_REPAIR, EXIT_NOTHING, EXIT_WAIT = 0, 1, 3, 4, 75
SCRIPTS = {"stk": "pipelines/stacking/8-fairfix/run_fairfix_stack.sh",
           "sibling": "pipelines/sibling/10-fairfix/run_fairfix.sh"}
BACKUP_DIRS = (("tests", "tasks"), ("solution", "tasks"), ("environment", "tasks"), ("checks", "build"))
BACKUP_FILES = (("instruction.md", "tasks"), ("task.toml", "tasks"), ("manifest.json", "build"), ("notes.md", "build"))
ENV_BACKUP_MAX = 200 << 20
PATCH_MAX = 400 << 10


def sha(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return ""


def utc_stamp():
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


class Stopped(Exception):
    """SIGTERM (cweq stop, a reaped lease): the job restores the task before it exits."""


def _stop(_sig, _frame):
    raise Stopped()


class Job:
    def __init__(self, slug, cfg, job_id=None, conn=None, proc_lister=None, out=print):
        self.slug, self.cfg, self.job_id = slug, cfg, job_id
        self.st = repairstep.settings(cfg)
        self.t, self.b = paths.TASKS / slug, paths.BUILD / slug
        self.conn = conn
        self.proc_lister = proc_lister or procs.list_processes
        self.out = out
        self.date = time.strftime("%Y%m%d", time.gmtime())
        self.log_file = self.b / f"repair-{self.date}.log"

    def log(self, text):
        line = f"{qdb.utc()} {text}"
        self.out(f"repairjob {self.slug}: {text}")
        try:
            with open(self.log_file, "a") as f:
                f.write(line + "\n")
        except OSError:
            pass

    # ------------------------------------------------------------ the hold
    def set_hold(self, text):
        b = self.b
        hold, sound = b / ".hold-repair", b / ".sound"
        if hold.exists():
            self.prev = (".hold-repair", markers.read_text(hold))
            if sound.exists():
                sound.unlink()
        elif sound.exists():
            os.replace(sound, hold)
            self.prev = (".sound", "")
        else:
            self.prev = (None, "")
        markers.write_atomic(hold, text + "\n")

    def hold_text(self, text):
        markers.write_atomic(self.b / ".hold-repair", text + "\n")

    def put_hold_back(self):
        kind, text = getattr(self, "prev", (None, ""))
        hold = self.b / ".hold-repair"
        if kind == ".sound":
            os.replace(hold, self.b / ".sound")
            (self.b / ".sound").write_text("")
        elif kind == ".hold-repair":
            markers.write_atomic(hold, text)
        elif hold.exists():
            hold.unlink()

    # ------------------------------------------------------------ waiting for the task's other work
    def others(self):
        """What else runs for the task: [(what, detail)]. Our own process and its children carry CWEQ_JOB."""
        import taskstate
        plist = [p for p in self.proc_lister() if p[0] != os.getpid()]
        out = [(k, f"pid {pid}") for k, _m, pid in taskstate.running(plist, ignore_own=True).get(self.slug, [])]
        for pid, cmd in procs.busy_tasks({self.slug}, self.cfg["busy"]["patterns"], plist,
                                         skip_dirs=(paths.COMMON,)).get(self.slug, []):
            out.append(("process", f"pid {pid} {cmd[:80]}"))
        if self.conn is not None:
            light = set(self.cfg["dispatch"].get("light_kinds", ()))
            for r in qdb.jobs(self.conn, "task=? AND state IN ('leased','running')", (self.slug,)):
                if str(r["id"]) != str(self.job_id) and r["kind"] not in light:
                    out.append((r["kind"], f"job #{r['id']}"))
        return out

    def wait_for_others(self, sleep=time.sleep):
        end = time.time() + float(self.st["wait_sec"])
        said = None
        while True:
            busy = self.others()
            if not busy:
                return True
            if said != busy:
                self.log("waiting for the task's other work: " + "; ".join(f"{k} {d}" for k, d in busy[:5]))
                said = busy
            if time.time() >= end:
                return False
            sleep(min(30.0, max(1.0, end - time.time())))

    # ------------------------------------------------------------ state, backup, restore
    def state(self):
        t, b = self.t, self.b
        env = self.t / "environment"
        return {"gate": fingerprint.digest(self.slug)[0], "tests": repairstep.tests_hash(self.slug),
                "instruction": sha(t / "instruction.md"), "task_toml": sha(t / "task.toml"),
                "environment": repairstep.cwe_reuse_tag.context_hash(env) if env.is_dir() else "",
                "notes": sha(b / "notes.md"),
                "folders": sorted(p.name for g in ("repaired-tests-*", "removed-tests-*") for p in b.glob(g))}

    def backup(self, dest):
        dest.mkdir(parents=True, exist_ok=True)
        skipped = []
        for name, where in BACKUP_DIRS:
            src = (self.t if where == "tasks" else self.b) / name
            if not src.is_dir():
                continue
            if name == "environment" and _size(src) > ENV_BACKUP_MAX:
                skipped.append(name)
                continue
            shutil.copytree(src, dest / name, symlinks=True)
        for name, where in BACKUP_FILES:
            src = (self.t if where == "tasks" else self.b) / name
            if src.is_file():
                shutil.copy2(src, dest / name)
        (dest / "BACKUP.json").write_text(json.dumps({"made_utc": qdb.utc(), "skipped": skipped}, indent=1))
        return skipped

    def rm_tree(self, p):
        try:
            shutil.rmtree(p)
            return
        except OSError:
            pass
        # Root-owned files (written by a container) cannot be removed by this user: remove them through a container.
        subprocess.run(["docker", "run", "--rm", "-v", f"{p.parent}:/x", self.st["cleanup_image"], "rm", "-rf",
                        f"/x/{p.name}"], capture_output=True, timeout=600)
        if p.exists():
            raise RuntimeError(f"cannot remove {p}")

    def restore(self, bk):
        for name, where in BACKUP_DIRS:
            live = (self.t if where == "tasks" else self.b) / name
            src = bk / name
            if name == "environment" and not src.exists():
                continue                                 # not backed up (too large) or absent: left as it is
            if live.exists() or live.is_symlink():
                self.rm_tree(live)
            if src.exists():
                shutil.copytree(src, live, symlinks=True)
        for name, where in BACKUP_FILES:
            live = (self.t if where == "tasks" else self.b) / name
            src = bk / name
            if src.is_file():
                shutil.copy2(src, live)
            elif live.exists():
                live.unlink()

    # ------------------------------------------------------------ the agent
    def agent_argv(self, inputs):
        cmd = self.st.get("agent_cmd") or []
        if cmd:
            return [str(x).format(slug=self.slug, inputs=str(inputs)) for x in cmd]
        return ["bash", SCRIPTS["stk" if self.slug.startswith("stk-") else "sibling"], self.slug]

    def run_agent(self, inputs, t0):
        env = dict(os.environ, REPAIR_INPUTS=str(inputs), REPAIR_DATE=self.date, REPAIR_JOB=str(self.job_id or "manual"),
                   FAIRFIX_TIMEOUT=str(int(self.st["timeout_sec"])))
        argv = self.agent_argv(inputs)
        self.log("agent: " + " ".join(argv))
        try:
            rc = subprocess.run(argv, cwd=str(paths.ROOT), env=env, stdin=subprocess.DEVNULL,
                                timeout=float(self.st["timeout_sec"]) + 900).returncode
        except subprocess.TimeoutExpired:
            rc = 124
        stf = self.b / "repair_status.txt"
        if stf.is_file() and (stf.stat().st_mtime >= t0 - 2):
            st = stf.read_text().strip() or f"exit {rc}"
        else:
            st = "ok" if rc == 0 else f"error: exit {rc}"
        return rc, st

    def static_ok(self):
        if not self.st["static_check"]:
            return True, "static check off"
        p = subprocess.run([sys.executable, "-I", "common/gate/gate.py", self.slug, "--only", "static", "--report",
                            "gate_report.partial.repair-static.json"], cwd=str(paths.ROOT), capture_output=True,
                           text=True, timeout=1800)
        tail = (p.stdout + p.stderr).strip().splitlines()[-1:] or [""]
        return p.returncode == 0, tail[0][:200]

    # ------------------------------------------------------------ the whole job
    def run(self, finding_arg=None, sleep=time.sleep):
        slug, b = self.slug, self.b
        if not self.t.is_dir() or not b.is_dir():
            self.out(f"repairjob {slug}: no tasks/{slug} or build/{slug}")
            return EXIT_NOTHING
        F = repairstep.findings(slug, self.cfg)
        manual = None
        if isinstance(finding_arg, str) and re.fullmatch(r"f-[0-9a-f]{16}", finding_arg or ""):
            if F["key"] != finding_arg:
                self.log(f"nothing to do: finding {finding_arg} is no longer the task's (now {F['key'] or 'none'}: "
                         f"covered by a repair, or a new audit changed it)")
                return EXIT_NOTHING
        elif finding_arg:
            manual = finding_arg
        if not F["items"] and not manual:
            self.log("nothing to do: no uncovered finding")
            return EXIT_NOTHING
        key = F["key"] if not manual else "m-" + hashlib.sha256(
            json.dumps([manual, F["key"]], sort_keys=True).encode()).hexdigest()[:16]
        t0 = time.time()
        main = threading.current_thread() is threading.main_thread()
        old_handler = signal.signal(signal.SIGTERM, _stop) if main else None
        try:
            return self._run(F, manual, key, t0, sleep)
        finally:
            if main:
                signal.signal(signal.SIGTERM, old_handler)

    def _run(self, F, manual, key, t0, sleep):
        slug, b = self.slug, self.b
        stamp = utc_stamp()
        inputs = b / f"repair-inputs-{stamp}"
        jid = self.job_id or "manual"
        self.set_hold(f"repair job #{jid} {qdb.utc()}: held for a test-only repair ({key}); set by the queue "
                      "(common/queue/repairjob.py) and lifted by the queue after the re-gate and the regrades")
        self.log(f"hold set ({self.prev[0] or 'no marker'} -> .hold-repair) for finding {key}: {F['why'] or manual}")
        try:
            if not self.wait_for_others(sleep):
                self.put_hold_back()
                self.log("the task's other work did not end in time: hold put back as it was, nothing changed (retried)")
                return EXIT_WAIT
        except Stopped:
            self.put_hold_back()
            self.log("stopped (SIGTERM) while waiting: hold put back as it was, nothing changed")
            return EXIT_FAILED
        try:                                             # nothing is changed yet: on any stop the hold goes back
            if self.st["trial_summary"]:                 # the runs' per-test results, as the hardening step got them
                subprocess.run([sys.executable, "-I", str(paths.COMMON / "trial" / "trial_summary.py"), slug],
                               cwd=str(paths.ROOT), capture_output=True, timeout=600)
            inputs.mkdir(parents=True)
            write_inputs(slug, inputs, F, manual, key, self.cfg)
            skipped = self.backup(inputs / "backup")
            pre = self.state()
            pre_static = self.static_ok()
        except BaseException as e:
            self.put_hold_back()
            self.log(f"stopped before the agent started ({type(e).__name__}: {e}): hold put back as it was, the task "
                     "is unchanged")
            return EXIT_FAILED
        self.log(f"inputs {inputs.name}; backup made{' (not backed up: ' + ', '.join(skipped) + ')' if skipped else ''}; "
                 f"gate {pre['gate'][:12]}, tests {pre['tests'][:12]}")
        try:
            return self.repair(inputs, pre, pre_static, key, t0)
        except BaseException as e:                       # stopped (SIGTERM) or a crash: never leave a half-edited task
            new = [n for n in self.state()["folders"] if n not in pre["folders"]]
            why = ("the job was stopped (SIGTERM) while the agent worked" if isinstance(e, Stopped)
                   else f"the repair job crashed: {type(e).__name__}: {e}")
            return self.fail(inputs, pre, [why], new, EXIT_FAILED, key)

    def repair(self, inputs, pre, pre_static, key, t0):
        """Steps 6-8: the agent, the checks in code, then success or the restore."""
        slug, b, jid = self.slug, self.b, self.job_id or "manual"
        rc, status = self.run_agent(inputs, t0)
        post = self.state()
        outcome = repairstep.jload(inputs / "OUTCOME.json") or {}
        problems = []
        if status != "ok":
            problems.append(f"agent did not finish: {status}")
        for k, what in (("instruction", "instruction.md"), ("task_toml", "task.toml"), ("environment", "environment/")):
            if post[k] != pre[k]:
                problems.append(f"{what} changed (a repair is test-only)")
        if post["notes"] != pre["notes"]:
            if (b / "notes.md").exists():
                shutil.copy2(b / "notes.md", inputs / "notes.md.agent-edit")
            if (inputs / "backup" / "notes.md").is_file():
                shutil.copy2(inputs / "backup" / "notes.md", b / "notes.md")
            self.log("notes.md edit reverted (kept as notes.md.agent-edit; the record belongs in history/)")
        new = [n for n in post["folders"] if n not in pre["folders"]]
        changed = post["gate"] != pre["gate"]
        no_repair = str(outcome.get("outcome", "")) in ("no_repair_needed", "could_not_repair")
        if not problems and no_repair and not changed:
            return self.fail(inputs, pre, [f"the agent made no repair: {outcome.get('outcome')}: "
                                           f"{str(outcome.get('reason', ''))[:300]}"], new, EXIT_NO_REPAIR, key)
        if not changed:
            problems.append("the agent changed no gated file (tests/, solution/, checks/, manifest patch_checks)")
        if not any((b / n / "README.md").is_file() for n in new):
            problems.append("no new repaired-tests-* / removed-tests-* folder with README.md")
        hist = [p for p in (b / "history").glob("*repair*.md") if p.stat().st_mtime >= t0 - 2] \
            if (b / "history").is_dir() else []
        if not hist:
            problems.append(f"no history/{self.date}-repair.md record")
        if not problems:
            ok, why = self.static_ok()
            if not ok and pre_static[0]:
                problems.append(f"the static gate stage fails after the repair: {why}")
        if problems:
            return self.fail(inputs, pre, problems, new, EXIT_FAILED, key)
        touched = touch_changed(self.t / "tests", inputs / "backup" / "tests")
        regate = None
        if self.conn is not None:
            listing = any(slug.startswith(p) for p in self.cfg["reconcile"]["listing_prefixes"])
            regate, _ = qdb.enqueue(self.conn, "regate", slug, {"fp": post["gate"][:16], "listing": listing},
                                    priority=self.cfg["priority"].get("regate", 50),
                                    max_attempts=self.cfg["max_attempts"].get("regate", 2), origin="reconciler")
        self.hold_text(f"repair job #{jid} done {qdb.utc()}: tests repaired ({new[-1]}); waiting for the re-gate"
                       f"{' #' + str(regate) if regate else ''} and the regrades of every graded run; the queue lifts "
                       "this hold (reconcile R6)")
        result = {"result": "repaired", "finding": key, "folder": new[-1], "folders": new, "history": [p.name for p in hist],
                  "gate_before": pre["gate"], "gate_after": post["gate"], "tests_before": pre["tests"],
                  "tests_after": post["tests"], "instruction_sha256": post["instruction"], "touched": touched,
                  "regate_job": regate, "agent_status": status, "agent_exit": rc, "outcome": outcome,
                  "job": self.job_id, "finished_utc": qdb.utc()}
        markers.write_atomic(inputs / "JOB-RESULT.json", json.dumps(result, indent=1) + "\n")
        self.log(f"repaired: {new[-1]}; {len(touched)} test file(s) touched; gate {pre['gate'][:12]} -> "
                 f"{post['gate'][:12]}; re-gate {'#' + str(regate) if regate else 'not queued (no queue database)'}; "
                 "hold kept until the re-gate is SOUND and every graded run is regraded")
        return EXIT_REPAIRED

    def fail(self, inputs, pre, problems, new, code, key):
        b = self.b
        moved = []
        for n in new:
            (inputs / "failed").mkdir(exist_ok=True)
            shutil.move(str(b / n), str(inputs / "failed" / n))
            moved.append(n)
        self.restore(inputs / "backup")
        back = self.state()
        same = back["gate"] == pre["gate"] and back["instruction"] == pre["instruction"]
        if not same:
            problems.append("RESTORE INCOMPLETE: the gated files differ from the backup")
        jid = self.job_id or "manual"
        self.hold_text(f"repair failed (job #{jid}, {qdb.utc()}): {'; '.join(problems)[:900]}; "
                       f"{'originals restored' if same else 'originals NOT fully restored'} from {inputs.name}/backup; "
                       f"a person decides: `cweq retry {jid}` runs the repair again, or rename .hold-repair to .sound "
                       "to release the task")
        result = {"result": "no_repair" if code == EXIT_NO_REPAIR else "failed", "finding": key, "problems": problems,
                  "moved_to_failed": moved, "restored": same, "gate_before": pre["gate"], "job": self.job_id,
                  "finished_utc": qdb.utc()}
        markers.write_atomic(inputs / "JOB-RESULT.json", json.dumps(result, indent=1) + "\n")
        self.log(("no repair" if code == EXIT_NO_REPAIR else "repair FAILED") + ": " + "; ".join(problems)[:600]
                 + f"; originals {'restored' if same else 'NOT fully restored'}; hold kept")
        return code


def _size(p):
    total = 0
    for d, _dirs, files in os.walk(p):
        for f in files:
            try:
                total += os.lstat(os.path.join(d, f)).st_size
            except OSError:
                pass
    return total


def touch_changed(live, before):
    """Touch every test file that is new or differs from the backup (rules that read file times see the repair)."""
    out = []
    if not live.is_dir():
        return out
    for p in sorted(live.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(live)
        old = before / rel
        if not old.is_file() or sha(old) != sha(p):
            os.utime(p, None)
            out.append(str(rel))
    return out


# ---------------------------------------------------------------- the inputs folder

FAIL_STATES = ("fail", "failed", "error", "timeout", "skip", "crash")


def failing_tests(results):
    out = []
    for group in ("security", "functional"):
        for name, v in (results.get(group) or {}).items():
            st = v if isinstance(v, str) else (v or {}).get("status", "") if isinstance(v, dict) else v
            if st not in ("pass", "passed", True):
                out.append((group, name, str(st)))
    return out


GROUP_WORDS = {"security", "functional", "tests", "test", "hidden", "project", "main"}


def name_tokens(name):
    """The words that name one test in verifier output: its last part (without parameters), and the part before it
    when the last is short (a parametrised case, 'TestX/sub')."""
    parts = [x for x in re.split(r"::|#|/|\.|\s", re.sub(r"\s*\(.*\)\s*$", "", str(name))) if x]
    parts = [re.sub(r"\[.*\]$", "", x) for x in parts]
    parts = [x for x in parts if x and x.lower() not in GROUP_WORDS]
    if not parts:
        return [str(name)]
    out = [parts[-1]]
    if len(parts[-1]) < 8 and len(parts) > 1:
        out.append(parts[-2])
    return [t for t in out if len(t) >= 4] or [parts[-1]]


def message_excerpts(gdir, tests, per_test=120, max_tests=25):
    """For each failing test, the lines of the verifier output that name it, with context."""
    logs = []
    for p in sorted(Path(gdir).rglob("*")):
        if p.is_file() and p.suffix in (".log", ".txt", ".xml", ".out") and p.stat().st_size < (64 << 20):
            logs.append((str(p.relative_to(gdir)), read_lines(p)))
    out = []
    for group, name, st in tests[:max_tests]:
        out.append(f"### {group}: {name} ({st})\n")
        shown = 0
        for fname, lines in logs:
            hits = [i for i, line in enumerate(lines) if any(t in line for t in name_tokens(name))]
            for i in hits[:3]:
                lo, hi = max(0, i - 8), min(len(lines), i + 20)
                out.append(f"{fname}:{lo + 1}-{hi}\n```\n" + "\n".join(lines[lo:hi])[:6000] + "\n```\n")
                shown += hi - lo
                if shown >= per_test:
                    break
            if shown >= per_test:
                break
        if not shown:
            out.append("(no line of the verifier output names this test)\n")
    if len(tests) > max_tests:
        out.append(f"... {len(tests) - max_tests} more failing tests: see results.json\n")
    return "\n".join(out)


def read_lines(p):
    try:
        return Path(p).read_text(errors="replace").splitlines()
    except OSError:
        return []


def transcript_lines(path, limit=4000):
    """The agent's text, tool calls and short results from a claude-code.txt transcript (JSON lines)."""
    out = []
    try:
        fh = open(path, errors="replace")
    except OSError:
        return out
    with fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            msg = ev.get("message") if isinstance(ev, dict) else None
            if not isinstance(msg, dict):
                continue
            for c in msg.get("content") or []:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "text" and ev.get("type") == "assistant":
                    out.append("AGENT: " + c.get("text", "").strip().replace("\n", " ")[:1200])
                elif c.get("type") == "tool_use":
                    out.append(f"CALL {c.get('name')}: " + json.dumps(c.get("input"), ensure_ascii=False)[:500])
                elif c.get("type") == "tool_result":
                    cont = c.get("content")
                    txt = cont if isinstance(cont, str) else " ".join(
                        x.get("text", "") for x in (cont or []) if isinstance(x, dict))
                    out.append("RESULT: " + str(txt).strip()[:500].replace("\n", " | "))
    return out


GENERIC_STEMS = {"mod", "index", "__init__", "main", "lib", "utils", "util", "helpers", "types", "init", "app", "config"}
SKIP_PATH = re.compile(r"(?i)(^|/)(\.?cache|vendor|node_modules|target|build|dist|\.git|__pycache__)/|\.lock$")


def edited_files(patch, limit=15):
    """Basenames of the source files a run's final diff changes (caches, vendored code and lock files left out)."""
    out = []
    for line in read_lines(patch) if Path(patch).is_file() else []:
        m = re.match(r"^(?:diff --git a/(\S+) b/|\+\+\+ b/(\S+))", line)
        m = m and (m.group(1) or m.group(2))
        if m and not SKIP_PATH.search(m):
            name = Path(m).name
            if Path(name).stem.lower() not in GENERIC_STEMS and name not in out:
                out.append(name)
        if len(out) >= limit:
            break
    return out


def transcript_excerpts(path, tests, max_lines=400, tail=30, files=(), max_chars=80_000):
    """The transcript lines around the failing area: where the agent met a failing test's name or edited one of the
    files its final diff changes (with 2 lines of context), then its last lines."""
    lines = transcript_lines(path)
    if not lines:
        return "(no transcript)\n"
    keys = {t.lower() for _g, n, _s in tests for t in name_tokens(n)} | {f.lower() for f in files}
    keep = set()
    for i, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in keys):
            keep.update(range(max(0, i - 2), min(len(lines), i + 3)))
    picked = sorted(keep)[:max_lines]
    body, last = [], -2
    for i in picked:
        if i != last + 1:
            body.append(f"--- transcript line {i + 1} ---")
        body.append(lines[i])
        last = i
    text = "\n".join(body or ["(none)"])
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[... cut: read the full transcript ...]"
    return ("## Around the failing tests (" + ", ".join(sorted(keys))[:300] + ")\n\n" + text
            + f"\n\n## The last {tail} lines (the agent's own conclusion)\n\n" + "\n".join(lines[-tail:]) + "\n")


def write_inputs(slug, inputs, F, manual, key, cfg):
    """FINDING.json / FINDING.md, runs/<run>/ for every graded run, INPUTS.md."""
    import reconcile
    b, t = paths.BUILD / slug, paths.TASKS / slug
    cur_tests = repairstep.tests_hash(slug)
    (inputs / "FINDING.json").write_text(json.dumps({"key": key, "task": slug, "why": F["why"], "items": F["items"],
                                                     "manual": manual, "written_utc": qdb.utc()}, indent=1,
                                                    default=str))
    md = [f"# Finding for {slug} ({key})", "", f"Why the repair runs: {F['why'] or 'queued by the owner'}", ""]
    if manual:
        md += ["## The owner's finding (manual enqueue)", "", "```", json.dumps(manual, indent=1)
               if not isinstance(manual, str) else manual, "```", ""]
    for it in F["items"]:
        if it["source"] == "audit":
            md += [f"## Audit of {it['trial']} ({it['model']} {it['run']}, reward {it['reward']})", "",
                   f"- postmortem: {it['postmortem']} (grading audited: {it['audited']}, recorded {it['recorded']})",
                   f"- attribution {it['attribution']}, confidence {it['confidence']}, trustworthy {it['trustworthy']}, "
                   f"the unfair tests decided the run: {it['deciding']}",
                   f"- auditor's summary: {it['summary']}", f"- recommended action: {it.get('recommended_action')}", ""]
            for x in it["tests"]:
                md += [f"### {x.get('test')}", ""] + [f"- {k}: {x.get(k)}" for k in
                                                      ("verdict", "unfair_kind", "stated_in_instruction",
                                                       "correct_fix_would_pass", "other_reading_fails",
                                                       "conflicting_sentences", "model_behaviour") if k in x] + [""]
        elif it["source"] == "fairness":
            md += ["## Fairness review (build/%s/FAIRNESS.md)" % slug, "", f"- {it.get('why')}; verdict {it['verdict']}, "
                   f"conflicts {it.get('conflicts')}", "", "Required changes / conflicts, quoted:", "", "```",
                   it.get("required") or "(see FAIRNESS.md)", "```", ""]
        else:
            md += ["## Owner decision (HUMAN-DECISION.md)", "", "```", it.get("text", ""), "```", ""]
    (inputs / "FINDING.md").write_text("\n".join(str(x) for x in md))

    runs_dir = inputs / "runs"
    runs_dir.mkdir()
    index = []
    for r in reconcile.graded_runs(slug, cfg["jobs_dir"]):
        tr = Path(r["path"])
        m = re.search(r"-(deepseek|mimo)-r(\d+)-", r["job"])
        name = f"{m.group(1)}-r{m.group(2)}-{tr.name.split('__')[-1]}" if m else tr.name
        d = runs_dir / name
        d.mkdir()
        gname, ghash, _w = repairstep.grading_in_use(r)
        gdir = tr / gname / "verifier" if gname != "original" else tr / "verifier"
        results = repairstep.jload(gdir / "results.json") or {}
        fails = failing_tests(results)
        if results:
            (d / "results.json").write_text(json.dumps(results, indent=1))
        (d / "failures.md").write_text(f"# Failing tests of {tr.name} ({gname})\n\n" + message_excerpts(gdir, fails))
        harvest = repairstep.jload(tr / "final-code" / "HARVEST.json") or {}
        patch = tr / "final-code" / "changes.patch"
        note = ""
        if patch.is_file():
            data = patch.read_bytes()
            (d / "changes.patch").write_bytes(data[:PATCH_MAX])
            if len(data) > PATCH_MAX or harvest.get("truncated"):
                note = (f"changes.patch is {'cut at ' + str(PATCH_MAX >> 10) + ' KB here' if len(data) > PATCH_MAX else 'complete here'}"
                        f"{'; the harvest itself was truncated' if harvest.get('truncated') else ''}: read the "
                        f"run's workspace in {tr / 'artifacts' / 'workspace'} for the full code")
        else:
            note = f"no changes.patch: read the run's workspace in {tr / 'artifacts' / 'workspace'}"
        if (tr / "final-code" / "changed_files.tsv").is_file():
            shutil.copy2(tr / "final-code" / "changed_files.tsv", d / "changed_files.tsv")
        (d / "transcript-excerpts.md").write_text(transcript_excerpts(tr / "agent" / "claude-code.txt", fails,
                                                                      files=edited_files(patch)))
        audit = repairstep.current_audit(tr)
        res = repairstep.jload(tr / "result.json") or {}
        lines = [f"# Run {name}", "", f"- trial folder: {tr}", f"- reward (grading in use, {gname}): "
                 f"{repairstep._grading_reward(tr, gname)}",
                 f"- graded on tests {ghash or 'unknown'} (current tests {cur_tests})",
                 f"- failing tests: {len(fails)} (failures.md; results.json)",
                 f"- final diff: changes.patch{'; ' + note if note else ''}",
                 f"- transcript: {tr / 'agent' / 'claude-code.txt'} (excerpts in transcript-excerpts.md)",
                 f"- audit: {audit[1] if audit else 'none recorded for this grading'}"
                 + (f" ({(audit[0].get('verdict') or {}).get('attribution')})" if audit else ""),
                 f"- exception: {(res.get('exception_info') or {}).get('exception_type') or '-'}"]
        (d / "RUN.md").write_text("\n".join(lines) + "\n")
        index.append(f"- runs/{name}/ ({r['job']}): reward {r['reward']}, {len(fails)} failing test(s)"
                     + (f", audit {audit[1].name}" if audit else ", no audit"))

    hist = sorted(p.name for p in (b / "history").glob("*")) if (b / "history").is_dir() else []
    prior = [p for p in hist if re.search(r"repair-(analysis|proposal)", p)]
    md = [f"# Inputs for the repair of {slug}", "",
          f"Finding: FINDING.md (key {key}). Test version now: {cur_tests}.", "",
          "## The failing runs' evidence (every graded run of the current task version)", ""] + (index or ["- none"]) + [
          "", "## The task", "",
          f"- {t / 'instruction.md'}", f"- {t / 'tests'}/ (all files)", f"- {t / 'solution'}/ (fix.patch)",
          f"- {b / 'manifest.json'} and {b / 'checks'}/*.patch", f"- {b / 'gate_report.json'}",
          f"- {b / 'trial_summary.md'} (per-test results of every run; which tests decided a run)",
          f"- {b / 'notes.md'} (the FULL build notes: you need the history)",
          f"- {b / 'FAIRNESS.md'} and FAIRNESS.md.prev-* (earlier reviews), {b / 'HUMAN-DECISION.md'}",
          "- earlier repairs: " + (", ".join(n for n, _t in repairstep.repair_folders(b)) or "none") + " (their README.md)",
          f"- {b / 'history'}/: " + (", ".join(hist) or "empty"), ""]
    if prior:
        md += ["## A prior repair analysis exists", "",
               "history/ holds " + ", ".join(prior) + ": an earlier repair was analysed and stopped before the swap. "
               "Use it as a starting point to VERIFY, never to apply blindly: check every claim against the tests, the "
               "code and the runs' evidence, and validate everything again.", ""]
    (inputs / "INPUTS.md").write_text("\n".join(md))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--job", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--finding", default="", help="JSON: a finding key (f-...), the owner's text, or an object")
    a = ap.parse_args(argv[1:])
    os.environ.setdefault("CWEQ_JOB", f"manual-{os.getpid()}")   # our children are ours (never waited for)
    import config
    cfg = config.load(a.config)
    try:
        finding = json.loads(a.finding) if a.finding else ""
    except ValueError:
        finding = a.finding
    conn = qdb.connect(cfg["db"]) if Path(cfg["db"]).parent.is_dir() else None
    return Job(a.slug, cfg, a.job, conn).run(finding)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
