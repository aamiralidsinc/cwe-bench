"""Stage 2 - Screener: drop junk fixes and repos we cannot build/test.

Input : data/01_mined/osv_candidates.json
Output: data/02_screened/screened.json  (cumulative; same record schema + a `screening` object)
        data/02_screened/rejected.json  {osv_id: [reasons]}

Rules (see skills/adversarial_research.md section 6)
  * fix commit must change >= 1 non-test SOURCE file in a language we can run (PyPI: .py; npm: js/ts family)
  * dependency-only, manifest/lock-only, docs-only and config/CI-only fixes are rejected
  * changed source lines must be within [--min-lines, --max-lines]
  * repo must have a root build manifest and at least one test file at the pre-patch commit
  * at most --max-per-repo tasks per repository (best score kept)

"Buildable" here is a structural check on the pre-patch file tree. A real Docker build happens in stage 4.
Everything is fetched through the GitHub REST API (cached under data/.cache/gh) - no cloning.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Optional

import requests

from src.common.classify import TEST_PATH_RE, classify
from src.common import knowledge
from src.common.config import Config
from src.common.logging_setup import configure_logging
from src.common.state_manager import StateManager, Status
from src.stage1_mining.osv_miner import GitHubResolver, RateLimiter, make_session

log = logging.getLogger(__name__)

STAGE = "stage2_screening"
GITHUB_API = "https://api.github.com"
MAX_FILES_IN_COMMIT_API = 300   # GitHub truncates the files list at 300
MAX_ATTEMPTS = 3
MAX_TOTAL_CHANGED_LINES = 2500   # ~80k chars of diff, the generator's patch limit

ROOT_MANIFESTS = {
    "PyPI": {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"},
    "npm": {"package.json"},
}
TEST_FILE_RE = {
    "PyPI": re.compile(r"(^|/)(test_[^/]+\.py|[^/]+_test\.py|conftest\.py)$"),
    "npm": re.compile(r"(\.(test|spec)\.[cm]?[jt]sx?$)|(^|/)__tests__/|(^|/)(test|tests)/[^/]+\.[cm]?[jt]sx?$"),
}


class TransientError(Exception):
    """GitHub trouble that may succeed on a later run."""


class PermanentError(Exception):
    """Commit/repo is gone or inaccessible."""


@dataclass
class Decision:
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# GitHub access (cached)
# --------------------------------------------------------------------------- #
class GitHubClient:
    def __init__(self, token: Optional[str], rps: float, cache_dir: Path):
        self.session = make_session(token)
        self.limiter = RateLimiter(rps)
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

    def get_json(self, path: str, cache_key: str) -> Any:
        cache = self.cache_dir / f"{cache_key}.json"
        if cache.is_file():
            try:
                return json.loads(cache.read_text())
            except json.JSONDecodeError:
                cache.unlink(missing_ok=True)
        url = f"{GITHUB_API}{path}"
        for attempt in range(4):
            self.limiter.wait()
            try:
                r = self.session.get(url, timeout=45)
            except requests.RequestException as e:
                log.warning("GitHub request failed", extra={"path": path, "error": str(e)})
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200:
                data = r.json()
                tmp = cache.with_suffix(".tmp")
                tmp.write_text(json.dumps(data))
                tmp.replace(cache)
                return data
            if r.status_code in (403, 429) and GitHubResolver._is_rate_limited(r):
                GitHubResolver._sleep_until_reset(r)
                continue
            if r.status_code in (404, 409, 410, 422, 451):
                raise PermanentError(f"HTTP {r.status_code} for {path}")
            time.sleep(2 ** attempt)
        raise TransientError(f"gave up on {path}")


# --------------------------------------------------------------------------- #
# Decision logic (pure, unit-testable)
# --------------------------------------------------------------------------- #
TEMPLATE_RE = re.compile(r"\.(ejs|hbs|handlebars|mustache|jinja2?|j2|njk|tmpl|tpl|liquid|eta)$", re.IGNORECASE)


def summarize_files(files: list[dict], ecosystem: str) -> dict[str, Any]:
    cats: dict[str, list[str]] = defaultdict(list)
    src_lines = 0
    src_dirs: set[str] = set()
    for f in files:
        name = f["filename"]
        cat = classify(name, ecosystem)
        cats[cat].append(name)
        if cat == "source":
            src_lines += int(f.get("additions", 0)) + int(f.get("deletions", 0))
            src_dirs.add(str(PurePosixPath(name).parent))
    return {
        "counts": {k: len(v) for k, v in cats.items()},
        "source_files": cats.get("source", []),
        "test_files": cats.get("test", []),
        "source_lines": src_lines,
        "source_dirs": sorted(src_dirs),
    }


def evaluate_diff(files: list[dict], ecosystem: str, min_lines: int, max_lines: int) -> Decision:
    if len(files) >= MAX_FILES_IN_COMMIT_API:
        return Decision(False, ["diff too large (>= 300 files)"])
    if not files:
        return Decision(False, ["empty diff"])
    s = summarize_files(files, ecosystem)
    counts: Counter = Counter(s["counts"])
    reasons = []
    # Whole-diff size (tests, fixtures, generated files included): the oracle patch must stay reviewable and fit the
    # generation prompt (stage 3 rejects patches over ~80k characters). e.g. a 40-line source fix with a 450k-char diff.
    total_changes = sum(int(f.get("changes", 0) or (int(f.get("additions", 0)) + int(f.get("deletions", 0)))) for f in files)
    s["total_changed_lines"] = total_changes
    if total_changes > MAX_TOTAL_CHANGED_LINES:
        reasons.append(f"whole fix diff too large ({total_changes} changed lines incl. tests/fixtures > {MAX_TOTAL_CHANGED_LINES})")
    if not s["source_files"]:
        non_code = set(counts) <= {"manifest", "docs", "config", "generated", "test"}
        only = set(counts) - {"test"}
        if only and only <= {"manifest"}:
            reasons.append("dependency/manifest-only change")
        elif only and only <= {"docs"}:
            reasons.append("documentation-only change")
        elif non_code:
            reasons.append("non-code change (config/CI/docs/manifest/generated/tests only)")
        else:
            reasons.append(f"no source file in a supported language for {ecosystem}")
    else:
        # A code generator's fix that mostly edits the TEMPLATES of generated code (e.g. EJS producing Java) cannot be
        # exercised through a real entry point offline - only implementation-bound text checks would be possible.
        tmpl = sum(int(f.get("additions", 0)) + int(f.get("deletions", 0)) for f in files
                   if TEMPLATE_RE.search(f["filename"]))
        s["template_lines"] = tmpl
        if tmpl > s["source_lines"]:
            reasons.append(f"fix lives mostly in code-generation templates ({tmpl} template lines > "
                           f"{s['source_lines']} source lines)")
        if s["source_lines"] < min_lines:
            reasons.append(f"trivial fix ({s['source_lines']} source lines < {min_lines})")
        if s["source_lines"] > max_lines:
            reasons.append(f"fix too large ({s['source_lines']} source lines > {max_lines})")
    return Decision(not reasons, reasons, s)


def evaluate_tree(tree: dict, ecosystem: str) -> Decision:
    paths = [e["path"] for e in tree.get("tree", []) if e.get("type") == "blob"]
    root_files = {p for p in paths if "/" not in p}
    reasons, info = [], {"truncated": bool(tree.get("truncated"))}
    manifests = sorted(m for m in root_files if m.lower() in ROOT_MANIFESTS[ecosystem]
                       or (ecosystem == "PyPI" and re.match(r"requirements.*\.txt$", m)))
    info["root_manifests"] = manifests
    if not manifests:
        reasons.append(f"no root build manifest for {ecosystem} (monorepo or unusual layout)")
    n_tests = sum(1 for p in paths if TEST_FILE_RE[ecosystem].search(p))
    info["test_files_in_repo"] = n_tests
    if n_tests == 0 and not info["truncated"]:
        reasons.append("no test files found in repo")
    info["has_dockerfile"] = any(p.lower() == "dockerfile" for p in root_files)
    return Decision(not reasons, reasons, info)


def score(diff: dict[str, Any], tree: dict[str, Any]) -> int:
    """Higher = better candidate for a hard, fair task. Calibrated on the measured results (skills/lessons_learned.md):
    every fix of <= 5 source files was solved by DeepSeek, the only task both models failed spans 8 files / 174 lines /
    4 dirs, and none of the 8 fixes of <= 3 files and <= 35 lines gave a usable task. So: reward breadth (files, dirs =
    layers crossed) up to ~8 files, prefer 100-400 changed lines, and push tiny local fixes to the bottom."""
    files, lines = len(diff["source_files"]), diff["source_lines"]
    dirs = len(diff["source_dirs"]) if diff["source_dirs"] else 0
    sc = 8 * min(files, 8)
    sc += 6 * min(max(dirs - 1, 0), 4)
    sc += 10 if 100 <= lines <= 400 else (5 if 40 <= lines < 100 else 0)
    sc -= 25 if files <= 3 and lines <= 35 else 0
    sc += 3 if tree.get("test_files_in_repo", 0) >= 5 else 0
    return sc


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def screen_one(rec: dict, gh: GitHubClient, min_lines: int, max_lines: int, published_after: str = "",
               prior: Callable[[dict], int] = lambda r: 0, max_repo_mb: int = 0) -> Decision:
    owner_repo = rec["repo_url"].removeprefix("https://github.com/")
    eco = rec["ecosystem"]
    if len(rec.get("fix_commits") or []) > 1:
        # A consecutive fix series: judge the combined change (pre-patch..last fix) and the EARLIEST commit's date.
        commit = gh.get_json(f"/repos/{owner_repo}/compare/{rec['pre_patch_commit']}...{rec['fixed_commit']}",
                             f"compare_{rec['pre_patch_commit'][:12]}_{rec['fixed_commit'][:12]}")
        dates = [d for cm in commit.get("commits", []) for x in ("author", "committer")
                 for d in [((cm.get("commit") or {}).get(x) or {}).get("date")] if d]
    else:
        commit = gh.get_json(f"/repos/{owner_repo}/commits/{rec['fixed_commit']}", f"commit_{rec['fixed_commit']}")
        c = commit.get("commit") or {}   # earlier of author/committer date: a cherry-picked backport keeps its age
        dates = [d for d in ((c.get("author") or {}).get("date"), (c.get("committer") or {}).get("date")) if d]
    commit_date = min(dates or [""])[:10]
    if published_after and commit_date and commit_date < published_after:
        return Decision(False, [f"fix committed {commit_date}, before {published_after} (could be in the models' training data)"])
    d = evaluate_diff(commit.get("files", []), eco, min_lines, max_lines)
    if not d.accepted:
        return d
    repo_info = gh.get_json(f"/repos/{owner_repo}", f"repo_{owner_repo.replace('/', '__')}")
    size_mb = int(repo_info.get("size", 0)) / 1024          # GitHub reports KB (repo incl. history)
    if max_repo_mb and size_mb > max_repo_mb:
        return Decision(False, [f"repo too large for local runs ({size_mb:.0f} MB > {max_repo_mb} MB)"], {"diff": d.info})
    tree = gh.get_json(f"/repos/{owner_repo}/git/trees/{rec['pre_patch_commit']}?recursive=1",
                       f"tree_{rec['pre_patch_commit']}")
    t = evaluate_tree(tree, eco)
    if not t.accepted:
        return Decision(False, t.reasons, {"diff": d.info, "repo": t.info})
    bonus = prior(rec)
    return Decision(True, [], {"diff": d.info, "repo": t.info, "score": score(d.info, t.info) + bonus, "prior": bonus,
                              "fix_commit_date": commit_date})


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise RuntimeError(f"{path} is unreadable; refusing to overwrite: {e}") from e


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    tmp.replace(path)


def apply_repo_cap(records: list[dict], cap: int) -> tuple[list[dict], dict[str, list[str]]]:
    kept, dropped, per_repo = [], {}, Counter()
    for rec in sorted(records, key=lambda r: -r["screening"].get("score", 0)):
        repo = rec["repo_url"].lower()
        if per_repo[repo] >= cap:
            dropped[rec["osv_id"]] = [f"repo cap reached ({cap} per repository)"]
            continue
        per_repo[repo] += 1
        kept.append(rec)
    return kept, dropped


def screen(cfg: Config, args: argparse.Namespace, state: Optional[StateManager]) -> int:
    candidates = load_json(args.input, {}).get("vulnerabilities", [])
    if not candidates:
        log.error("No candidates in %s; run stage 1 first", args.input)
        return 2
    gh = GitHubClient(cfg.github_token, args.github_rps, cfg.cache_dir / "gh")

    todo = [r for r in candidates if not state or state.should_process(STAGE, r["osv_id"], MAX_ATTEMPTS)]
    log.info("Screening", extra={"candidates": len(candidates), "to_screen": len(todo)})

    cutoff = args.published_after or cfg.published_after
    priors = knowledge.load_priors(cfg)
    if cutoff:
        log.info("Recency filter active", extra={"fix_committed_after": cutoff})

    def work(rec: dict) -> tuple[dict, Optional[Decision], Optional[str], bool]:
        if cutoff and (rec.get("published") or "9999")[:10] < cutoff:   # advisory older than cutoff => fix older too
            return rec, Decision(False, [f"advisory published {(rec.get('published') or '?')[:10]}, before {cutoff} "
                                         "(models may remember older CVEs)"]), None, False
        try:
            return rec, screen_one(rec, gh, args.min_lines, args.max_lines, cutoff, lambda r: knowledge.prior_bonus(priors, r),
                                   args.max_repo_mb), None, False
        except PermanentError as e:
            return rec, None, str(e), True
        except TransientError as e:
            return rec, None, str(e), False
        except Exception as e:  # never let one record kill the batch
            log.exception("screen error", extra={"osv_id": rec["osv_id"]})
            return rec, None, f"unexpected: {e!r}", False

    accepted, rejected = [], {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for rec, dec, err, permanent in pool.map(work, todo):
            oid = rec["osv_id"]
            if err:
                rejected_reason = [f"github: {err}"]
                if permanent:
                    rejected[oid] = rejected_reason
                    state and state.mark(STAGE, oid, Status.REJECTED, err)
                else:
                    state and state.mark(STAGE, oid, Status.FAILED, err)
                    log.warning("Transient failure; will retry next run", extra={"osv_id": oid, "error": err})
            elif dec.accepted:
                accepted.append({**rec, "screening": dec.info})
            else:
                rejected[oid] = dec.reasons
                state and state.mark(STAGE, oid, Status.REJECTED, "; ".join(dec.reasons))

    prior = load_json(args.output, {}).get("vulnerabilities", [])
    by_id = {r["osv_id"]: r for r in prior if r["osv_id"] not in rejected}   # a re-screen can revoke earlier passes
    by_id.update({r["osv_id"]: r for r in accepted})
    kept, dropped = apply_repo_cap(list(by_id.values()), args.max_per_repo)

    rejected_all = load_json(args.rejected, {})
    rejected_all.update(rejected)
    rejected_all.update(dropped)
    for oid in dropped:
        state and state.mark(STAGE, oid, Status.REJECTED, dropped[oid][0])
    for r in kept:
        state and state.mark(STAGE, r["osv_id"], Status.DONE, payload={"score": r["screening"].get("score")})

    write_json(args.output, {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                             "count": len(kept), "vulnerabilities": kept})
    write_json(args.rejected, rejected_all)
    reasons = Counter(x.split(" (")[0] for rs in rejected.values() for x in rs)
    log.info("Screening finished", extra={"accepted_total": len(kept), "newly_rejected": len(rejected),
                                          "top_reasons": dict(reasons.most_common(5))})
    return 0 if kept else 1


def parse_args(argv: Optional[list[str]], cfg: Config) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage 2: screen mined candidates")
    p.add_argument("--input", type=Path, default=cfg.data_dir / "01_mined" / "osv_candidates.json")
    p.add_argument("--output", type=Path, default=cfg.data_dir / "02_screened" / "screened.json")
    p.add_argument("--rejected", type=Path, default=cfg.data_dir / "02_screened" / "rejected.json")
    p.add_argument("--min-lines", type=int, default=4)
    p.add_argument("--max-lines", type=int, default=400)
    p.add_argument("--max-per-repo", type=int, default=3)
    p.add_argument("--max-repo-mb", type=int, default=int(__import__("os").environ.get("MAX_REPO_MB", "150")),
                   help="reject repositories larger than this (GitHub size incl. history); 0 = no limit (default 150)")
    p.add_argument("--published-after", metavar="YYYY-MM-DD",
                   help="reject advisories published before this date (older CVEs may be memorised by the target models)")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--github-rps", type=float, default=None)
    p.add_argument("--ignore-state", action="store_true")
    args = p.parse_args(argv)
    if args.github_rps is None:
        args.github_rps = 3.0 if cfg.github_token else 0.5
    return args


def main(argv: Optional[list[str]] = None, cfg: Optional[Config] = None) -> int:
    cfg = cfg or Config.load()
    args = parse_args(argv, cfg)
    if not logging.getLogger().handlers:
        configure_logging()
    if not cfg.github_token:
        log.warning("No GITHUB_TOKEN: 60 GitHub calls/hour; screening will stall on large inputs")
    state = None if args.ignore_state else StateManager(cfg.state_db)
    try:
        return screen(cfg, args, state)
    except KeyboardInterrupt:
        log.error("Interrupted")
        return 130
    except RuntimeError as e:
        log.error("%s", e)
        return 1
    finally:
        if state:
            state.close()


if __name__ == "__main__":
    sys.exit(main())
