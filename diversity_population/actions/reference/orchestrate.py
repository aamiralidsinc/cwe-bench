#!/usr/bin/env python3
"""Per-item trial orchestrator (incremental, resumable).

One run per task (not a matrix), so each task is independent: dispatch DeepSeek; the moment a task's
run finishes, read its verdict and — only if DeepSeek failed 3/3 — dispatch that task's MiMo run,
without waiting on any other task. both-fail 3/3 => breaker candidate.

  python3 -I orchestrate.py arm_a.tsv        # tsv cols: id  repo  build_run  tokenvar

State -> results/orch/<arm>.state.json (resumable); verdicts -> results/orch/<arm>.verdicts.tsv.
Reads .env for per-repo tokens + the payload key for decrypting result artifacts.
"""
import csv, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.expanduser("~/terminal-bench/.env")
KEY = os.path.expanduser("~/.tb-graders/cwe/precision_validation/payload.key")
OUT = os.path.join(HERE, "results", "orch"); os.makedirs(OUT, exist_ok=True)
RUNS = "3"


def envval(var):
    for l in open(ENV):
        if l.startswith(var + "="):
            return l.split("=", 1)[1].strip().strip('"\'').rstrip("\r")
    return ""


def gh(token, *args, timeout=120):
    e = dict(os.environ, GH_TOKEN=token)
    return subprocess.run(["gh", *args], capture_output=True, text=True, env=e, timeout=timeout)


def dispatch(t, build_run, tid, model):
    """Dispatch one per-item run; return its run id (the new run for this workflow)."""
    before = set(_run_ids(t["token"], t["repo"]))
    gh(t["token"], "workflow", "run", "trial", "-R", t["repo"],
       "-f", f"build_run={build_run}", "-f", f"ids={tid}", "-f", f"model={model}", "-f", f"runs={RUNS}")
    for _ in range(12):
        time.sleep(5)
        new = [r for r in _run_ids(t["token"], t["repo"]) if r not in before]
        if new:
            return new[0]
    return None


def _run_ids(token, repo):
    r = gh(token, "run", "list", "-R", repo, "-w", "trial", "-L", "15",
           "--json", "databaseId", "-q", ".[].databaseId")
    return [x for x in r.stdout.split() if x]


def status(token, repo, run_id):
    r = gh(token, "run", "view", run_id, "-R", repo, "--json", "status,conclusion",
           "-q", '"\(.status) \(.conclusion)"')
    p = r.stdout.split()
    return (p[0] if p else "unknown", p[1] if len(p) > 1 else "")


def verdict(t, run_id, tid, model):
    """Read the SUMMARY line from the completed trial job's console log (echoed by the Trials step).
    Robust to the artifact not carrying it. Returns {solved,counted,infra,status,summary}."""
    jid = gh(t["token"], "run", "view", run_id, "-R", t["repo"], "--json", "jobs",
             "-q", '.jobs[]|select(.name|startswith("trial"))|.databaseId').stdout.split()
    if not jid:
        return {"status": "no-job"}
    log = gh(t["token"], "api", "--allow-escape-sequences",
             f"repos/{t['repo']}/actions/jobs/{jid[0]}/logs", timeout=120).stdout
    line = ""
    for l in log.splitlines():
        if "SUMMARY " in l and f" {tid} {model} " in l:
            line = l.split("SUMMARY", 1)[1]
            line = "SUMMARY" + line
    if not line:
        return {"status": "no-summary", "summary": ""}
    v = {"summary": line.strip(), "status": "ok"}
    for kv in line.split():
        if "=" in kv:
            k, val = kv.split("=", 1); v[k] = val.strip()
    # status in the SUMMARY is "ok" or "TRIAL-INFEASIBLE-..."; surface infeasible as a review flag
    if v.get("status", "").startswith("TRIAL-INFEASIBLE"):
        v["status"] = "infeasible"
    return v


def main():
    rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
    arm = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    sf = os.path.join(OUT, f"{arm}.state.json")
    st = json.load(open(sf)) if os.path.exists(sf) else {}
    for r in rows:
        st.setdefault(r["id"], {"id": r["id"], "repo": r["repo"], "build_run": r["build_run"],
                                "tokenvar": r["tokenvar"], "ds": {}, "mm": {}})
    tok = {r["tokenvar"]: envval(r["tokenvar"]) for r in rows}

    def tctx(s):
        return {"repo": s["repo"], "token": tok[s["tokenvar"]]}

    def save():
        json.dump(st, open(sf, "w"), indent=1)
        with open(os.path.join(OUT, f"{arm}.verdicts.tsv"), "w", newline="") as fh:
            w = csv.writer(fh, delimiter="\t"); w.writerow(["id", "repo", "ds", "mm", "verdict"])
            for s in st.values():
                w.writerow([s["id"], s["repo"], s["ds"].get("v", ""), s["mm"].get("v", ""), s.get("verdict", "")])

    def compute_verdict(s):
        # Both models run on EVERY task so MiMo-only breakers are captured too (user, 2026-10-23).
        ds, mm = s["ds"], s["mm"]
        if "solved" not in ds or "solved" not in mm:
            return  # wait until both sides have a parsed result
        d, m = ds.get("solved"), mm.get("solved")
        dok, mok = ds.get("status") == "ok", mm.get("status") == "ok"
        if not dok or not mok:
            s["verdict"] = f"review (ds={ds.get('status','?')} mm={mm.get('status','?')})"
        elif d == "0" and m == "0":
            s["verdict"] = "BREAKER (both fail 3/3)"
        elif d == "0" and m == "1":
            s["verdict"] = "DeepSeek-only breaker (MiMo solved)"
        elif d == "1" and m == "0":
            s["verdict"] = "MiMo-only breaker (DeepSeek solved)"
        else:
            s["verdict"] = "both solved (not breaker)"

    RERUN_MAX = 4  # a job that fails before emitting a result (transient artifact-download/infra) gets re-dispatched

    def poll_side(s, side, model):
        o = s[side]
        if not o.get("run"):
            o["run"] = dispatch(tctx(s), s["build_run"], s["id"], model)
            o["v"] = "dispatched"; print(f"[{side} dispatch] {s['id']} -> run {o['run']}", flush=True); return True
        if "solved" in o or o.get("status") in ("no-artifact", "rerun-exhausted"):
            return False  # terminal
        stt, concl = status(tctx(s)["token"], s["repo"], o["run"])
        if stt != "completed":
            o["v"] = "running"; return True
        r = verdict(tctx(s), o["run"], s["id"], model)
        # A failed job (artifact download, infra) emits no SUMMARY -> re-dispatch, never count as a model result.
        if r.get("status") in ("no-summary", "no-job") and concl != "success":
            o["reruns"] = o.get("reruns", 0) + 1
            if o["reruns"] > RERUN_MAX:
                o["status"] = "rerun-exhausted"; o["v"] = "rerun-exhausted"
                print(f"[{side} FAILED] {s['id']}: exhausted {RERUN_MAX} reruns", flush=True); return False
            print(f"[{side} rerun {o['reruns']}] {s['id']}: job {concl}/{r.get('status')} -> re-dispatch", flush=True)
            for k in ("run", "summary", "status"):
                o.pop(k, None)
            o["v"] = f"rerun {o['reruns']}"; return True
        o.update(r)
        o["v"] = f"solved={r.get('solved','?')} counted={r.get('counted','?')} {r.get('status','?')}"
        print(f"[{side} done] {s['id']}: {o['v']}", flush=True)
        return False

    # Dispatch BOTH models per item, then poll both to completion; verdict from both.
    for _ in range(700):  # up to ~23h at 120s
        pending = False
        for s in st.values():
            pending |= poll_side(s, "ds", "deepseek")
            pending |= poll_side(s, "mm", "mimo")
            compute_verdict(s)
        save()
        if not pending:
            break
        time.sleep(120)
    print("=== orchestrator done ===", flush=True)
    for s in st.values():
        print(f"{s['id']}\t{s.get('verdict','?')}")


if __name__ == "__main__":
    main()
