#!/bin/bash
# (A) Harbor: make a compose-DOWN non-zero exit non-fatal (teardown/network-removal race under
#     concurrency must not fail a run whose test already completed during 'up'). Backed up + ast-checked.
# (B) gate_one_ds.sh: fix the stale-marker bug (remove the opposite marker when marking unsound).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
D="$HOME/.local/share/uv/tools/harbor/lib/python3.13/site-packages/harbor/environments/docker/docker.py"
cp "$D" "$D.bak-$(date -u +%Y%m%dT%H%M%SZ)"
python3 - "$D" <<"PY"
import sys, ast
p = sys.argv[1]; s = open(p).read()
old = '''        if check and result.return_code != 0:
            raise RuntimeError('''
new = '''        if check and result.return_code != 0:
            if "down" in full_command:
                return result  # teardown is best-effort; a network-removal race must not fail a completed run
            raise RuntimeError('''
n = s.count(old)
assert n == 1, f"expected exactly 1 match, found {n}"
s2 = s.replace(old, new)
ast.parse(s2)  # fail loudly on any syntax error BEFORE writing
open(p, "w").write(s2)
print("harbor docker.py: patched + ast OK")
PY
echo "--- harbor patch verify ---"; grep -n -A3 "if check and result.return_code != 0:" "$D" | head -6
echo "--- harbor still imports? ---"
( cd "$HOME/.local/share/uv/tools/harbor/lib/python3.13/site-packages" && python3 -c "import ast; ast.parse(open('harbor/environments/docker/docker.py').read()); print('ast OK')" )
cd "$CWE_ROOT"
cp common/gate/gate_one_ds.sh "common/gate/gate_one_ds.sh.bak-$(date -u +%Y%m%dT%H%M%SZ)"
python3 - common/gate/gate_one_ds.sh <<"PY"
import sys
p=sys.argv[1]; s=open(p).read()
old='else touch "build/$s/.unsound"; echo "$s unsound"'
new='else rm -f "build/$s/.sound"; touch "build/$s/.unsound"; echo "$s unsound"'
assert s.count(old)==1, f"gate_one_ds: expected 1 match, found {s.count(old)}"
open(p,"w").write(s.replace(old,new))
print("gate_one_ds.sh: stale-marker bug fixed")
PY
bash -n common/gate/gate_one_ds.sh && echo "gate_one_ds.sh: syntax OK"
grep -n "\.sound\|\.unsound" common/gate/gate_one_ds.sh | tail -2
