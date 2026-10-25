#!/usr/bin/env python3
"""Gate fingerprint: a gate pass is valid only for the exact files it gated.

    python3 common/gate/fingerprint.py write <slug>   # gate_one_ds.sh calls this when a task is SOUND
    python3 common/gate/fingerprint.py check <slug>   # exit 0 current, 1 STALE (re-gate first), 2 no fingerprint

What it covers: everything a gate stage reads, i.e. tasks/<slug>/{tests,solution,environment}/ and
build/<slug>/checks/ plus the manifest's patch_checks list. Any change there (fairfix, testfix, upgrade, a
hand repair) can change what nop, oracle or a patch check returns, so the old SOUND no longer proves the
task. instruction.md is NOT covered: no gate stage reads it; an instruction change needs a re-trial instead.

Why (2026-10-25): electron-builder-ds, hubuum-client-rust-ds and mockoon-ds kept a .sound from before the
upgrade that added their deciding tests, and the gap went unnoticed until the quality audit. run_trial.sh
and regrade.py refuse to start on a STALE task. Tasks gated before 2026-10-25 have no fingerprint (exit 2):
they get a warning, not a block, because file dates on the VM are not reliable enough to judge them.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402

SKIP = {".git", "node_modules", "__pycache__", ".pytest_cache"}


def digest(slug):
    t, b = paths.TASKS / slug, paths.BUILD / slug
    h = hashlib.sha256()
    files = []
    for root in (t / "tests", t / "solution", t / "environment", b / "checks"):
        if root.is_dir():
            files += [p for p in root.rglob("*") if p.is_file() and not (SKIP & set(p.parts))]
    for p in sorted(files):
        h.update(str(p.relative_to(paths.ROOT)).encode() + b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest())
    try:
        pc = json.loads((b / "manifest.json").read_text()).get("patch_checks")
    except Exception:
        pc = None
    h.update(json.dumps(pc, sort_keys=True).encode())
    return h.hexdigest(), len(files)


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("write", "check"):
        sys.exit(__doc__)
    cmd, slug = sys.argv[1], sys.argv[2]
    f = paths.BUILD / slug / "gate_fingerprint.json"
    now, n = digest(slug)
    if cmd == "write":
        f.write_text(json.dumps({"slug": slug, "sha256": now, "files": n,
                                 "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=1))
        print(f"{slug}: gate fingerprint {now[:12]} ({n} files)")
        return
    if not f.is_file():
        print(f"{slug}: no gate fingerprint (gated before 2026-10-25); cannot prove the gate is current")
        sys.exit(2)
    rec = json.loads(f.read_text())
    if rec.get("sha256") != now:
        print(f"{slug}: STALE gate: tests/solution/environment/checks changed since the gate passed "
              f"({rec.get('written_utc')}). Re-gate: bash common/gate/gate_one_ds.sh {slug}")
        sys.exit(1)
    print(f"{slug}: gate current ({now[:12]})")


if __name__ == "__main__":
    main()
