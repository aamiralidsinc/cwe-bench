#!/usr/bin/env python3
"""Leak probe, run INSIDE a task's agent image (as root, read-only use of the image).

Inputs (mounted at /probe): inj.patch (the task's injection patch, may be empty), sol.txt (paths touched by the
reference fix, one per line, relative to /workspace).  Output: one JSON object on stdout.

For each channel it asks: if an agent sorted the starting files by this attribute, would the files the builder
touched come out on top?  precision@k = share of injected files among the k most extreme tracked files
(k = number of injected files), ranks = position of each injected file in that order (0 = most extreme).

Used by common/gate/env_leak_check.py (the gate's leak check and the delivery refusal). From the 2026-10-28
investigation (build/audit/timestamp-leak-20261028/tools/probe.py), plus one channel added at the rollout:
index_mtime_cohort, the file times the git baseline (A6) recorded in .git/index (`git ls-files --debug`). A reset
of the file times alone, without refreshing the index, still leaves the old times readable there.
"""
import json, os, re, subprocess, sys, shutil, hashlib, stat as st

W = "/workspace"
out = {}


def sh(cmd, user=None):
    if user:
        cmd = ["su", user, "-s", "/bin/sh", "-c", cmd]
    else:
        cmd = ["sh", "-c", cmd]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout


patch = open("/probe/inj.patch", errors="replace").read() if os.path.exists("/probe/inj.patch") else ""
inj, new = [], set()
cur_old = None
for line in patch.splitlines():
    if line.startswith("--- "):
        cur_old = line[4:].split("\t")[0].strip()
    elif line.startswith("+++ "):
        p = line[4:].split("\t")[0].strip()
        if p == "/dev/null":
            continue
        p = re.sub(r"^[ab]/", "", p)
        inj.append(p)
        if cur_old == "/dev/null":
            new.add(p)
inj = sorted(set(inj))
sol = [l.strip() for l in open("/probe/sol.txt")] if os.path.exists("/probe/sol.txt") else []
sol = sorted(set(p for p in sol if p))
out["n_injected"] = len(inj)
out["n_new_files"] = len(new)
# the patch may be applied with another -p level or from a sub-folder: strip leading parts until the file exists
STRIP = 0
def _resolve(p):
    parts = p.split("/")
    for k in range(len(parts)):
        q = "/".join(parts[k:])
        if q and os.path.exists(os.path.join(W, q)):
            return q, k
    return None, None
_res = [(p,) + _resolve(p) for p in inj]
_ks = [k for _p, q, k in _res if q is not None]
if _ks:
    STRIP = max(set(_ks), key=_ks.count)
out["extra_strip"] = STRIP
out["injected_missing"] = [p for p, q, k in _res if q is None]
new = {_resolve(p)[0] for p in new if _resolve(p)[0]}
inj = sorted({q for p, q, k in _res if q is not None})

# ---- tracked file set (the A6 baseline) ----
owner = sh(f"stat -c %U {W}").strip() or "root"
git_ok = os.path.isdir(os.path.join(W, ".git"))
tracked = []
if git_ok:
    tracked = [l for l in sh(f"cd {W} && git -c safe.directory='*' ls-files -z", None).split("\0") if l]
if not tracked:
    for root, dirs, files in os.walk(W):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "vendor", "target", ".venv")]
        for f in files:
            tracked.append(os.path.relpath(os.path.join(root, f), W))
out["git_baseline"] = git_ok
out["n_tracked"] = len(tracked)
S = {}
for p in tracked:
    try:
        S[p] = os.lstat(os.path.join(W, p))
    except OSError:
        pass
targets = set(inj)


def rank_channel(key, reverse=True, files=None, targets=targets):
    files = files if files is not None else list(S)
    if not targets or not files:
        return None
    order = sorted(files, key=lambda p: key(S[p]), reverse=reverse)
    k = len(targets)
    top = order[:k]
    pos = {p: i for i, p in enumerate(order)}
    ranks = sorted(pos[p] for p in targets if p in pos)
    return {"precision_at_k": round(sum(p in targets for p in top) / k, 3),
            "max_rank": ranks[-1] if ranks else None, "ranks": ranks[:12],
            "top": order[:min(len(order), k + 3)]}


def cohort(key, SS=None, T=None):
    """distinct values of key (seconds) among tracked files; how many files share each injected file's value.
    pure_recall = share of injected files that sit in a cohort where injected files are at least half the members
    (what `ls -lt` / `find -newer` would show an agent as a separate group)."""
    from collections import Counter
    SS = S if SS is None else SS
    T = targets if T is None else T
    c = Counter(key(s) for s in SS.values())
    if not c or not T:
        return None
    mode_v, mode_n = c.most_common(1)[0]
    inj_vals = sorted(set(key(SS[p]) for p in T if p in SS))
    cohorts, pure = [], 0
    for v in inj_vals:
        members = [p for p, s in SS.items() if key(s) == v]
        ni = sum(m in T for m in members)
        cohorts.append({"value": v, "size": len(members), "injected_in_it": ni, "is_mode": v == mode_v})
        if ni * 2 >= len(members) and v != mode_v:
            pure += ni
    return {"distinct_values": len(c), "mode_value": mode_v, "mode_size": mode_n, "injected_cohorts": cohorts[:10],
            "pure_recall": round(pure / max(1, len([p for p in T if p in SS])), 3)}


out["mtime"] = {"rank": rank_channel(lambda s: s.st_mtime_ns), "cohort": cohort(lambda s: int(s.st_mtime))}


class _M:  # adapter so cohort() can read plain mtimes (ns)
    def __init__(self, ns): self.st_mtime = ns // 10**9


# git index: the A6 baseline stores each file's stat data at `git add` time (read before any git status below,
# which would refresh it)
IX = {}
if git_ok:
    cur = None
    for line in sh(f"cd {W} && git -c safe.directory='*' -c core.quotePath=false ls-files --debug").splitlines():
        if not line.startswith((" ", "\t")):
            cur = line
            continue
        m = re.match(r"\s+mtime:\s*(\d+):", line)
        if m and cur is not None:
            IX[cur] = _M(int(m.group(1)) * 10**9)
out["n_index"] = len(IX)
out["index_mtime_cohort"] = cohort(lambda s: int(s.st_mtime), IX, {p for p in targets if p in IX}) if IX else None
solt = set(p for p in sol if p in S)
out["n_sol_existing"] = len(solt)
out["mtime_sol"] = rank_channel(lambda s: s.st_mtime_ns, targets=solt) if solt else None
out["mtime_sol_cohort"] = cohort(lambda s: int(s.st_mtime), None, solt) if solt else None
out["ctime"] = {"rank": rank_channel(lambda s: s.st_ctime_ns), "cohort": cohort(lambda s: int(s.st_ctime))}
out["atime"] = {"rank": rank_channel(lambda s: s.st_atime_ns), "cohort": cohort(lambda s: int(s.st_atime))}
out["inode"] = {"rank_high": rank_channel(lambda s: s.st_ino), "rank_low": rank_channel(lambda s: s.st_ino, reverse=False)}
out["size_mode_owner"] = cohort(lambda s: f"{s.st_uid}:{s.st_gid}:{oct(s.st_mode)}")
# directories: does the mtime of the containing directories point at injected locations?
dirs = sorted({os.path.dirname(p) for p in S})
D = {}
for d in dirs:
    try:
        D[d] = os.lstat(os.path.join(W, d)).st_mtime_ns
    except OSError:
        pass
idirs = {os.path.dirname(p) for p in targets}
if git_ok:
    # The git baseline (A6) creates .git in the tree root after everything else, so the root folder's mtime is the
    # baseline's time in every task: it says nothing about which files were patched. Left out of T3 (2026-10-28,
    # seen on amqp091-go-s2 after B2b, whose patched files sit in the root).
    D.pop("", None)
    idirs.discard("")
out["dir_mtime_cohort"] = cohort(lambda s: int(s.st_mtime), {d: _M(v) for d, v in D.items()}, idirs) if D else None
if idirs and D:
    order = sorted(D, key=lambda d: D[d], reverse=True)
    k = len(idirs)
    out["dir_mtime"] = {"n_dirs": len(D), "k": k, "precision_at_k": round(sum(d in idirs for d in order[:k]) / k, 3),
                        "top": order[:k + 3]}

# ---- git state as the agent sees it ----
g = {}
if git_ok:
    u = owner if owner != "root" else None
    g["status_lines"] = len([l for l in sh(f"cd {W} && git status --porcelain --ignored=no", u).splitlines() if l])
    g["status_sample"] = sh(f"cd {W} && git status --porcelain | head -5", u).splitlines()
    g["commits"] = len(sh(f"cd {W} && git log --all --oneline", u).splitlines())
    g["reflog"] = len(sh(f"cd {W} && git reflog", u).splitlines())
    g["stash"] = len(sh(f"cd {W} && git stash list", u).splitlines())
    g["branches"] = sh(f"cd {W} && git branch -a", u).split()
    g["log"] = sh(f"cd {W} && git log --all --format='%an|%s'", u).splitlines()[:5]
    # files git thinks are dirty by stat (racy) – index stat info vs file
    g["diff_names"] = sh(f"cd {W} && git diff --name-only HEAD | head -20", u).splitlines()
out["git"] = g

# ---- leftovers ----
lo = sh(f"find {W} -xdev \\( -name node_modules -o -name .git \\) -prune -o -type f \\( -name '*.orig' -o -name '*.rej' "
        f"-o -name '*.bak' -o -name '*~' -o -name '.*.swp' -o -name '*.patch' -o -name '*.diff' \\) -print 2>/dev/null | head -30")
out["leftovers_workspace"] = lo.splitlines()
lo2 = sh("find / -xdev \\( -path /proc -o -path /sys -o -path /probe \\) -prune -o \\( -iname '*inject*' -o -name '*.rej' "
         "-o -name 'fix.patch' -o -name 'manifest.json' -path '*build*' \\) -print 2>/dev/null | grep -v -E "
         "'/node_modules/|site-packages|/usr/(lib|share)/' | head -30")
out["leftovers_fs"] = lo2.splitlines()
out["tmp"] = sh("ls -A /tmp /var/tmp 2>/dev/null | head -20").splitlines()
out["histories"] = sh("ls -la /root/.bash_history /home/*/.bash_history /root/.python_history 2>/dev/null").splitlines()
# string channel: comments in injected files mentioning injection / builder / vulnerable
cm = []
for p in inj:
    try:
        t = open(os.path.join(W, p), errors="replace").read()
    except OSError:
        continue
    for m in re.finditer(r"(?i).{0,40}\b(inject(ed|ion)|seeded|planted|sibling|vulnerab\w*|CWE-\d+|TODO: ?fix|insecure)\b.{0,40}", t):
        cm.append(f"{p}: {m.group(0).strip()}")
out["suspicious_strings"] = cm[:15]

# ---- pristine copies elsewhere on the filesystem (the pre-injection version of a modified file) ----
pc = []
mod = [p for p in inj if p not in new]
if mod and patch:
    tmp = "/tmp/_probe_orig"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    for p in inj:
        os.makedirs(os.path.dirname(os.path.join(tmp, p)), exist_ok=True)
        shutil.copy2(os.path.join(W, p), os.path.join(tmp, p))
    r = None
    for lvl in range(0, 6):                            # the -p level that reverse-applies cleanly
        dry = subprocess.run(["patch", "-R", f"-p{lvl}", "--dry-run", "-s", "-f", "-d", tmp, "-i", "/probe/inj.patch"],
                             capture_output=True, text=True)
        if dry.returncode == 0:
            r = subprocess.run(["patch", "-R", f"-p{lvl}", "-s", "-f", "--no-backup-if-mismatch", "-d", tmp, "-i",
                                "/probe/inj.patch"], capture_output=True, text=True)
            break
    out["reverse_patch_ok"] = bool(r is not None and r.returncode == 0)
    orig_hash = {}
    for p in mod:
        fp = os.path.join(tmp, p)
        if os.path.exists(fp) and out["reverse_patch_ok"]:
            h0 = hashlib.sha256(open(fp, "rb").read()).hexdigest()
            if h0 != hashlib.sha256(open(os.path.join(W, p), "rb").read()).hexdigest():   # only real originals
                orig_hash[h0] = p
    names = {os.path.basename(p) for p in mod}
    expr = " -o ".join(f"-name '{n}'" for n in names)
    cands = sh(f"find / -xdev \\( -path /proc -o -path /sys -o -path /probe -o -path {tmp} \\) -prune -o -type f \\( {expr} \\) -print 2>/dev/null").splitlines()
    for c in cands:
        if c.startswith(W + "/") and os.path.relpath(c, W) in mod:
            continue
        try:
            h = hashlib.sha256(open(c, "rb").read()).hexdigest()
        except OSError:
            continue
        if h in orig_hash:
            pc.append(f"{c} == original of {orig_hash[h]}")
    shutil.rmtree(tmp, ignore_errors=True)
out["pristine_copies"] = pc[:20]
json.dump(out, sys.stdout, default=str)
