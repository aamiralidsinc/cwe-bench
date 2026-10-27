"""The event queue (events.py), the decisions inbox (inbox.py) and delivery preparation (delivery.py)."""
import json
import sys

import delivery
import events
import inbox
import qdb
import taskstate
import worker
from test_adopt import batch, built, ledger

BREAKER = ("**failed 0/3** [0.5]", "**failed 0/3** [0.4]", "**BREAKER candidate**")


def states():
    ctx = taskstate.context([])
    return ctx, events.read_all(ctx)


def sync(conn, cfg, **kw):
    ctx, st = states()
    kw.setdefault("disk_gb", 900)
    kw.setdefault("ready", [])
    return events.sync(conn, cfg, ctx, st, **kw)


def fairness(root, slug, verdict="READY", extra=""):
    (root / "build" / slug / "FAIRNESS.md").write_text(f"# Fairness review\n\n{extra}\n\nGATE_A: {verdict}\n")


def keep(root, slug, date="2026-10-27"):
    (root / "build" / slug / "HUMAN-DECISION.md").write_text(f"DECISION: KEEP\nDATE: {date}\n")


def test_first_pass_is_a_silent_baseline_then_each_transition_emits_once(root, conn, cfg):
    batch(root, "scale-b9", ["a-s2"])
    built(root, "a-s2", runs={"deepseek": [0.5] * 3, "mimo": [0.4] * 3})
    ledger(root, [("a-s2", *BREAKER)])
    assert sync(conn, cfg) == []                                  # baseline: stage awaiting_fairness recorded
    fairness(root, "a-s2", extra="Human review: confirm the reading of rule 2.")
    got = sync(conn, cfg)
    assert [(e["kind"], e["task"]) for e in got] == [("stage.awaiting_decision", "a-s2")]
    assert sync(conn, cfg) == []                                  # same state: nothing new
    assert [r["kind"] for r in events.listing(conn)] == ["stage.awaiting_decision"]


def test_breaker_candidate_and_audit_ready(root, conn, cfg):
    built(root, "b-s2", runs={"deepseek": [0.5] * 3, "mimo": [0.4] * 3})
    ledger(root, [("b-s2", "**failed 0/3** [0.5]", "0/2 so far, needs 3 [0.4]", "open")])
    sync(conn, cfg)
    ledger(root, [("b-s2", *BREAKER)])
    ready = ["/j/b-s2-mimo-r3-x/b-s2__T3/postmortem-1"]
    got = sync(conn, cfg, ready=ready)
    assert {e["kind"] for e in got} == {"breaker.candidate", "audit.ready", "stage.awaiting_fairness"}
    assert sync(conn, cfg, ready=ready) == []                    # a folder emits once, ever


def test_job_events_after_the_baseline_only(root, conn, cfg):
    sync(conn, cfg)
    a, _ = qdb.enqueue(conn, "regrade", "x-s2", {"trial": "j/x-s2__1"})
    b, _ = qdb.enqueue(conn, "cleanup", "_machine", {"hour": "h"})
    c, _ = qdb.enqueue(conn, "regate", "y-s2", {"fp": "1"})
    d, _ = qdb.enqueue(conn, "rescore", "z-s2", {"fp": "1"})
    qdb.set_state(conn, a, "failed", "boom")
    qdb.set_state(conn, b, "done", "ok")                          # a bookkeeping kind: no event when done
    qdb.set_state(conn, c, "blocked", "attempts used")
    qdb.set_state(conn, d, "done", "superseded by a newer version")  # bookkeeping close: no event
    got = sync(conn, cfg)
    assert sorted((e["kind"], e["task"]) for e in got) == [("job.blocked", "y-s2"), ("job.failed", "x-s2")]
    assert sync(conn, cfg) == []


def test_urgent_first_then_fifo_and_handle(root, conn, cfg):
    sync(conn, cfg)
    events.emit(conn, "stage.kept", "k1", "a")
    events.emit(conn, "job.failed", "k2", "b")
    got = sync(conn, cfg, disk_gb=50)                             # below the critical level
    assert [e["kind"] for e in got] == ["disk.critical"] and got[0]["urgent"]
    assert sync(conn, cfg, disk_gb=40) == []                      # still critical: no second event
    first = events.next_open(conn)
    assert first["kind"] == "disk.critical"
    assert events.handle(conn, first["id"], "paused builds") and not events.handle(conn, first["id"], "again")
    assert events.next_open(conn)["dedup"] == "k1"                # then strictly oldest first


def test_adoption_conflicts_emit_once(root, conn, cfg):
    sync(conn, cfg)
    conn.execute("INSERT INTO adoptions (started, finished, tasks, counts, conflicts, differences, ok)"
                 " VALUES ('t','t',0,'{}',?, '[]', 0)", (json.dumps(["p-s2: task package exists but no build record"]),))
    got = sync(conn, cfg)
    assert [(e["kind"], e["urgent"]) for e in got] == [("adoption.conflict", True)]
    assert sync(conn, cfg) == []


def test_dry_run_writes_nothing(root, conn, cfg):
    sync(conn, cfg)
    assert sync(conn, cfg, disk_gb=10, dry_run=True)[0]["kind"] == "disk.critical"
    assert events.listing(conn) == []


def test_delivery_plan_both_model_breakers_only(root, conn, cfg):
    for s in ("k-s2", "one-s2", "done-s2"):
        built(root, s, runs={"deepseek": [0.5] * 3, "mimo": [0.4] * 3})
        keep(root, s)
    ledger(root, [("k-s2", *BREAKER), ("one-s2", "**failed 0/3** [0.5]", "SOLVED 1/2", "rejected (MiMo solved)"),
                  ("done-s2", *BREAKER)])
    (root / "build" / "audit" / "delivered.tsv").write_text("# slug\tdelivered_as\tclient_commit\tdate\n"
                                                            "done-s2\tdone-task\tabc\t2026-10-27\n")
    _ctx, st = states()
    jobs, notes = delivery.plan(st)
    assert [j["task"] for j in jobs] == ["k-s2"] and jobs[0]["args"] == {"decision": "KEEP 2026-10-27"}
    assert any("one-s2" in n and "not a both-model breaker" in n for n in notes)
    rep = delivery.reconcile(conn, cfg, st)
    again = delivery.reconcile(conn, cfg, st)
    assert rep[0]["want"][0]["id"] == again[0]["want"][0]["id"]   # one job per decision


def fake_export(tmp_path, body=""):
    """A stand-in for export_delivery.py: writes the layout and a report, like the real tool."""
    script = tmp_path / "fake_export.py"
    script.write_text(f'''import sys, pathlib
out, slug, name = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[4].split("=")[1]
(out / "tasks" / name).mkdir(parents=True)
(out / "tasks" / name / "task.toml").write_text('[task]\\nname = "cwe-bench/' + slug + '"\\n')
for m in ("deepseek-v4.1-flash", "mimo-v2.6-pro"):
    for i in (1, 2, 3):
        d = out / "trajectory" / name / m / f"rollout{{i}}"; d.mkdir(parents=True)
        (d / "trajectory.json").write_text({body!r} if i == 1 else "{{}}")
(out / "EXPORT-REPORT.md").write_text("# Export report\\n\\n## Secret scan: 2 key values checked, 0 files redacted\\n")
''')
    return script


def test_prep_writes_ready_json(root, cfg, tmp_path):
    built(root, "k-s2")
    (root / "tasks" / "k-s2" / "task.toml").write_text('[metadata]\nrepo = "https://github.com/acme/Widget.js"\n'
                                                       'cwe_id = "CWE-918"\n')
    (root / "tasks" / "k-s2" / "instruction.md").write_text("# Widgets fetch any address\n")
    script = fake_export(tmp_path)
    out = tmp_path / "pkg"
    name = delivery.propose_name("k-s2")
    assert name == "widget-js-ssrf"
    rc, ready = delivery.prep("k-s2", cfg, out_dir=out,
                              export=[sys.executable, str(script), str(out), "k-s2", "--name", f"k-s2={name}"])
    assert rc == 0 and ready["ready"] and ready["rollouts"] == {"deepseek-v4.1-flash": 3, "mimo-v2.6-pro": 3}
    assert 'name = "cwe-bench/widget-js-ssrf"' in (out / "tasks" / name / "task.toml").read_text()
    assert ready["readme_row"] == "| `widget-js-ssrf` | Widgets fetch any address |"
    assert json.loads((out / "ready.json").read_text())["ready"]


def test_prep_blocks_on_a_key_in_a_trajectory(root, cfg, tmp_path):
    built(root, "k-s2")
    script = fake_export(tmp_path, body="ANTHROPIC_API_KEY=sk-" + "a" * 40 + " task-" + "b" * 40)
    out = tmp_path / "pkg"
    rc, ready = delivery.prep("k-s2", cfg, name="k-task", out_dir=out,
                              export=[sys.executable, str(script), str(out), "k-s2", "--name", "k-s2=k-task"])
    assert rc == 3 and not ready["ready"]
    assert sorted(ready["pattern_hits"]) == [f"trajectory/k-task/{m}/rollout1/trajectory.json"
                                             for m in ("deepseek-v4.1-flash", "mimo-v2.6-pro")]


def test_task_names_are_not_keys(root):
    assert not delivery.PATTERNS.search("src/main/help/en/help/task-" + "x" * 40)
    assert delivery.PATTERNS.search("KEY=sk-" + "x" * 40)


def test_record_delivered_is_idempotent_and_adds_the_control(root):
    built(root, "stk-k-1")
    (root / "tasks" / "stk-k-1-control").mkdir(parents=True)
    keep(root, "stk-k-1")
    (root / "build" / "audit").mkdir(parents=True, exist_ok=True)
    assert delivery.record_delivered("stk-k-1", "k-task", "c0ffee1", "2026-10-28") == (["stk-k-1", "stk-k-1-control"], True)
    assert delivery.record_delivered("stk-k-1", "k-task", "c0ffee1", "2026-10-28") == ([], False)
    reg = (root / "build" / "audit" / "delivered.tsv").read_text()
    assert reg.count("stk-k-1\tk-task\tc0ffee1\t2026-10-28") == 1
    assert "DELIVERED: 2026-10-28 to marahassan8/cwe-bench main, commit c0ffee1, as tasks/k-task" in \
        (root / "build" / "stk-k-1" / "HUMAN-DECISION.md").read_text()
    _ctx, st = states()
    assert st["stk-k-1"]["stage"] == "delivered"


def test_inbox_sections(root, conn, cfg):
    for s in ("dec-s2", "nr-s2", "kept-s2"):
        built(root, s, runs={"deepseek": [0.5] * 3, "mimo": [0.4] * 3})
    ledger(root, [(s, *BREAKER) for s in ("dec-s2", "nr-s2", "kept-s2")])
    fairness(root, "dec-s2", extra="**Human review:** confirm that <b>rule 2</b> covers the second route.")
    fairness(root, "nr-s2", "NOT_READY", extra="**Required change:** reword P1 over its protected data.")
    keep(root, "kept-s2")
    jid, _ = qdb.enqueue(conn, "regrade", "x-s2", {"trial": "j/x"})
    qdb.set_state(conn, jid, "blocked", "attempts used up")
    _ctx, st = states()
    items = inbox.collect(conn, st, [])
    assert [i["task"] for i in items["keep"]] == ["dec-s2"]
    assert "rule 2" in items["keep"][0]["detail"]
    assert "reword P1" in items["not_ready"][0]["detail"]
    assert [i["task"] for i in items["deliver"]] == ["kept-s2"]
    assert items["blocked"][0]["task"] == "x-s2"
    page = inbox.page(items)
    assert "&lt;b&gt;rule 2&lt;/b&gt;" in page and "http" not in page.replace("https://", "")
    assert "Decisions inbox" in inbox.text(items)


def test_worker_command_for_delivery_prep(conn, cfg):
    jid, _ = qdb.enqueue(conn, "delivery_prep", "k-s2", {"decision": "KEEP 2026-10-27"})
    argv = worker.command(qdb.get(conn, jid), cfg)
    assert argv[-2:] == ["prep", "k-s2"] and argv[-3].endswith("delivery.py")
