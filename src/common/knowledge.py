"""Run-over-run learning: outcome log, human-readable results.md, and an auto-maintained lessons file.

  data/knowledge/task_outcomes.jsonl   one row per task per stage outcome (machine readable)
  data/knowledge/results.md            append-only log: every stage-4/5 run with a per-task table
  skills/lessons_learned.md            distilled "do / avoid" guidance; the task generator reads it every time
  skills/task_design_techniques.md     hand-curated task-design rules (failure definition, techniques); also in the prompt

The lessons file is rewritten by an Opus call (`update_lessons`) from the accumulated outcomes, so what DeepSeek / MiMo
solve (task too easy) or what the rubric/oracle rejects feeds straight back into the next generation round.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

from src.common.config import Config
from src.common.llm import CliBackend

log = logging.getLogger(__name__)

LESSONS_NAME = "lessons_learned.md"
TECHNIQUES_NAME = "task_design_techniques.md"
MAX_LESSONS_CHARS = 8000
MAX_TECHNIQUES_CHARS = 9000
LESSONS_SECTIONS = ("## Breaks BOTH models (replicate)", "## Breaks only DeepSeek (MiMo solves)",
                    "## Breaks only MiMo (DeepSeek solves)", "## Solved by both (avoid)",
                    "## Task-quality pitfalls (rubric / oracle failures)", "## Selection hints")
LESSONS_MAX_TOKENS = 12000


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def knowledge_dir(cfg: Config) -> Path:
    d = cfg.data_dir / "knowledge"
    d.mkdir(parents=True, exist_ok=True)
    return d


def lessons_path(cfg: Config) -> Path:
    return cfg.root / "skills" / LESSONS_NAME


def task_features(cfg: Config, osv_id: str) -> dict[str, Any]:
    """Static facts about a task from the mined/screened records."""
    rec: dict[str, Any] = {}
    for rel in ("01_mined/osv_candidates.json", "02_screened/screened.json"):
        p = cfg.data_dir / rel
        if p.is_file():
            try:
                for v in json.loads(p.read_text()).get("vulnerabilities", []):
                    if v.get("osv_id") == osv_id:
                        rec.update(v)
            except (OSError, json.JSONDecodeError):
                pass
    scr = (rec.get("screening") or {}).get("diff", {})
    return {
        "cwe_ids": rec.get("cwe_ids"), "ecosystem": rec.get("ecosystem"), "package": rec.get("package"),
        "repo": (rec.get("repo_url") or "").removeprefix("https://github.com/"), "sources": rec.get("sources"),
        "severity": rec.get("severity"), "source_files": len(scr.get("source_files", [])) or None,
        "source_lines": scr.get("source_lines"), "source_dirs": len(scr.get("source_dirs", [])) or None,
    }


def record_outcome(cfg: Config, osv_id: str, stage: str, status: str, detail: str = "", **extra: Any) -> None:
    row = {"ts": _now(), "osv_id": osv_id, "stage": stage, "status": status, "detail": detail[:600],
           **task_features(cfg, osv_id), **extra}
    try:
        with open(knowledge_dir(cfg) / "task_outcomes.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as e:
        log.warning("Cannot write outcome row", extra={"error": str(e)})


def load_outcomes(cfg: Config, limit: Optional[int] = None) -> list[dict]:
    p = knowledge_dir(cfg) / "task_outcomes.jsonl"
    if not p.is_file():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:] if limit else rows


def append_results(cfg: Config, title: str, columns: list[str], rows: list[list[Any]], notes: str = "") -> None:
    """Append a dated section with a markdown table to data/knowledge/results.md."""
    path = knowledge_dir(cfg) / "results.md"
    new = not path.exists()
    esc = lambda x: str(x if x is not None else "").replace("|", "\\|").replace("\n", " ")[:160]
    lines = []
    if new:
        lines += ["# CWE-Bench run results", "",
                  "Append-only log written by the pipeline. Machine-readable twin: `task_outcomes.jsonl`. "
                  "Distilled guidance: `skills/lessons_learned.md`.", ""]
    lines += [f"## {_now()} - {title}", ""]
    if notes:
        lines += [notes, ""]
    if rows:
        lines += ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
        lines += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows]
        lines.append("")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def model_verdicts(per_model: dict[str, dict], timeout_policy: str = "exclude") -> dict[str, str]:
    """tag -> 'solved' (some attempt got full reward) | 'failed' (graded, never solved) | 'timed_out' (every unsolved
    graded attempt hit the time limit; not a failure under TIMEOUT_POLICY=exclude) | 'unknown' (only errors/no data)."""
    out = {}
    for tag, st in per_model.items():
        fails = [a for a in st.get("attempts", []) if a.get("outcome") == "fail"]
        if st.get("passes"):
            out[tag] = "solved"
        elif fails and timeout_policy == "exclude" and all(a.get("timed_out") for a in fails):
            out[tag] = "timed_out"
        elif st.get("fails"):
            out[tag] = "failed"
        else:
            out[tag] = "unknown"
    return out


def pattern_of(verdicts: dict[str, str]) -> str:
    """both_fail (the target) | both_solve | only_<tag>_fails (that model fails, the other solves) |
    <tag>_fails_<other>_timed_out | <tag>_timed_out_<other>_solves | unknown."""
    solved = [t for t, v in verdicts.items() if v == "solved"]
    failed = [t for t, v in verdicts.items() if v == "failed"]
    timed = [t for t, v in verdicts.items() if v == "timed_out"]
    if len(failed) == len(verdicts) and failed:
        return "both_fail"
    if len(solved) == len(verdicts) and solved:
        return "both_solve"
    if solved and failed and len(solved) + len(failed) == len(verdicts):
        return "only_" + "_".join(failed) + "_fails"
    if failed and timed and len(failed) + len(timed) == len(verdicts):
        return "_".join(failed) + "_fails_" + "_".join(timed) + "_timed_out"
    if timed and solved and len(timed) + len(solved) == len(verdicts):
        return "_".join(timed) + "_timed_out_" + "_".join(solved) + "_solves"
    return "unknown"


def task_profile(cfg: Config, osv_id: str, eval_dir: Path) -> dict[str, Any]:
    """Task type + each model's deterministic result ('how it failed'), for the outcome log and the lessons."""
    try:
        from src.common.results_report import MODELS, model_result, task_type
        tt = task_type(cfg, osv_id)
        res = {tag: {k: v for k, v in model_result(eval_dir / tag).items() if k in ("verdict", "cell", "how")}
               for tag, _ in MODELS}
        return {"task_type": tt["label"], "entry_point": tt["entry_point"][:200], "model_results": res}
    except Exception as e:      # reporting detail only; never block a verdict
        log.warning("Task profile failed", extra={"osv_id": osv_id, "error": repr(e)[:200]})
        return {}


def load_priors(cfg: Config) -> dict[str, Any]:
    """Historical both_fail rate per CWE (stage-5 outcomes with a known pattern). Used to rank screening candidates."""
    per: dict[str, list[int]] = {}
    total = hits = 0
    latest: dict[str, dict] = {}
    for r in load_outcomes(cfg):
        if r.get("stage") == "stage5_evaluator" and r.get("pattern") and r["pattern"] != "unknown":
            latest[r["osv_id"]] = r
    for r in latest.values():
        hit = int(r["pattern"] == "both_fail")
        total += 1
        hits += hit
        for cwe in r.get("cwe_ids") or []:
            n = per.setdefault(cwe, [0, 0])
            n[0] += 1
            n[1] += hit
    return {"per_cwe": per, "overall": (hits / total) if total else None, "n": total}


def prior_bonus(priors: dict[str, Any], rec: dict) -> int:
    """Screening score adjustment in [-10, +15] from how often this CWE produced tasks that broke BOTH models (n >= 3)."""
    base = priors.get("overall")
    rates = [h / n for cwe in (rec.get("cwe_ids") or []) for n, h in [priors["per_cwe"].get(cwe, [0, 0])] if n >= 3]
    if base is None or not rates:
        return 0
    return max(-10, min(15, round(25 * (sum(rates) / len(rates) - base))))


def learned_ranking(cfg: Config) -> dict[str, Any]:
    """What the evaluations so far say about candidate SELECTION: per vulnerability family and per package/repo,
    how many evaluated tasks there were and in how many some model failed (a counted failure)."""
    from src.common.results_report import MODELS, collect
    fam: dict[str, list[int]] = {}
    pkg: dict[str, list[int]] = {}
    meta = {}
    for rel in ("01_mined/osv_candidates.json", "02_screened/screened.json"):
        p = cfg.data_dir / rel
        if p.is_file():
            try:
                meta.update({v["osv_id"]: v for v in json.loads(p.read_text()).get("vulnerabilities", [])})
            except (OSError, json.JSONDecodeError, KeyError):
                pass
    for r in collect(cfg):
        broke = int(any(r["per"][t]["verdict"] in ("failed", "failed+timed_out") for t, _ in MODELS))
        graded = any(r["per"][t]["graded"] for t, _ in MODELS)
        if not graded:
            continue
        for f in r["type"]["family"].split(" + "):
            n = fam.setdefault(f, [0, 0]); n[0] += 1; n[1] += broke
        m = meta.get(r["task"], {})
        for key in {(m.get("package") or "").lower(), (m.get("repo_url") or "").lower().rstrip("/")} - {""}:
            n = pkg.setdefault(key, [0, 0]); n[0] += 1; n[1] += broke
    return {"family": fam, "package": pkg}


def selection_adjustment(learned: dict[str, Any], rec: dict) -> tuple[int, str]:
    """Score adjustment in [-30, +30] for a screened candidate, with the reason (logged with the pick)."""
    from src.common.results_report import cwe_family
    why, adj = [], 0.0
    fams = [f for f in cwe_family(rec.get("cwe_ids") or []).split(" + ") if f]
    fadj = []
    for f in fams:
        n, broke = learned["family"].get(f, [0, 0])
        if n >= 3:
            v = 25 * broke / n - (15 if broke == 0 and n >= 4 else 0)
            fadj.append(v)
            why.append(f"{f}: {broke}/{n} broke a model")
    if fadj:
        adj += sum(fadj) / len(fadj)
    seen = [learned["package"].get(k) for k in {(rec.get("package") or "").lower(),
                                                 (rec.get("repo_url") or "").lower().rstrip("/")} - {""}]
    seen = [s for s in seen if s]
    if seen:
        n = max(s[0] for s in seen); broke = max(s[1] for s in seen)
        adj += 5 if broke else -15
        why.append(f"same package/repo: {broke}/{n} broke a model")
    return max(-30, min(30, round(adj))), "; ".join(why)


MAX_ANALYSIS_CHARS = 7000
ANALYSIS_KEEP = ("#### Weakness", "#### Task-design lessons")


def failure_analysis_lessons(cfg: Config) -> str:
    """From each curated data/knowledge/failure_analyses/<osv_id>.md: its title line plus the weakness and task-design
    lesson sections (the per-attempt evidence stays in C_RESULTS.md). Tasks that broke BOTH models come first."""
    d = knowledge_dir(cfg) / "failure_analyses"
    if not d.is_dir():
        return ""
    parts = []
    for f in sorted(d.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("#### Summary")), "")
        summary = ""
        if title:
            summary = text.split("#### Summary", 1)[1].split("\n####", 1)[0].strip()
        keep = [("#### " + sec.split("\n", 1)[0].strip() + "\n" + sec.split("\n", 1)[1].split("\n####", 1)[0].strip())
                for sec in ("\n" + text).split("\n#### ")[1:] if ("#### " + sec).startswith(ANALYSIS_KEEP)]
        if keep:
            both = "both" in summary.lower()[:200]
            parts.append((0 if both else 1, f"## {f.stem}: {summary}\n" + "\n".join(keep)))
    parts.sort(key=lambda p: p[0])
    return "\n\n".join(p for _, p in parts)[:MAX_ANALYSIS_CHARS]


def lessons_for_prompt(cfg: Config) -> str:
    """Text the task generator appends to its prompt: the curated technique guide, then the auto-maintained lessons."""
    out = ""
    tech = cfg.root / "skills" / TECHNIQUES_NAME
    if tech.is_file() and tech.read_text(encoding="utf-8").strip():
        out += ("\n\n# Task-design techniques (curated - follow them)\n"
                + tech.read_text(encoding="utf-8").strip()[:MAX_TECHNIQUES_CHARS] + "\n")
    fmap = knowledge_dir(cfg) / "model_failure_map.md"
    if fmap.is_file() and fmap.read_text(encoding="utf-8").strip():
        out += ("\n\n# Which task types each evaluated agent could not repair completely (measured results)\n"
                + fmap.read_text(encoding="utf-8").strip()[:5000] + "\n")
    board = knowledge_dir(cfg) / "technique_scoreboard.md"
    if board.is_file() and board.read_text(encoding="utf-8").strip():
        out += ("\n\n# Which techniques have broken the evaluated agents so far (measured)\n"
                + board.read_text(encoding="utf-8").strip()[:4000] + "\n")
    lessons = failure_analysis_lessons(cfg)
    if lessons:
        out += ("\n\n# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)\n"
                + lessons + "\n")
    p = lessons_path(cfg)
    text = p.read_text(encoding="utf-8").strip() if p.is_file() else ""
    if text:
        out += ("\n\n# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)\n"
                + text[:MAX_LESSONS_CHARS] + "\n")
    return out


def lessons_problems(text: str) -> list[str]:
    """Why a lessons rewrite must be rejected (empty = OK): it must be complete - start with the first section and
    contain every section in order - and fit the size limit without being cut."""
    problems = []
    if not text.startswith(LESSONS_SECTIONS[0]):
        problems.append(f"does not start with {LESSONS_SECTIONS[0]!r} (starts {text[:40]!r})")
    pos = [text.find(h) for h in LESSONS_SECTIONS]
    missing = [h for h, i in zip(LESSONS_SECTIONS, pos) if i < 0]
    if missing:
        problems.append(f"missing sections {missing}")
    elif pos != sorted(pos):
        problems.append("sections out of order")
    if len(text) > MAX_LESSONS_CHARS:
        problems.append(f"{len(text)} chars > {MAX_LESSONS_CHARS} (would be cut)")
    return problems


LESSONS_PROMPT = """\
You maintain the lessons file of a benchmark factory that builds security-fix tasks. A task is only useful if BOTH target
models (DeepSeek V4.1 Flash = "deepseek", Xiaomi MiMo-V2.6-Pro = "mimo") fail it at pass@3 = 0 for legitimate reasons (not a
broken task). The long-term goal is to make each generation round better than the last: learn WHAT breaks each model and
combine those techniques in new tasks.

Each outcome row has a `pattern`:
  both_fail            both models failed (target) - `technique` says what made it hard
  only_deepseek_fails  DeepSeek failed, MiMo solved - what defeated DeepSeek but not MiMo
  only_mimo_fails      MiMo failed, DeepSeek solved - what defeated MiMo but not DeepSeek
  <a>_fails_<b>_timed_out / <a>_timed_out_<b>_solves   a timeout is NOT a failure; record it as "too slow", not "broken"
  both_solve           too easy - `why_easy` / `technique` explain
`task_type` (vulnerability family; fix breadth) and `model_results` (each model's verdict and how it failed, measured)
say WHICH KIND of task broke WHICH model - a task that broke only one model is still evidence for that model's section.
Other statuses: accepted / rejected_task_defect / needs_review (trial analysis), rejected_rubric / failed_oracle / rejected_unbuildable
(the task itself was bad; `detail` says why). `recall_probe` shows whether the models could name the fix location from the report alone.

Rewrite the lessons file. Rules:
- Evidence only. Cite counts like (n=3); mark anything with n<3 as "tentative".
- Concrete and actionable for an LLM that WRITES the next report and tests: report style, which behaviours/variants the tests
  cover, fix shapes (files, lines, entry-point type), CWE classes, and test-design mistakes the rubric caught.
- For each model, keep a separate list of techniques that broke it, then say which techniques to COMBINE in a single task.
- Add SELECTION hints (CWE / ecosystem / fix shapes to prefer or skip) for the screening step.
- Keep earlier lessons that are still supported; drop ones contradicted by new data; merge duplicates.
- Max ~4500 characters, Markdown, these sections only: "## Breaks BOTH models (replicate)", "## Breaks only DeepSeek (MiMo solves)",
  "## Breaks only MiMo (DeepSeek solves)", "## Solved by both (avoid)", "## Task-quality pitfalls (rubric / oracle failures)",
  "## Selection hints". No preamble.

# Outcome rows (oldest first)
{rows}

# Current lessons file
{current}
"""


def update_lessons(cfg: Config, backend: CliBackend, model: str, max_rows: int = 150) -> bool:
    rows = load_outcomes(cfg, max_rows)
    if not rows:
        return False
    keep = ("osv_id", "stage", "status", "detail", "cwe_ids", "ecosystem", "repo", "source_files", "source_lines",
            "source_dirs", "models", "pattern", "model_verdicts", "technique", "failure_classes", "why_easy", "recall_probe",
            "sources", "task_type", "model_results")
    compact = "\n".join(json.dumps({k: r[k] for k in keep if r.get(k) not in (None, [], {})}, ensure_ascii=False)
                        for r in rows)[:60_000]
    path = lessons_path(cfg)
    current = path.read_text(encoding="utf-8") if path.is_file() else "(none yet)"
    if lessons_problems(current.strip()):          # never feed a damaged file back in as the "current" lessons
        current = "(the previous file was damaged; rebuild every section from the outcome rows)"
    text, usage = backend.complete(model, "You write concise, evidence-backed engineering guidance. Output Markdown only.",
                                   [{"role": "user", "content": LESSONS_PROMPT.format(rows=compact, current=current)}],
                                   LESSONS_MAX_TOKENS)
    text = text.strip()
    problems = lessons_problems(text)
    if (usage or {}).get("output_tokens", 0) >= LESSONS_MAX_TOKENS * 0.98:
        problems.append("output hit the token limit (likely cut)")
    if problems:
        log.warning("Lessons update rejected; keeping the previous file", extra={"problems": problems})
        bad = knowledge_dir(cfg) / "lessons_history" / f"rejected_{time.strftime('%Y%m%d-%H%M%S')}.md"
        bad.parent.mkdir(exist_ok=True)
        bad.write_text(text, encoding="utf-8")
        return False
    hist = knowledge_dir(cfg) / "lessons_history"
    hist.mkdir(exist_ok=True)
    if path.is_file():
        (hist / f"lessons_{time.strftime('%Y%m%d-%H%M%S')}.md").write_text(current, encoding="utf-8")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    tmp.replace(path)
    log.info("Lessons updated", extra={"rows": len(rows), "chars": len(text)})
    return True
