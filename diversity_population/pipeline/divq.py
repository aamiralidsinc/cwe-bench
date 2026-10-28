#!/usr/bin/env python3
"""divq: the diversity experiment's work queue on GitHub Actions. See DESIGN.md.

Run with a Python 3.11+ interpreter (tomllib), e.g. ~/.venvs/kaggle/bin/python3.12 on the Mac, python3 on the VM.

  divq init
  divq preflight                       # read-only setup checks; exit 2 on a critical gap
  divq release build <commit> | list | activate <id> | rollback
  divq reconcile [--once] [--dry-run]  # derive jobs from out/results/ + the batch
  divq dispatch  [--once] [--dry-run]  # start queued jobs within the per-account limits
  divq poll      [--once]              # follow runs, fetch+decrypt+check completed ones
  divq run       [--once]              # reconcile, adapt limits, dispatch, poll (the main loop)
  divq status | explain <task> | events [next|handle ID --action T] | inbox [--html PATH]
  divq repo sync                       # print the commands that create/update each account's repo (owner runs them)
"""
import argparse, json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import divq_core as core
import divq_release as rel

WF_DIR = core.HERE / "workflows"


def executor(s):
    import divq_gh
    return divq_gh.GH(s)


def loop(fn, once, tick):
    while True:
        fn()
        if once:
            return
        time.sleep(tick)


def cmd_run(s, c, a):
    ex = None if a.dry_run else executor(s)
    tick = s.get("dispatch", "tick_sec", default=60)

    def tick_once():
        core.record_settings(c, s, "run")
        planned, new = core.reconcile(c, s, dry_run=a.dry_run)
        queued = bool(c.execute("SELECT 1 FROM jobs WHERE state='queued' LIMIT 1").fetchone())
        if not a.dry_run:
            core.adapt_limits(c, s, queued_work=queued)
            started, why = core.dispatch_once(c, s, ex)
            closed = core.poll_once(c, s, ex)
            print(core.utc(), f"reconciled(+{new}) dispatched({len(started)}{' — '+why if why else ''}) closed({len(closed)})", flush=True)
        else:
            print(core.utc(), f"[dry-run] would queue {new}, {len(planned)} planned", flush=True)
    loop(tick_once, a.once, tick)


def cmd_status(s, c, a):
    counts = core.status_counts(c)
    print("release:", core.kv_get(c, "release.current") or "(none active)")
    why = core.admission(c, s)
    print("dispatch:", "open" if not why else f"closed — {why}")
    for kind in ("build", "trial_run"):
        d = counts.get(kind, {})
        print(f"  {kind:10} " + "  ".join(f"{st}={d.get(st,0)}" for st in ("queued", "dispatched", "running", "done", "failed", "blocked")))
    for acct in [x["name"] for x in s.accounts()]:
        print(f"  account {acct}: limit {core.account_limit(c, s, acct)}, running {core.running_on(c, acct)}")
    # stage tally from disk
    stages = {}
    for t in core.read_batch(s):
        if core.task_priority(s, t) is None:
            continue
        st = core.stage(s, t)
        stages[st] = stages.get(st, 0) + 1
    print("stages (enabled chunks):", json.dumps(stages))


def cmd_explain(s, c, a):
    t = next((x for x in core.read_batch(s) if x["slug"] == a.task), None)
    if not t:
        sys.exit(f"{a.task} is not in the batch")
    res = core.read_results(s, t["slug"])
    print(f"{t['slug']}  chunk {t['chunk']} order {t['order']} score {t['score']}  pattern {t['pattern']}")
    print("stage:", core.stage(s, t, res))
    if res["build"]:
        print("build:", {k: res["build"].get(k) for k in ("status", "fingerprint", "account", "run_id", "token")})
    for m, runs in res["runs"].items():
        ms, g = core.model_state(runs, s.get("trial", "runs", default=3))
        print(f"  {m}: {ms} rewards={g}")
    for j in core.jobs_for(c, t["slug"]):
        print(f"  job {j['id']} {j['kind']} {j['state']} acct={j['account']} run={j['run_id']} rel={j['release']} "
              f"cfg={j['settings_hash']} attempts={j['attempts']}/{j['max_attempts']} :: {(j['result'] or '')[:80]}")


def cmd_events(s, c, a):
    if a.sub == "next":
        urgent = set(s.get("events", "urgent", default=["disk.critical"]))
        rows = c.execute("SELECT * FROM events WHERE state='open' ORDER BY id").fetchall()
        rows.sort(key=lambda r: (r["kind"] not in urgent, r["id"]))
        print(json.dumps(dict(rows[0]), indent=1) if rows else "no open events")
    elif a.sub == "handle":
        c.execute("UPDATE events SET state='handled', action=? WHERE id=?", (a.action, a.id))
        print(f"handled event {a.id}")
    else:
        for r in c.execute("SELECT * FROM events WHERE state='open' ORDER BY id").fetchall():
            print(f"  [{r['id']}] {r['kind']} {r['task']} {r['payload']}")


def cmd_inbox(s, c, a):
    lines = ["# divq decisions inbox", ""]
    bc = [t for t in core.read_batch(s) if core.task_priority(s, t) is not None and core.stage(s, t) == "breaker_candidate"]
    lines.append(f"## Breaker candidates ({len(bc)}) — for VM fairness + audit, then the keep decision")
    lines += [f"- {t['slug']} ({t['pattern']}, score {t['score']})" for t in bc]
    big = [t for t in core.read_batch(s) if core.task_priority(s, t) is not None and core.stage(s, t) == "too_big_for_runner"]
    if big:
        lines.append(f"\n## Too big for a standard runner ({len(big)}) — run these on the VM")
        lines += [f"- {t['slug']}" for t in big]
    blocked = c.execute("SELECT * FROM jobs WHERE state='blocked' ORDER BY id").fetchall()
    if blocked:
        lines.append(f"\n## Blocked jobs ({len(blocked)})")
        lines += [f"- job {j['id']} {j['kind']} {j['task']}: {(j['result'] or '')[:100]}" for j in blocked]
    if not [x for x in s.accounts()]:
        lines.append("\n## Accounts\n- none enabled. Flip `enabled = true` in settings.toml for the accounts to use, then `divq repo sync`.")
    out = "\n".join(lines) + "\n"
    if a.html:
        Path(a.html).write_text(f"<!doctype html><meta charset=utf-8><title>divq inbox</title><pre>{out}</pre>")
        print("wrote", a.html)
    else:
        print(out)


def cmd_repo_sync(s, c, a):
    print("# Owner runs these (git push / secret writes may be blocked for the agent).")
    print("# Each repo is PUBLIC and holds only: the two workflows, a one-line README, and the encrypted payload.")
    rid = core.kv_get(c, "release.current")
    for acct in [x for x in s.accounts(enabled_only=False)]:
        if not acct.get("enabled"):
            print(f"\n# {acct['name']}: disabled in settings; skipping"); continue
        repo = acct["repo"]
        print(f"\n## {acct['name']} -> {repo} (token: {acct['token_var']})")
        print(f"export GH_TOKEN=$(grep '^{acct['token_var']}=' {s.data['paths']['env_file']} | cut -d= -f2- | tr -d \"\\\"' \\r\")")
        print(f"gh repo view {repo} >/dev/null 2>&1 || gh repo create {repo} --public -d 'build/trial runner'")
        print(f"# push diversity_population/pipeline/workflows/*.yml to {repo}/.github/workflows/ and the payload to payload.tgz.gpg")
        print(f"gh secret set PAYLOAD_KEY -R {repo} < {s.data['paths']['key_file']}")
        print(f"grep '^DEEPSEEK_API_KEY=' {s.data['paths']['env_file']} | cut -d= -f2- | tr -d \"\\\"' \\r\\n\" | gh secret set DEEPSEEK_API_KEY -R {repo}")
        print(f"grep '^MIMO_API_KEY=' {s.data['paths']['env_file']} | cut -d= -f2- | tr -d \"\\\"' \\r\\n\" | gh secret set MIMO_API_KEY -R {repo}")
    print(f"\n# active release payload to push: {rel.payload_path(s, c, rid) if rid else '(build+activate a release first)'}")


def cmd_preflight(s, c, a):
    crit = 0
    def line(level, msg):
        nonlocal crit
        if level == "CRITICAL":
            crit += 1
        print(f"  [{level}] {msg}")
    print("divq preflight")
    # payload key
    line("OK" if s.p("key_file").is_file() else "CRITICAL",
         f"payload key {s.p('key_file')}" + ("" if s.p('key_file').is_file() else " MISSING (openssl rand -base64 48 > FILE; chmod 600 FILE)"))
    # release
    rid = core.kv_get(c, "release.current")
    line("OK" if rid else "CRITICAL", f"active release {rid}" if rid else "no active release (divq release build/activate)")
    # local disk
    free = core.local_free_gb(s.p("results").parent if s.p("results").parent.exists() else core.DIV)
    floor = s.get("dispatch", "local_disk_floor_gb", default=30)
    line("OK" if free >= floor else "CRITICAL", f"local disk {free:.0f} GB (floor {floor})")
    # batch present
    line("OK" if (s.p("chunks") / "all_chunks.tsv").is_file() else "CRITICAL", "batch chunks present")
    # accounts
    accts = s.accounts()
    if not accts:
        line("NEEDS APPLYING", "no account enabled (flip enabled=true in settings.toml for the accounts to use)")
    else:
        ex = executor(s)
        for acct in accts:
            try:
                login = ex.login(acct["name"])
            except Exception as e:
                line("CRITICAL", f"{acct['name']}: token error: {str(e)[:80]}"); continue
            line("OK" if login else "CRITICAL", f"{acct['name']}: token resolves to '{login}'")
            if not a.no_remote:
                for wf in ("build", "trial"):
                    line("OK" if ex.workflow_registered(acct["name"], wf) else "NEEDS APPLYING",
                         f"{acct['name']}: workflow '{wf}' registered on {acct['repo']}")
                have = ex.secret_names(acct["name"])
                for sec in ("PAYLOAD_KEY", "DEEPSEEK_API_KEY", "MIMO_API_KEY"):
                    line("OK" if sec in have else "NEEDS APPLYING", f"{acct['name']}: secret {sec} set")
    print(f"preflight: {'CRITICAL gaps: ' + str(crit) if crit else 'no critical gaps'}")
    sys.exit(2 if crit else 0)


def main():
    ap = argparse.ArgumentParser(prog="divq")
    ap.add_argument("--db"); ap.add_argument("--config")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "status"):
        sub.add_parser(name)
    for name in ("reconcile", "dispatch", "run"):
        p = sub.add_parser(name); p.add_argument("--once", action="store_true"); p.add_argument("--dry-run", action="store_true")
    sub.add_parser("poll").add_argument("--once", action="store_true")
    pe = sub.add_parser("preflight"); pe.add_argument("--no-remote", action="store_true")
    px = sub.add_parser("explain"); px.add_argument("task")
    pev = sub.add_parser("events"); pev.add_argument("sub", nargs="?", choices=["next", "handle"]); pev.add_argument("id", nargs="?", type=int); pev.add_argument("--action", default="")
    pin = sub.add_parser("inbox"); pin.add_argument("--html")
    pr = sub.add_parser("release"); prs = pr.add_subparsers(dest="sub", required=True)
    prb = prs.add_parser("build"); prb.add_argument("commit"); prb.add_argument("--note", default="")
    prs.add_parser("list"); pra = prs.add_parser("activate"); pra.add_argument("id"); prs.add_parser("rollback")
    prp = sub.add_parser("repo"); prp.add_argument("sub", choices=["sync"])
    a = ap.parse_args()

    s = core.Settings(a.config)
    c = core.connect(a.db or s.p("db"))
    core.record_settings(c, s, a.cmd)

    if a.cmd == "init":
        print("db:", a.db or s.p("db")); return
    if a.cmd == "status":
        return cmd_status(s, c, a)
    if a.cmd == "reconcile":
        planned, n = core.reconcile(c, s, dry_run=a.dry_run)
        print(f"{'[dry-run] ' if a.dry_run else ''}planned {len(planned)}, newly queued {n}"); return
    if a.cmd == "dispatch":
        ex = None if a.dry_run else executor(s)
        started, why = core.dispatch_once(c, s, ex, dry_run=a.dry_run)
        print(f"{'[dry-run] ' if a.dry_run else ''}started {len(started)}" + (f"; closed: {why}" if why else "")); return
    if a.cmd == "poll":
        print("closed:", core.poll_once(c, s, executor(s))); return
    if a.cmd == "run":
        return cmd_run(s, c, a)
    if a.cmd == "preflight":
        return cmd_preflight(s, c, a)
    if a.cmd == "explain":
        return cmd_explain(s, c, a)
    if a.cmd == "events":
        return cmd_events(s, c, a)
    if a.cmd == "inbox":
        return cmd_inbox(s, c, a)
    if a.cmd == "repo":
        return cmd_repo_sync(s, c, a)
    if a.cmd == "release":
        if a.sub == "build":
            return rel.build(s, c, a.commit, a.note)
        if a.sub == "list":
            for r in c.execute("SELECT * FROM releases ORDER BY created").fetchall():
                mark = " *active" if r["id"] == core.kv_get(c, "release.current") else ""
                print(f"  {r['id']}  {r['created']}  commit {r['commit_sha'][:12]}  tasks {r['tasks']}  {r['note']}{mark}")
            return
        if a.sub == "activate":
            return rel.activate(s, c, a.id)
        if a.sub == "rollback":
            return rel.rollback(s, c)


if __name__ == "__main__":
    main()
