#!/usr/bin/env python3
"""tree_time_reset.py: insert the B2b file-time reset into an existing environment/Dockerfile (2026-10-28).

    python3 common/builder/tree_time_reset.py <Dockerfile> [--check] [--epoch N]
    python3 common/builder/tree_time_reset.py --postbuild <slug>

Why: a step that edits the source tree after the checkout (injection.patch, sed -i, COPY) leaves the edited files
with their own mtime, so an agent can list the planted code by time (reports/reward-hacking.md). The template's B2b
step gives every file and folder of the tree one fixed time; this script adds the same step to a Dockerfile written
before the template had it.

Where it goes (final build stage only):
  B2 mode    the B2 user step (`RUN ... chown -R agent:agent /home/agent /workspace`) is the last step that writes
             the tree before the git baseline (A6): append `&& find <root> -xdev -exec touch -h -d "@${TREE_EPOCH}" {} +`
             to that RUN, with `ARG TREE_EPOCH=1704067200` before it. Same layer as the chown, which rewrites every
             file anyway: ctime and inode order are hidden too, and the image does not grow. Exactly the template.
  own step   otherwise (no B2, a /app task, or a step writing the tree after B2): one `RUN find <root> -xdev -exec
             touch ...` right before the A6 baseline (or after the last step that writes the tree, without A6), as
             root, restoring the previous USER. It rewrites the whole tree into one more layer (ctime reset too).
root = /workspace or /app, from the chown, the A6 step or the last WORKDIR.

--check: only report (exit 0 already normalised or not applicable, 1 would change). Without it the file is rewritten
in place (no backup in environment/: a new file there would change the build context). Exit 3 = changed, but a step
after the git baseline still writes the tree (needs a person).

--postbuild <slug> (common/gate/postbuild.sh, pipelines/sibling/6-build/resume_pipeline.sh; owner decision 2 of
2026-10-28): run on tasks/<slug>/environment/Dockerfile BEFORE the first gate of an in-flight build. Refuses (no
change, exit 0) when build/<slug>/gate_fingerprint.json exists, because then a change would make the gate stale. The
old Dockerfile is kept as build/<slug>/environment.Dockerfile.pre-b2b; one line goes to build/<slug>/postbuild.log.
Never fails a build: any problem is logged and the exit code is 0.
"""
import argparse
import re
import shutil
import sys
import time
from pathlib import Path

EPOCH = 1704067200
MARK = 'touch -h -d "@${TREE_EPOCH}"'
B2_CHOWN = re.compile(r"chown\s+-R\s+agent:agent\s+(?P<targets>[^;&|\n]*)")
A6 = re.compile(r"git\s+init\b.*Starting project|Starting project.*git\s+init\b", re.S)
# instructions after B2 that the template itself has and that never write the tree
TEMPLATE_SAFE = re.compile(r"claude-code-releases/bootstrap\.sh|ln\s+-sf\s+/home/agent/\.local/bin/claude|"
                           r"claude\s+--version|nodejs\.org/dist|mkdir\s+-p\s+/home/agent|/etc/node-cpu-limit\.js")
# commands that build or install inside the current folder (a RUN with WORKDIR in the tree)
BUILDY = re.compile(r"\b(npm|npx|yarn|pnpm|pip3?|poetry|uv|mvn|mvnw|gradle|gradlew|go|cargo|make|cmake|composer|"
                    r"bundle|rake|dotnet|sbt|ant|tsc|node|python3?|php|ruby|git|cp|mv|tar|unzip|ln|tee)\b|>\s*[^/&\s]")


def instructions(lines):
    """[(keyword, body, first_line, last_line)] with continuation lines joined; comments inside skipped."""
    out, buf, start = [], "", None
    for i, raw in enumerate(lines):
        s = raw.rstrip("\n").rstrip()
        if not buf and (not s.strip() or s.lstrip().startswith("#")):
            continue
        if buf and s.lstrip().startswith("#"):
            continue
        if start is None:
            start = i
        if s.endswith("\\"):
            buf += s[:-1] + " "
            continue
        buf += s
        m = re.match(r"\s*(\w+)\s*(.*)", buf, re.S)
        if m:
            out.append((m.group(1).upper(), m.group(2), start, i))
        buf, start = "", None
    if buf:
        m = re.match(r"\s*(\w+)\s*(.*)", buf, re.S)
        if m:
            out.append((m.group(1).upper(), m.group(2), start, len(lines) - 1))
    return out


def _static():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gate"))
    import static_leak
    return static_leak


def writes_tree(kw, body, root, workdir):
    """True when this instruction may write the source tree."""
    sl = _static()
    if kw in ("COPY", "ADD"):
        parts = [p for p in body.split() if not p.startswith("--")]
        if len(parts) >= 2:
            dest = parts[-1]
            tgt = dest if dest.startswith("/") else str(Path(workdir) / dest)
            return tgt.startswith(root) or tgt in (".", "./")
        return False
    if kw != "RUN" or TEMPLATE_SAFE.search(body):
        return False
    if any(rx.search(body) for _, rx in sl.MOD):
        return True
    return root in body or (workdir.startswith(root) and bool(BUILDY.search(body)))


def plan(text):
    """{'action': none|b2|own, 'why': str, 'root': str, ...} for one Dockerfile's text."""
    lines = text.splitlines(keepends=True)
    ins = instructions(lines)
    froms = [k for k, (kw, *_r) in enumerate(ins) if kw == "FROM"]
    if not froms:
        return {"action": "none", "why": "no FROM"}
    stage = ins[froms[-1]:]
    if any(MARK in body or "TREE_EPOCH" in body for kw, body, *_ in stage if kw == "RUN"):
        return {"action": "none", "why": "already normalised (TREE_EPOCH step present)"}
    a6s = [k for k, (kw, body, *_r) in enumerate(stage) if kw == "RUN" and A6.search(body)]
    a6 = a6s[-1] if a6s else None          # the last baseline is the one the agent sees
    b2 = None
    for k, (kw, body, *_r) in enumerate(stage):
        if a6 is not None and k > a6:
            break
        if kw == "RUN" and not body.lstrip().startswith("[") and B2_CHOWN.search(body):
            tg = B2_CHOWN.search(body).group("targets").split()
            if any(t.rstrip("/") in ("/workspace", "/app") for t in tg):
                b2 = k
    root = None
    if b2 is not None:
        tg = [t.rstrip("/") for t in B2_CHOWN.search(stage[b2][1]).group("targets").split()]
        root = "/workspace" if "/workspace" in tg else "/app"
    if root is None and a6 is not None:
        m = re.search(r"rm\s+-rf\s+(/\S+?)/\.git", stage[a6][1])
        if m:
            root = m.group(1)
    workdir, user = "/", None
    users = []
    for kw, body, *_r in stage:
        if kw == "WORKDIR":
            workdir = body.strip()
            if root is None and workdir.rstrip("/") in ("/workspace", "/app"):
                root = workdir.rstrip("/")
    root = root or "/workspace"
    # anything after B2 (up to A6, or to the end) that writes the tree?
    late = []
    workdir = "/"
    for k, (kw, body, *_r) in enumerate(stage):
        if kw == "WORKDIR":
            workdir = body.strip()
        if b2 is not None and k <= b2:
            continue
        if a6 is not None and k == a6:
            continue
        if writes_tree(kw, body, root, workdir):
            late.append(k)
    after_a6 = [k for k in late if a6 is not None and k > a6]
    if b2 is not None and not [k for k in late if a6 is None or k < a6]:
        return {"action": "b2", "root": root, "line": stage[b2][3], "first": stage[b2][2],
                "why": "append to the B2 step", "after_a6": bool(after_a6)}
    # own step: before A6, else after the last instruction that writes the tree (else at the end)
    if a6 is not None:
        at = stage[a6][2]
        k_at = a6
    else:
        wr = [k for k, (kw, body, *_r) in enumerate(stage) if kw in ("RUN", "COPY", "ADD")]
        last = (late[-1] if late else (wr[-1] if wr else len(stage) - 1))
        at = stage[last][3] + 1
        k_at = last + 1
    for kw, body, *_r in stage[:k_at]:
        if kw == "USER":
            user = body.strip()
    return {"action": "own", "root": root, "insert_at": at, "user": user, "after_a6": bool(after_a6),
            "why": "own step " + ("before the git baseline" if a6 is not None else "after the last tree write")}


def apply(text, epoch=EPOCH):
    """(new_text, plan)."""
    p = plan(text)
    if p["action"] == "none":
        return text, p
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    find = f'find {p["root"]} -xdev -exec {MARK} {{}} +'
    if p["action"] == "b2":
        last = lines[p["line"]].rstrip("\n").rstrip()
        lines[p["line"]] = last + " \\\n" + f"    && {find}\n"
        head = (f"# B2b (added by common/builder/tree_time_reset.py): every file and folder under {p['root']} gets one\n"
                f"# fixed time, so file dates cannot show which files a build step changed. Same RUN as the chown, so\n"
                f"# ctime is uniform too. Never write {p['root']} after this step.\n"
                f"ARG TREE_EPOCH={epoch}\n")
        lines.insert(p["first"], head)
    else:
        u = p.get("user")
        nonroot = u not in (None, "root", "0", "0:0")
        block = (f"# --- B2b (added by common/builder/tree_time_reset.py): one file time for the whole tree -------\n"
                 f"# Every file and folder under {p['root']} gets one fixed time (mtime/atime, and ctime because the\n"
                 f"# whole tree is rewritten into this layer), so file dates cannot show which files a step changed.\n"
                 + ("USER root\n" if nonroot else "") +
                 f"ARG TREE_EPOCH={epoch}\n"
                 f"RUN {find}\n"
                 + (f"USER {u}\n" if nonroot else "") + "\n")
        lines.insert(p["insert_at"], block)
    return "".join(lines), p


def postbuild(slug):
    here = Path(__file__).resolve()
    sys.path.insert(0, str(next(q for q in here.parents if (q / ".cwe-bench-root").is_file()) / "common"))
    import paths
    df = paths.TASKS / slug / "environment" / "Dockerfile"
    b = paths.BUILD / slug
    log = b / "postbuild.log"

    def say(msg):
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {slug} b2b: {msg}"
        print(line)
        try:
            b.mkdir(parents=True, exist_ok=True)
            with open(log, "a") as f:
                f.write(line + "\n")
        except OSError:
            pass

    try:
        if (b / "gate_fingerprint.json").exists():
            say("skipped: the task already has a gate fingerprint (a change would make its gate stale)")
            return 0
        if not df.is_file():
            say(f"skipped: no {df}")
            return 0
        text = df.read_text()
        new, p = apply(text)
        if new == text:
            say(f"no change ({p['why']})")
            return 0
        shutil.copy2(df, b / "environment.Dockerfile.pre-b2b")
        df.write_text(new)
        say(f"inserted the file-time reset ({p['why']}, root {p['root']})"
            + ("; WARNING: a step after the git baseline still writes the tree" if p.get("after_a6") else ""))
        return 0
    except Exception as e:      # never fail a build over this
        say(f"ERROR (not blocking): {type(e).__name__}: {e}")
        return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dockerfile", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--epoch", type=int, default=EPOCH)
    ap.add_argument("--postbuild", metavar="SLUG")
    a = ap.parse_args(argv)
    if a.postbuild:
        return postbuild(a.postbuild)
    if not a.dockerfile:
        ap.error("a Dockerfile or --postbuild SLUG is required")
    df = Path(a.dockerfile)
    text = df.read_text()
    new, p = apply(text, a.epoch)
    if new == text:
        print(f"{df}: no change ({p['why']})")
        return 0
    if a.check:
        print(f"{df}: would change ({p['why']}, root {p['root']})")
        return 1
    df.write_text(new)
    print(f"{df}: changed ({p['why']}, root {p['root']})")
    if p.get("after_a6"):
        print(f"{df}: WARNING: a step after the git baseline still writes the tree; fix it by hand")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
