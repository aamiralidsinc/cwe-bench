#!/bin/bash
# Re-apply harbor patch (A): a non-zero exit from `docker compose down` does not fail a run, but is logged.
#
# Why (2026-10-20): a teardown/network-removal race under concurrency failed runs whose tests had already finished,
# so a failed `down` returns instead of raising. Since 2026-10-29 the branch also logs a warning first
# ("compose down failed (rc N), ignored: ..."), in the trial's log: a failed `down` can leave the project's network
# behind, and leaked networks exhausted Docker's address pool (reports/gate-compose-rca-20261029.md). The verdict
# still ignores it.
#
# Idempotent: patches an unpatched docker.py, upgrades the 2026-10-20 silent version, and leaves the logging version
# alone. Writes atomically (a harbor process starting meanwhile reads the old or the new file, never half of one)
# after a backup and an ast check. Running harbor processes keep the code they loaded.
# A harbor reinstall or upgrade reverts this patch: run this script again afterwards.
# Usage (on the VM): bash common/trial/harbor/patch_teardown.sh
#
# (The old part B, a one-time fix to gate_one_ds.sh's stale .sound marker, is in common/gate/gate_one_ds.sh since
# 2026-10-20 and was removed from this script: a release is read-only.)
set -euo pipefail
D="${HARBOR_DOCKER_PY:-$HOME/.local/share/uv/tools/harbor/lib/python3.13/site-packages/harbor/environments/docker/docker.py}"
[ -f "$D" ] || { echo "harbor docker.py not found: $D" >&2; exit 1; }
python3 - "$D" <<'PY'
import ast, os, shutil, sys, tempfile, time
p = sys.argv[1]
s = open(p).read()
head = '''        if check and result.return_code != 0:
'''
silent = '''            if "down" in full_command:
                return result  # teardown is best-effort; a network-removal race must not fail a completed run
'''
logged = '''            if "down" in full_command:
                # patched by common/trial/harbor/patch_teardown.sh: logged, then ignored for the verdict
                self.logger.warning(
                    f"compose down failed (rc {result.return_code}), ignored; the project's network may be left "
                    f"behind: {(result.stdout or '')[-500:]} {(result.stderr or '')[-500:]}"
                )
                return result  # teardown is best-effort; a network-removal race must not fail a completed run
'''
if s.count(head) != 1:
    sys.exit(f"expected exactly one '{head.strip()}', found {s.count(head)}: harbor changed; patch by hand")
if head + logged in s:
    print("already patched (teardown failures logged)"); sys.exit(0)
if head + silent in s:
    s2 = s.replace(head + silent, head + logged, 1); what = "silent teardown patch upgraded to a logged one"
else:
    s2 = s.replace(head, head + logged, 1); what = "teardown patch applied (logged)"
ast.parse(s2)                                   # fail loudly on any syntax error BEFORE writing
bak = p + ".bak-teardown-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
shutil.copy2(p, bak)
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), prefix=".docker.py.")
with os.fdopen(fd, "w") as f:
    f.write(s2)
shutil.copymode(p, tmp)
os.replace(tmp, p)
print(f"patched: {what}; backup {bak}")
PY
grep -n -A4 'if "down" in full_command' "$D" | head -6
