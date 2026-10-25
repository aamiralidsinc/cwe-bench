#!/bin/bash
# Re-apply harbor patch (B): the nftables kernel-probe timeout in DockerEnvironment._egress_control_kernel_support().
#
# Why: harbor runs `docker run --rm <probe image>` with timeout=30 before every trial and gate run that uses the
# network allowlist. Under heavy load (load average > ~150) the probe container needs more than 30 s, the probe
# returns False, and harbor refuses the run with "network_mode='allowlist' is not supported by
# EnvironmentType.DOCKER". trial.py records that as "session-ended-early-no-result at ~37s" (ungraded). On
# 2026-10-24 this refused 27 starts. Raising the timeout to 300 s removed it.
#
# A harbor reinstall or upgrade reverts this patch: run this script again afterwards. It is idempotent.
# Usage (on the VM): bash common/trial/harbor/patch_probe_timeout.sh
set -euo pipefail
D="${HARBOR_DOCKER_PY:-$HOME/.local/share/uv/tools/harbor/lib/python3.13/site-packages/harbor/environments/docker/docker.py}"
[ -f "$D" ] || { echo "harbor docker.py not found: $D" >&2; exit 1; }
python3 - "$D" <<'PY'
import ast, re, shutil, sys, time
p = sys.argv[1]
s = open(p).read()
fn = s.find("def _egress_control_kernel_support")
if fn < 0:
    sys.exit("probe function _egress_control_kernel_support not found: harbor changed; patch by hand")
body_end = s.find("\n    def ", fn + 10)
body = s[fn:body_end if body_end > 0 else len(s)]
if re.search(r"timeout=300\b", body):
    print("already patched (timeout=300)"); sys.exit(0)
n = len(re.findall(r"timeout=30,", body))
if n != 1:
    sys.exit(f"expected exactly one 'timeout=30,' in the probe function, found {n}: patch by hand")
new_body = body.replace("timeout=30,", "timeout=300,  # patched by common/trial/harbor/patch_probe_timeout.sh (was 30)", 1)
s2 = s[:fn] + new_body + s[fn + len(body):]
ast.parse(s2)
bak = p + ".bak-probe30-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
shutil.copy2(p, bak)
open(p, "w").write(s2)
print("patched: probe timeout 30 -> 300; backup", bak)
PY
