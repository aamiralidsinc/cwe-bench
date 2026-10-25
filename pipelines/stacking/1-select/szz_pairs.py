#!/usr/bin/env python3
"""Step 1c of the stacking pipeline: SZZ check of fix-of-fix pairs (STACKING-EXPLORATION.md §8, H3a/H3b).

For each H3b pair (earlier fix A, later fix B, same repo): take the lines B's fix deletes or changes,
blame them in B's parent, and count how many were written by A's fix commits.
  H3a   (regression)      : at least half of B's changed lines come from A's fix (B corrects code A wrote)
  H3b1  (incomplete, touches A's code): some, but under half
  H3b2  (incomplete, elsewhere): none (A was incomplete; B adds protection elsewhere)
  H3u   (unclassified)    : B only adds lines, so SZZ cannot attribute (read by hand)
Clones are blobless and cached in ~/.tb-graders/cwe/stacking/clones/ (network: github.com only).

  python3 -I pipelines/stacking/1-select/szz_pairs.py [--limit N] [--only owner/repo ...] [--max-repo-mb 1500]
Output: pipelines/stacking/out/szz_pairs.tsv (append-safe; already-done pairs are skipped), progress on stderr.
"""
import argparse, csv, os, re, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
OUT = str(paths.STACKING_OUT)
CLONES = os.path.expanduser("~/.tb-graders/cwe/stacking/clones")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@")
COLS = ["b", "a", "repo", "status", "b_changed_lines", "blamed_to_a", "share_a", "blamed_commits", "files", "note"]


def git(repo_dir, *args, timeout=600):
    r = subprocess.run(["git", "-C", repo_dir, *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, r.stdout, r.stderr


GIANTS = {"liferay/liferay-portal"}   # known multi-GB histories; skipped without cloning
META = os.path.expanduser("~/.tb-graders/cwe/sourcer-data/repo-meta")


def ensure_clone(repo, max_mb):
    d = os.path.join(CLONES, repo.replace("/", "__"))
    if repo in GIANTS:
        return None, "known giant repo, skipped"
    mp = os.path.join(META, repo.replace("/", "__") + ".json")
    if os.path.isfile(mp):
        try:
            import json
            kb = json.load(open(mp)).get("size_kb") or 0
            if kb / 1000 > max_mb:
                return None, f"repo ~{kb/1000:.0f} MB (cached metadata) over cap"
        except Exception:
            pass
    if os.path.isdir(os.path.join(d, ".git")) or os.path.isfile(os.path.join(d, "HEAD")):
        return d, None
    os.makedirs(CLONES, exist_ok=True)
    r = subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout",
                        f"https://github.com/{repo}.git", d], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    if r.returncode != 0:
        return None, "clone failed: " + r.stderr.strip()[:120]
    size = sum(os.path.getsize(os.path.join(p, f)) for p, _, fs in os.walk(d) for f in fs) / 1e6
    if size > max_mb:
        return None, f"repo {size:.0f} MB over cap"
    return d, None


def full_sha(d, short):
    rc, out, _ = git(d, "rev-parse", "--verify", "--quiet", short + "^{commit}")
    return out.strip() if rc == 0 else None


def changed_old_lines(d, sha):
    """{path: [old line numbers deleted or changed]} for one fix commit vs its first parent."""
    rc, out, _ = git(d, "diff", "--unified=0", "--no-color", "--no-renames", f"{sha}^", sha, timeout=900)
    res, path = {}, None
    if rc != 0:
        return res
    for line in out.splitlines():
        if line.startswith("--- "):
            path = None if line[4:] == "/dev/null" else line[6:] if line.startswith("--- a/") else None
        m = HUNK.match(line)
        if m and path:
            start, cnt = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
            if cnt > 0 and not re.search(r"(^|/)(tests?|spec|__tests__|testdata)(/|$)|_test\.|\.test\.|\.spec\.|CHANGELOG|\.md$"
                                         r"|(^|/)(dist|build|vendor|node_modules|third_party)/|\.min\.|\.map$"
                                         r"|(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|go\.sum|Cargo\.lock|composer\.lock|poetry\.lock)$", path):
                lst = res.setdefault(path, [])
                lst.extend(range(start, start + cnt))
                del lst[200:]   # cap per file: generated or huge rewrites make blame crawl on blobless clones
    return res


def blame(d, sha, path, lines):
    authors = {}
    for i in range(0, len(lines), 50):
        args = ["blame", "--porcelain"]
        for n in lines[i:i + 50]:
            args += ["-L", f"{n},{n}"]
        rc, out, _ = git(d, *args, f"{sha}^", "--", path, timeout=900)
        if rc != 0:
            continue
        for l in out.splitlines():
            m = re.match(r"^([0-9a-f]{40}) \d+ \d+", l)
            if m:
                authors[m.group(1)] = authors.get(m.group(1), 0) + 1
    return authors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--max-repo-mb", type=float, default=1500)
    a = ap.parse_args()
    pairs = [r for r in csv.DictReader(open(os.path.join(OUT, "h3b_pairs.tsv")), delimiter="\t") if r["status"] == "ready"]
    if a.only:
        pairs = [p for p in pairs if p["repo"] in a.only]
    out_path = os.path.join(OUT, "szz_pairs.tsv")
    done = set()
    if os.path.isfile(out_path):
        done = {(r["b"], r["a"]) for r in csv.DictReader(open(out_path), delimiter="\t")}
    else:
        open(out_path, "w").write("\t".join(COLS) + "\n")
    todo = [p for p in pairs if (p["b"], p["a"]) not in done]
    if a.limit:
        todo = todo[: a.limit]
    t0 = time.time()
    for i, p in enumerate(todo, 1):
        repo = p["repo"].split(";")[0]
        row = dict(b=p["b"], a=p["a"], repo=repo, status="", b_changed_lines=0, blamed_to_a=0, share_a="",
                   blamed_commits=0, files=0, note="")
        try:
            d, err = ensure_clone(repo, a.max_repo_mb)
        except Exception as e:          # one bad repo must not stop the run
            d, err = None, f"error: {type(e).__name__}: {str(e)[:100]}"
        if not d:
            row.update(status="skipped", note=err)
        else:
            a_fix = {full_sha(d, c) for c in p["a_fix"].split(";") if c} - {None}
            b_fix = [s for s in (full_sha(d, c) for c in p["b_fix"].split(";") if c) if s]
            if not a_fix or not b_fix:
                row.update(status="skipped", note="fix commit not in clone (fork or rewritten history)")
            else:
              try:
                total, to_a, commits, files = 0, 0, {}, 0
                for sha in b_fix:
                    for path, lines in changed_old_lines(d, sha).items():
                        files += 1
                        for c, n in blame(d, sha, path, lines).items():
                            total += n
                            commits[c] = commits.get(c, 0) + n
                            if c in a_fix:
                                to_a += n
                share = to_a / total if total else 0
                status = ("H3u" if total == 0 else "H3a" if share >= 0.5 else
                          "H3b1" if to_a else "H3b2")
                row.update(status=status, b_changed_lines=total, blamed_to_a=to_a, share_a=f"{share:.2f}",
                           blamed_commits=len(commits), files=files)
              except Exception as e:      # one bad pair must not stop the run
                row.update(status="error", note=f"{type(e).__name__}: {str(e)[:100]}")
        with open(out_path, "a") as o:
            o.write("\t".join(str(row[c]).replace("\t", " ") for c in COLS) + "\n")
        print(f"[{i}/{len(todo)} {time.time()-t0:.0f}s] {repo} {p['b']} -> {row['status']} {row['note']}",
              file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
