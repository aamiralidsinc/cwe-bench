"""Legitimate tool use that must keep working, through the same agent loop."""

from __future__ import annotations

import json
import os
from pathlib import Path

from conftest import (
    FILE_ROOTS_ENV,
    SKILLS_DIR,
    UPLOADS_DIR,
    call_tool,
    call_tool_fresh,
    factor_pair_csv,
    journal_csv,
    ohlcv_csv,
    preview,
    run_route,
    upload,
)


# ---------------------------------------------------------------- uploads

def test_uploaded_text_document_is_readable(env):
    path = upload(b"quarterly note: revenue up 12%\n", "note.txt")
    res = call_tool("read_document", {"file_path": str(path)}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert "revenue up 12%" in res.body["text"]


def test_uploaded_spreadsheet_document_is_readable(env):
    path = upload("ticker,weight\nAAPL,0.4\nMSFT,0.6\n".encode(), "weights.csv")
    res = call_tool("read_document", {"file_path": str(path)}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert "MSFT" in res.body["text"]


def test_upload_area_path_with_dot_segments_staying_inside(env):
    path = upload(b"inside the upload area\n", "inside.txt")
    spelled = str(UPLOADS_DIR) + "/./sub/../" + path.name
    os.makedirs(UPLOADS_DIR / "sub", exist_ok=True)
    res = call_tool("read_document", {"file_path": spelled}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert "inside the upload area" in res.body["text"]


def test_document_in_current_run_workspace_is_readable(env):
    (env.run_dir / "report.md").write_text("# Run report\nSharpe 1.4\n", encoding="utf-8")
    res = call_tool("read_document", {"file_path": str(env.run_dir / "report.md")}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert "Sharpe 1.4" in res.body["text"]


def test_uploaded_trade_statement_is_analysed(env):
    path = upload(journal_csv().encode("utf-8"), "broker.csv")
    res = call_tool("analyze_trade_journal", {"file_path": str(path)}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert res.body["total_records"] == 30


def test_uploaded_trade_statement_builds_shadow_profile(env):
    path = upload(journal_csv().encode("utf-8"), "broker.csv")
    res = call_tool("extract_shadow_strategy", {"journal_path": str(path)}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert res.body["shadow_id"].startswith("shadow_")


# ---------------------------------------------------------------- configured directories

def test_configured_directories_are_readable(env):
    first, second = env.home / "imports-a", env.home / "imports-b"
    first.mkdir()
    second.mkdir()
    (second / "memo.txt").write_text("configured directory memo\n", encoding="utf-8")
    (first / "trades.csv").write_text(journal_csv(), encoding="utf-8")
    roots = {FILE_ROOTS_ENV: f"{first}, {second}"}
    res = call_tool_fresh("read_document", {"file_path": str(second / "memo.txt")}, env.run_dir, **roots)
    assert res.ok, res.raw[:300]
    assert "configured directory memo" in res.body["text"]
    res = call_tool_fresh("analyze_trade_journal", {"file_path": str(first / "trades.csv")}, env.run_dir,
                          **roots)
    assert res.ok, res.raw[:300]


def test_configured_directory_with_home_shorthand(env):
    target = env.home / "broker-exports"
    target.mkdir()
    (target / "memo.txt").write_text("home shorthand memo\n", encoding="utf-8")
    (target / "trades.csv").write_text(journal_csv(), encoding="utf-8")
    roots = {FILE_ROOTS_ENV: "~/broker-exports"}
    res = call_tool_fresh("read_document", {"file_path": str(target / "memo.txt")}, env.run_dir, **roots)
    assert res.ok, res.raw[:300]
    assert "home shorthand memo" in res.body["text"]
    res = call_tool_fresh("analyze_trade_journal", {"file_path": "~/broker-exports/trades.csv"}, env.run_dir,
                          **roots)
    assert res.ok, res.raw[:300]
    assert res.body["total_records"] == 30


# ---------------------------------------------------------------- run workspace

def test_read_file_in_current_run_default_workspace(env):
    (env.run_dir / "notes.md").write_text("alpha beta\n", encoding="utf-8")
    res = call_tool("read_file", {"path": "notes.md"}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert "alpha beta" in res.body["content"]


def test_read_file_with_relative_and_absolute_workspace(env):
    (env.run_dir / "code").mkdir()
    (env.run_dir / "code" / "engine.py").write_text("X = 1\n", encoding="utf-8")
    for run_dir in (".", "code", str(env.run_dir)):
        path = "engine.py" if run_dir == "code" else "code/engine.py"
        res = call_tool("read_file", {"path": path, "run_dir": run_dir}, env.run_dir)
        assert res.ok, (run_dir, res.raw[:300])
        assert "X = 1" in res.body["content"]


def test_read_file_bundled_skill_docs(env):
    skill = next(p for p in sorted(SKILLS_DIR.iterdir()) if (p / "SKILL.md").is_file())
    expected = "".join((skill / "SKILL.md").read_text(encoding="utf-8").splitlines(keepends=True)[:5])
    for path in (f"{skill.name}/SKILL.md", f"skills/{skill.name}/SKILL.md"):
        res = call_tool("read_file", {"path": path, "limit": 5}, env.run_dir)
        assert res.ok, (path, res.raw[:300])
        assert res.body["content"] == expected


def test_write_and_edit_file_in_current_run(env):
    res = call_tool("write_file", {"path": "code/signal_engine.py", "content": "LOOKBACK = 20\n"}, env.run_dir)
    assert res.ok, res.raw[:300]
    target = env.run_dir / "code" / "signal_engine.py"
    assert target.read_text(encoding="utf-8") == "LOOKBACK = 20\n"
    res = call_tool("edit_file", {"path": "code/signal_engine.py", "old_text": "20", "new_text": "30",
                                  "run_dir": str(env.run_dir)}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert target.read_text(encoding="utf-8") == "LOOKBACK = 30\n"


def test_pattern_scan_on_current_run(env):
    arts = env.run_dir / "artifacts"
    arts.mkdir()
    (arts / "ohlcv_DEMO.csv").write_text(ohlcv_csv(), encoding="utf-8")
    res = call_tool("pattern", {"run_dir": str(env.run_dir), "patterns": "peaks_valleys"}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert "DEMO" in res.body["results"]


def test_backtest_runs_in_current_run(env):
    (env.run_dir / "code").mkdir()
    (env.run_dir / "config.json").write_text(json.dumps({"source": "yfinance", "codes": []}),
                                             encoding="utf-8")
    (env.run_dir / "code" / "signal_engine.py").write_text(
        "class SignalEngine:\n    def generate(self, data_map):\n        return {}\n", encoding="utf-8")
    res = call_tool("backtest", {}, env.run_dir)
    assert res.body is not None, res.raw[:300]
    # The engine was started on the workspace: it leaves its process logs there.
    assert (env.run_dir / "logs" / "runner_stdout.txt").exists(), res.raw[:300]


def test_factor_analysis_on_run_artifacts(env):
    f_text, r_text = factor_pair_csv()
    arts = env.run_dir / "artifacts"
    arts.mkdir()
    (arts / "f.csv").write_text(f_text, encoding="utf-8")
    (arts / "r.csv").write_text(r_text, encoding="utf-8")
    out_dir = env.run_dir / "factor_out"
    res = call_tool("factor_analysis", {"factor_csv": str(arts / "f.csv"), "return_csv": str(arts / "r.csv"),
                                        "output_dir": str(out_dir), "n_groups": 4}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert (out_dir / "ic_summary.json").is_file()


def test_factor_analysis_on_uploaded_csvs(env):
    f_text, r_text = factor_pair_csv()
    fpath = upload(f_text.encode(), "factor.csv")
    rpath = upload(r_text.encode(), "returns.csv")
    out_dir = env.run_dir / "factor_out"
    res = call_tool("factor_analysis", {"factor_csv": str(fpath), "return_csv": str(rpath),
                                        "output_dir": str(out_dir), "n_groups": 4}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert (out_dir / "group_equity.csv").is_file()


# ---------------------------------------------------------------- stored-document preview

def test_uploaded_document_can_be_previewed(env):
    path = upload(b"preview body: revenue up 12%\n", "note.txt")
    resp = preview(str(path))
    assert resp.status_code == 200, resp.text[:300]
    assert "revenue up 12%" in resp.text


def test_upload_preview_with_dot_segments_staying_inside(env):
    path = upload(b"inside the upload area\n", "inside.txt")
    os.makedirs(UPLOADS_DIR / "sub", exist_ok=True)
    spelled = str(UPLOADS_DIR) + "/./sub/../" + path.name
    resp = preview(spelled)
    assert resp.status_code == 200, resp.text[:300]
    assert "inside the upload area" in resp.text


# ---------------------------------------------------------------- data inside the run

def test_backtest_data_override_inside_run(env):
    (env.run_dir / "data").mkdir()
    (env.run_dir / "data" / "bars.csv").write_text("close\n101.5\n", encoding="utf-8")
    (env.run_dir / "code").mkdir()
    (env.run_dir / "code" / "signal_engine.py").write_text(
        "class SignalEngine:\n    def generate(self, data_map):\n        return {}\n", encoding="utf-8")
    for local in ("data/bars.csv", str(env.run_dir / "data" / "bars.csv")):
        (env.run_dir / "config.json").write_text(
            json.dumps({"source": "yfinance", "codes": [], "local_data_file": local}), encoding="utf-8")
        res = call_tool("backtest", {}, env.run_dir)
        assert res.body is not None, res.raw[:300]
        assert res.body.get("data_preview"), res.raw[:300]
        assert "101.5" in json.dumps(res.body["data_preview"])


# ---------------------------------------------------------------- skill supporting files

def test_skill_supporting_file_is_loaded(env):
    res = call_tool("load_skill", {"name": "strategy-generate", "file": "examples.md"}, env.run_dir)
    assert res.ok, res.raw[:300]
    assert "Examples" in res.body["content"]
    assert "dual MA crossover" in res.body["content"]


# ---------------------------------------------------------------- shadow account backtest

def test_shadow_backtest_runs_in_its_run_workspace(env):
    path = upload(journal_csv().encode("utf-8"), "broker.csv")
    res = call_tool("extract_shadow_strategy", {"journal_path": str(path)}, env.run_dir)
    assert res.ok, res.raw[:300]
    shadow_id = res.body["shadow_id"]
    res = call_tool("run_shadow_backtest", {"shadow_id": shadow_id, "markets": ["us"],
                                            "window_start": "2026-01-01", "window_end": "2026-03-31"},
                    env.run_dir)
    assert res.ok, res.raw[:300]
    # The application keeps a shadow account's backtest workspace in its own run storage.
    workspace = env.home / ".vibe-trading" / "shadow_runs" / shadow_id
    assert (workspace / "config.json").is_file(), res.raw[:300]
    # The engine was started on that workspace: it leaves its process logs there.
    assert (workspace / "logs" / "runner_stdout.txt").exists(), res.raw[:300]


def test_shadow_backtest_uses_the_recorded_statement_for_attribution(env):
    path = upload(journal_csv().encode("utf-8"), "broker.csv")
    res = call_tool("extract_shadow_strategy", {"journal_path": str(path)}, env.run_dir)
    assert res.ok, res.raw[:300]
    shadow_id = res.body["shadow_id"]
    res = call_tool("run_shadow_backtest", {"shadow_id": shadow_id, "markets": ["us"],
                                            "window_start": "2026-01-01", "window_end": "2026-03-31"},
                    env.run_dir)
    assert res.ok, res.raw[:300]
    # The statement recorded with the profile is inside the upload area, so the
    # attribution that the profile was saved for still runs without re-supplying it.
    assert res.body["attribution"]["counterfactual_trades"], res.raw[:300]


# ---------------------------------------------------------------- stored run routes

def test_run_code_and_pine_routes_serve_a_normal_run(env):
    (env.run_dir / "code").mkdir()
    (env.run_dir / "code" / "signal_engine.py").write_text("LOOKBACK = 20\n", encoding="utf-8")
    (env.run_dir / "artifacts").mkdir()
    (env.run_dir / "artifacts" / "strategy.pine").write_text("//@version=5\n", encoding="utf-8")

    code = run_route(f"{env.run_dir.name}/code")
    assert code.status_code == 200, code.text[:300]
    assert code.json()["signal_engine.py"] == "LOOKBACK = 20\n"
    pine = run_route(f"{env.run_dir.name}/pine")
    assert pine.status_code == 200, pine.text[:300]
    assert "//@version=5" in pine.json()["content"]
