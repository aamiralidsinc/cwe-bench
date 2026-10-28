"""cwe_tree_reset: give the agent's starting tree one file time at container start (harness reset, 2026-10-28).

Why. Agent images built before the B2b template (common/builder/templates/environment.Dockerfile) apply
injection.patch in a later RUN than the checkout, so the files the builder changed carry a later mtime/atime, their
folders a later mtime, and the git baseline (A6) records those times in .git/index. An agent that sorts files by time
finds the planted code (reports/reward-hacking.md). The owner chose a harness-level reset for tasks already in
trials (decision 4, option b): it changes no task file and no gate fingerprint.

What. Before the agent starts, in the AGENT container only (never the separate verifier, whose build context is
tests/), ReuseDockerEnvironment.start (cwe_reuse_env.py) runs:
  1. as root, in /workspace (else /app):
       every git-tracked file -> mtime = atime = TREE_EPOCH         (`git ls-files -z | xargs -0 touch -h -c -d @E`)
       every folder of the tree except .git -> the same time        (after the files: copy-up can touch parents)
     A tree without a git baseline: every file and folder, skipping .git, node_modules, vendor, target, .venv.
  2. as the owner of .git: `git update-index -q --refresh`, so the index records the new times, not the old ones.
     Run as the owner, so .git/index keeps its owner.
Only the tracked files are touched: on overlayfs a touch copies the file up into the container layer, so touching
untracked build output (node_modules, target/) would copy gigabytes. ctime becomes "now" for every touched file, in
path order. Not hidden: inode numbers (overlayfs keeps the lower inode), which 11 probed images order by layer.

Nothing is written into the container except the touched times and the refreshed index: no marker file, so the agent
sees no trace of the reset. The result line goes to the trial log (trial.log, "cwe-tree-reset: ...").
CWE_TREE_RESET=0 turns it off. The fixed time equals the template's TREE_EPOCH (2024-01-01T00:00:00Z): in the past,
so build tools never treat a source as newer than its outputs; files the agent edits get the current time.
"""
from __future__ import annotations

import os

TREE_EPOCH = 1704067200          # 2024-01-01T00:00:00Z, the same value as ARG TREE_EPOCH in the B2b template

# Part 1, as root. Prints "root=<dir> owner=<uid>:<gid> files=<n> dirs=<n> mode=<git|walk>" on its last line.
RESET_ROOT_SH = r"""
set -u
E=@%(epoch)d
W=""
for d in /workspace /app; do if [ -d "$d" ]; then W=$d; break; fi; done
[ -n "$W" ] || { echo "cwe-tree-reset: skipped (no /workspace or /app)"; exit 0; }
cd "$W" || exit 3
fail=0
if [ -d .git ] && command -v git >/dev/null 2>&1; then
  mode=git
  nf=$(git -c safe.directory='*' ls-files -z | tr -cd '\0' | wc -c)
  git -c safe.directory='*' ls-files -z | xargs -0 -r touch -h -c -d "$E" -- || fail=1
else
  mode=walk
  nf=$(find . -xdev \( -name .git -o -name node_modules -o -name vendor -o -name target -o -name .venv \) -prune \
       -o ! -type d -print | wc -l)
  find . -xdev \( -name .git -o -name node_modules -o -name vendor -o -name target -o -name .venv \) -prune \
       -o ! -type d -print0 | xargs -0 -r touch -h -c -d "$E" -- || fail=1
fi
nd=$(find . -xdev -name .git -prune -o -type d -print | wc -l)
find . -xdev -name .git -prune -o -type d -print0 | xargs -0 -r touch -h -c -d "$E" -- || fail=1
o=$(stat -c %%u:%%g .git 2>/dev/null || stat -c %%u:%%g . 2>/dev/null || echo 0:0)
echo "root=$W owner=$o files=$nf dirs=$nd mode=$mode fail=$fail"
[ "$fail" = 0 ] || exit 4
"""

# Part 2, as the owner of .git (uid:gid from part 1). Exit 0 also when git reports files whose content changed
# (refresh exits 1 then): the index is refreshed for all others, and a changed file is not ours to judge here.
REFRESH_SH = r"""
cd "%(root)s" || exit 3
[ -d .git ] || exit 0
git update-index -q --refresh >/dev/null 2>&1
rc=$?
[ "$rc" -le 1 ] && echo "index refreshed (rc $rc)" || { echo "index refresh failed (rc $rc)"; exit 5; }
"""


def enabled(environ=None) -> bool:
    return (environ if environ is not None else os.environ).get("CWE_TREE_RESET", "1") != "0"


def root_script(epoch: int = TREE_EPOCH) -> str:
    return RESET_ROOT_SH % {"epoch": int(epoch)}


def refresh_script(root: str) -> str:
    return REFRESH_SH % {"root": root}


def parse_summary(text: str) -> dict:
    """The key=value pairs of part 1's last line (empty when part 1 skipped)."""
    lines = [l for l in (text or "").strip().splitlines() if l.startswith("root=")]
    if not lines:
        return {}
    return dict(kv.split("=", 1) for kv in lines[-1].split() if "=" in kv)


def is_agent_context(environment_dir) -> bool:
    """True for the agent's build context (environment/); False for the separate verifier's (tests/)."""
    from pathlib import Path
    return Path(environment_dir).resolve().name != "tests"
