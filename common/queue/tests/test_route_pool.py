"""Router: solved stacked tasks join the general sibling pool (owner rule 2026-10-27), never a prioritized lane."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

import paths  # put on sys.path by conftest (via the queue modules)

REPO = next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file())


def load_route(root, monkeypatch):
    monkeypatch.setattr(paths, "ROOT", root)
    monkeypatch.setattr(paths, "DATA_ROOT", root)
    monkeypatch.setattr(paths, "STACKING_OUT", root / "pipelines" / "stacking" / "out")
    spec = importlib.util.spec_from_file_location("route_under_test", REPO / "pipelines/router/route.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


@pytest.fixture
def world(root, monkeypatch):
    so = root / "pipelines" / "stacking" / "out"
    for eid, repo in (("100", "org/solved"), ("101", "org/plain"), ("102", "org/built"), ("103", "org/queued")):
        write(so / "screener-ds" / f"{eid}.json", json.dumps({"entry_id": eid, "repo": repo, "pattern_fit": "A"}))
    write(root / "pipelines" / "router" / "out" / "stacking_batches.txt", "batchA\n")
    write(so / "batchA.tsv", "job_id\tslug\tpattern\tscore\trepo\n"
          "j1\tstk-solved-1\tH4\t0.6\torg/solved\nj2\tstk-open-2\tH4\t0.6\torg/open\n")
    write(root / "build" / "audit" / "ledger.md",
          "# Ledger\n\n## All tasks\n\n| Track | Task | DeepSeek | MiMo | Verdict |\n|---|---|---|---|---|\n"
          "| stacking | stk-solved-1 | SOLVED 1/1 | **failed 0/3** | rejected (DeepSeek solved) |\n"
          "| stacking | stk-open-2 | **failed 0/3** | **failed 0/3** | **BREAKER candidate** |\n")
    write(root / "tasks" / "built-s2" / "task.toml", '[metadata]\nrepo = "https://github.com/org/built"\n')
    # a sibling candidate already prepared and queued in a batch
    write(root / "pipelines" / "router" / "out" / "batches" / "scale-b9.txt", "queued-s2\n")
    write(root / "pipelines" / "router" / "out" / "step2" / "pipeline" / "specs_deepseek" / "queued-s2.json",
          json.dumps({"slug": "queued-s2", "entry_id": "103"}))
    # the sibling lane scripts the pool command runs (real code; they resolve their own repo root)
    for rel in ("pipelines/sibling/4-select/lane.py",):
        d = root / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(REPO / rel, d)
    return root


def test_step3_routes_into_the_general_pool_only(world, monkeypatch, capsys):
    r = load_route(world, monkeypatch)
    r.step3(None)
    out = world / "pipelines" / "router" / "out"
    assert (out / "step2" / "screener" / "100.json").is_file()          # the general pool
    assert (out / "step3" / "screener" / "100.json").is_file()          # the routing record
    assert not (out / "step3" / "pipeline" / "selection_deepseek.json").exists()   # no prioritized selection
    assert "stk-solved-1" in (out / "step3" / "routed.tsv").read_text()
    assert "stk-open-2" not in (out / "step3" / "routed.tsv").read_text()          # both failed: not routed
    r.step3(None)                                                        # once only
    assert (out / "step3" / "routed.tsv").read_text().count("stk-solved-1") == 1


def test_step2_keeps_routed_solved_tasks_in_the_pool(world, monkeypatch):
    r = load_route(world, monkeypatch)
    r.step3(None)
    r.step2(None)
    names = {p.name for p in (world / "pipelines" / "router" / "out" / "step2" / "screener").glob("*.json")}
    assert "100.json" in names              # solved stacked task survives the rebuild
    assert "101.json" in names              # an ordinary unpicked screen
    assert "102.json" not in names          # repo already built


def test_pool_excludes_built_and_batched_and_marks_the_source(world, monkeypatch, capsys):
    r = load_route(world, monkeypatch)
    r.step3(None)
    r.step2(None)
    r.pool(None)
    pipe = world / "pipelines" / "router" / "out" / "step2" / "pipeline"
    rows = {x["entry_id"]: x for x in map(json.loads, (pipe / "pool.jsonl").read_text().splitlines())}
    assert set(rows) == {"100", "101"}                                   # 103 is in a batch, 102 is built
    assert all("source" not in x for x in rows.values())                 # the ranking does not see the origin
    src = dict(l.split("\t")[0::2] for l in (pipe / "pool_sources.tsv").read_text().splitlines()[1:])
    assert src == {"100": "solved stacked task", "101": "step-2 screen"}
    assert "in a batch" in (pipe / "pool_excluded.tsv").read_text()
    assert "1 from solved stacked tasks" in capsys.readouterr().out
