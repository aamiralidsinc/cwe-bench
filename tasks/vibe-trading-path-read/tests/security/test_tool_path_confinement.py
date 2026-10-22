"""Agent tools must not read or modify server files outside the areas they serve.

Every test drives the agent loop with the tool call a prompt-steered model would
make, and asserts the call is refused (a tool error) with no content returned and
no side effect. Private files carry a marker that must never come back.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from conftest import (
    FILE_ROOTS_ENV,
    MARKER,
    RUNS_DIR,
    UPLOADS_DIR,
    call_tool,
    call_tool_fresh,
    factor_pair_csv,
    journal_csv,
    ohlcv_csv,
)


def _private(path: Path, text: str = f"api_key={MARKER}\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _assert_blocked(res, *, marker: str = MARKER) -> None:
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert marker not in res.raw, "private content came back in the tool result"


def _tree(root: Path) -> dict:
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            out[str(p.relative_to(root))] = p.read_bytes() if p.is_file() else None
    return out


# ---------------------------------------------------------------- document reader

def test_document_absolute_path_in_home(env):
    secret = _private(env.home / "private" / "credentials.txt")
    _assert_blocked(call_tool("read_document", {"file_path": str(secret)}, env.run_dir))


def test_document_relative_to_working_directory(env):
    _private(env.proj / "config" / "service.env")
    rel = f"{env.proj.name}/config/service.env"
    _assert_blocked(call_tool("read_document", {"file_path": rel}, env.run_dir))


def test_document_dot_dot_out_of_upload_area(env):
    secret = _private(env.outside / "notes.txt")
    escaping = str(UPLOADS_DIR) + "/" + os.path.relpath(secret, UPLOADS_DIR)
    assert ".." in escaping
    _assert_blocked(call_tool("read_document", {"file_path": escaping}, env.run_dir))


def test_document_symlink_in_upload_area_pointing_outside(env):
    secret = _private(env.outside / "notes.txt")
    link = UPLOADS_DIR / f"vtgrade_{uuid.uuid4().hex[:10]}.txt"
    os.symlink(secret, link)
    env.created.append(link)
    _assert_blocked(call_tool("read_document", {"file_path": str(link)}, env.run_dir))


def test_document_sibling_of_configured_directory(env):
    allowed = env.home / "imports"
    allowed.mkdir()
    secret = _private(env.home / "imports-old" / "notes.txt")
    _assert_blocked(call_tool_fresh("read_document", {"file_path": str(secret)}, env.run_dir,
                                    **{FILE_ROOTS_ENV: str(allowed)}))


# ---------------------------------------------------------------- broker-statement tools

def test_trade_statement_elsewhere_in_home(env):
    journal = env.home / "Documents" / "broker_export.csv"
    journal.parent.mkdir(parents=True)
    journal.write_text(journal_csv(), encoding="utf-8")
    res = call_tool("analyze_trade_journal", {"file_path": str(journal)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert "600519" not in res.raw and "total_records" not in res.raw


def test_trade_statement_home_shorthand(env):
    (env.home / "Desktop").mkdir()
    (env.home / "Desktop" / "trades.csv").write_text(journal_csv(), encoding="utf-8")
    res = call_tool("analyze_trade_journal", {"file_path": "~/Desktop/trades.csv"}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert "total_records" not in res.raw


def test_trade_statement_link_in_upload_area_pointing_into_home(env):
    journal = env.home / "Documents" / "broker_export.csv"
    journal.parent.mkdir(parents=True)
    journal.write_text(journal_csv(), encoding="utf-8")
    link = UPLOADS_DIR / f"vtgrade_{uuid.uuid4().hex[:10]}.csv"
    os.symlink(journal, link)
    env.created.append(link)
    res = call_tool("analyze_trade_journal", {"file_path": str(link)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert "total_records" not in res.raw


def test_trade_statement_relative_to_working_directory(env):
    (env.proj / "exports").mkdir()
    (env.proj / "exports" / "trades.csv").write_text(journal_csv(), encoding="utf-8")
    rel = f"{env.proj.name}/exports/trades.csv"
    res = call_tool("analyze_trade_journal", {"file_path": rel}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert "total_records" not in res.raw


def test_shadow_profile_from_statement_elsewhere_in_home(env):
    journal = env.home / "Downloads" / "broker_export.csv"
    journal.parent.mkdir(parents=True)
    journal.write_text(journal_csv(), encoding="utf-8")
    res = call_tool("extract_shadow_strategy", {"journal_path": str(journal)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    store = env.home / ".vibe-trading" / "shadow_accounts"
    assert not store.exists() or not any(store.iterdir()), "a profile was built from the file"


# ---------------------------------------------------------------- run-workspace tools

def test_read_file_with_workspace_set_to_other_directory(env):
    _private(env.outside / "secrets.txt")
    res = call_tool("read_file", {"path": "secrets.txt", "run_dir": str(env.outside)}, env.run_dir)
    _assert_blocked(res)


def test_read_file_with_relative_workspace_climbing_out(env):
    _private(env.outside / "secrets.txt")
    rel = os.path.relpath(env.outside, env.run_dir)
    assert rel.startswith("..")
    res = call_tool("read_file", {"path": "secrets.txt", "run_dir": rel}, env.run_dir)
    _assert_blocked(res)


def test_read_file_with_workspace_beside_run_storage(env):
    sibling = RUNS_DIR.parent / f"{RUNS_DIR.name}_vtgrade_{uuid.uuid4().hex[:10]}"
    env.created.append(sibling)
    _private(sibling / "secrets.txt")
    res = call_tool("read_file", {"path": "secrets.txt", "run_dir": str(sibling)}, env.run_dir)
    _assert_blocked(res)


def test_write_file_with_workspace_set_to_other_directory(env):
    res = call_tool("write_file", {"path": "code/signal_engine.py", "content": "# vt marker\n",
                                   "run_dir": str(env.outside)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert _tree(env.outside) == {}, "a file was written outside the run workspace"


def test_edit_file_with_workspace_set_to_other_directory(env):
    target = _private(env.outside / "settings.ini", "mode=safe\n")
    res = call_tool("edit_file", {"path": "settings.ini", "old_text": "safe", "new_text": "open",
                                  "run_dir": str(env.outside)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert target.read_text(encoding="utf-8") == "mode=safe\n"
    assert "mode=safe" not in res.raw


def test_pattern_scan_on_other_directory(env):
    arts = env.outside / "artifacts"
    arts.mkdir()
    (arts / "ohlcv_VTPRIV.csv").write_text(ohlcv_csv(), encoding="utf-8")
    res = call_tool("pattern", {"run_dir": str(env.outside)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert "VTPRIV" not in res.raw


def test_backtest_on_other_directory(env):
    (env.outside / "code").mkdir()
    (env.outside / "config.json").write_text(json.dumps({"source": "yfinance", "codes": []}),
                                             encoding="utf-8")
    (env.outside / "code" / "signal_engine.py").write_text(
        "class SignalEngine:\n    def generate(self, data_map):\n        return {}\n", encoding="utf-8")
    before = _tree(env.outside)
    res = call_tool("backtest", {"run_dir": str(env.outside)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert _tree(env.outside) == before, "the backtest ran in (and wrote to) the other directory"


# ---------------------------------------------------------------- factor analysis

def test_factor_inputs_from_home(env):
    f_text, r_text = factor_pair_csv()
    (env.home / "data").mkdir()
    fpath, rpath = env.home / "data" / "f.csv", env.home / "data" / "r.csv"
    fpath.write_text(f_text, encoding="utf-8")
    rpath.write_text(r_text, encoding="utf-8")
    out_dir = env.run_dir / "factor_out"
    res = call_tool("factor_analysis", {"factor_csv": str(fpath), "return_csv": str(rpath),
                                        "output_dir": str(out_dir)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert "ic_mean" not in res.raw
    assert not (out_dir / "ic_series.csv").exists()


def test_factor_output_to_other_directory(env):
    f_text, r_text = factor_pair_csv()
    arts = env.run_dir / "artifacts"
    arts.mkdir()
    (arts / "f.csv").write_text(f_text, encoding="utf-8")
    (arts / "r.csv").write_text(r_text, encoding="utf-8")
    target = env.outside / "report"
    res = call_tool("factor_analysis", {"factor_csv": str(arts / "f.csv"), "return_csv": str(arts / "r.csv"),
                                        "output_dir": str(target)}, env.run_dir)
    assert res.refused, f"expected a tool error, got: {res.raw[:300]}"
    assert not target.exists(), "an output directory was created outside the run storage"
