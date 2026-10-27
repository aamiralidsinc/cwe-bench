"""pipelines/sibling/4-select/combine.py: several selection passes become one ranking."""
import importlib.util
from pathlib import Path

REPO = next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file())
spec = importlib.util.spec_from_file_location("combine", REPO / "pipelines/sibling/4-select/combine.py")
combine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(combine)


def test_mean_score_with_zero_for_a_pass_that_left_it_out():
    p1 = [{"entry_id": "a", "score": 10, "reason": "r1"}, {"entry_id": "b", "score": 8}]
    p2 = [{"entry_id": "b", "score": 9, "reason": "r2"}, {"entry_id": "c", "score": 9}, {"entry_id": "zz", "score": 10}]
    out = combine.combine({"a", "b", "c"}, [p1, p2])
    assert [r["entry_id"] for r in out] == ["b", "a", "c"]      # b 8.5 (two passes); a 5.0; c 4.5; zz not in pool
    assert out[0]["picked_by"] == 2 and out[0]["reason"] == "r2" and out[0]["scores"] == [8.0, 9.0]


def test_ties_go_to_more_passes_then_better_rank():
    p1 = [{"entry_id": "x", "score": 6}, {"entry_id": "y", "score": 6}]
    p2 = [{"entry_id": "w", "score": 6}, {"entry_id": "x", "score": 6}, {"entry_id": "x", "score": 1}]
    out = combine.combine({"w", "x", "y"}, [p1, p2], top=2)
    assert [r["entry_id"] for r in out] == ["x", "w"]           # x 6.0; w and y 3.0, w ranked first in its pass
