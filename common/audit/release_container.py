#!/usr/bin/env python3
"""Remove kept trial containers once they are no longer needed for review.

    python3 common/audit/release_container.py list
    python3 common/audit/release_container.py <trial_dir> "<why it can go>"

Before removing, the agent's final code is saved (harvest_code.py) if it was not
already, so only the container and its image are lost, never the evidence. Every
release is appended to build/audit/kept_containers.tsv.
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)
sys.path.insert(0, str(paths.TRIAL_DIR))
from harvest_code import harvest  # noqa: E402
from trial import KEPT, remove_container  # noqa: E402


def kept_now():
    if not KEPT.is_file():
        return {}
    state = {}
    for line in KEPT.read_text().splitlines()[1:]:
        c = line.split("\t")
        state[c[6]] = c if c[1] == "kept" else None
    return {k: v for k, v in state.items() if v}


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        running = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Size}}"],
                                 capture_output=True, text=True).stdout
        status = {l.split("\t")[0]: l.split("\t", 1)[1] for l in running.splitlines()}
        for name, c in kept_now().items():
            print(f"{c[0]}  {c[2]}/{c[3]}  {c[5]}  [{status.get(name, 'GONE')}]  {c[7]}")
        return 0
    trial = Path(sys.argv[1]).resolve()
    why = sys.argv[2] if len(sys.argv) > 2 else "released"
    container = f"{trial.name.lower()}__env-main-1"
    print("code:", harvest(trial, "before-release", container))
    remove_container(container)
    with open(KEPT, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\treleased\t\t\t{trial.parent.name}\t"
                f"{trial.name}\t{container}\t{why}\n")
    print("released", container)
    return 0


if __name__ == "__main__":
    sys.exit(main())
