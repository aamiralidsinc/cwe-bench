"""notes_filter.py: earlier conclusions go, how the task is built stays (owner 2026-10-28)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import notes_filter as nf  # noqa: E402

NOTES = """# x build notes

## Levers (one line each)
- T1 published fix site: pkg/a.go:12, covered by security/test_a.py::test_one.
- T2 injected sibling at pkg/b.go:40 (planted; reason to dismiss: legacy path).

### Recurring trust decision
The handler makes one trust decision per request; T3 sits on it.

## Gate results
static: only the missing blind patch and FAIRNESS.md; nop PASS; oracle PASS (3 runs).

## Trial environment
The verifier starts MariaDB as `mysql`; tests run `DROP TABLE t` on a scratch database.

```
reward 1.0 in the oracle log; deepseek r1 is a fixture name here
```

## 2026-10-16 test repair (user-approved)
| Item | Decision | Reason |
|---|---|---|
| SCP traversal (REC mimo-r1-n001) | **fixed**: new `test_scp_download_absolute_path`. |
| "-1 packet size" audit note (REC deepseek-r11-n001) | **lenient, fixed**. |
- **Upload tests demand exactly 403** (REC mimo-r11): fixed with the any-4xx helper. Not unfair: the rule says 4xx.

### Regrade (saved final code)
| deepseek r12 X2oZisd | 1.0 | 1.0 |

## 2026-10-16 audit finding on DeepSeek r12 (decision for the user)
r12 scored 1.0 (17/17). The post-run audit judged it untrusted.

## Client audit PO-3 (2026-10-28)
CLIENT-AUDIT: WITHDRAW

## Verified
- Pinned tree: security 0/10, functional 9/9. Both models solve nothing here is not a run claim.
- Earlier runs were audited fair, so nothing changed. The oracle passes.
"""


def test_conclusion_sections_go_whole():
    res, dropped, n, removed = nf.strip_conclusions(NOTES)
    assert dropped == ["Regrade (saved final code)", "2026-10-16 audit finding on DeepSeek r12 (decision for the user)",
                       "Client audit PO-3 (2026-10-28)"]
    for gone in ("X2oZisd", "untrusted", "CLIENT-AUDIT", "17/17"):
        assert gone not in res


def test_build_facts_stay_including_product_words():
    res = nf.strip_conclusions(NOTES)[0]
    for kept in ("T1 published fix site: pkg/a.go:12", "T2 injected sibling", "### Recurring trust decision",
                 "one trust decision per request", "static: only the missing blind patch and FAIRNESS.md",
                 "`DROP TABLE t`", "## Trial environment", "reward 1.0 in the oracle log; deepseek r1 is a fixture",
                 "security 0/10, functional 9/9", "The oracle passes."):
        assert kept in res, kept


def test_change_logs_keep_what_changed_and_lose_the_conclusions():
    res, _d, _n, removed = nf.strip_conclusions(NOTES)
    assert "## 2026-10-16 test repair\n" in res                      # "(user-approved)" left out of the heading
    assert "| SCP traversal | **fixed**: new `test_scp_download_absolute_path`. |" in res
    assert "packet size" not in res and "lenient" not in res
    assert "- **Upload tests demand exactly 403**: fixed with the any-4xx helper." in res
    assert "Not unfair" not in res and "audited fair" not in res
    assert any("mimo-r1-n001" in r for r in removed)


def test_main_writes_a_copy(tmp_path):
    src, out = tmp_path / "notes.md", tmp_path / "notes.for-review.md"
    src.write_text(NOTES)
    assert nf.main(["x", str(src), str(out)]) == 0
    assert out.read_text() == nf.strip_conclusions(NOTES)[0]
    assert nf.main(["x", str(tmp_path / "missing.md"), str(out)]) == 0 and out.read_text() == ""
