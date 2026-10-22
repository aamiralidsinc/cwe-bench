import os, shutil, subprocess, sys

B = "/tmp/b"
SRC = "/tmp/src"
OUT = "/tmp/out"
OLD_CHECKS = "/tmp/checks"
FRAG = "packages/astro/src/core/pages/fragment-handler.ts"
RWT = "packages/astro/src/core/rewrites/rewrite-handler.ts"
SKIP = {"blind.patch", "pass_hardening.patch", "pass_alt_fetch_primitives.patch"}

def sh(cmd, cwd=B, check=True):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r

def copy(name, dest):
    shutil.copyfile(f"{SRC}/{name}", f"{B}/{dest}")

def reset():
    sh("git reset -q --hard HEAD && git clean -qfd")
    for root, _dirs, files in os.walk(f"{B}/packages/astro/src"):
        for f in files:
            if f.endswith((".orig", ".rej")):
                os.remove(os.path.join(root, f))

names = sorted(n for n in os.listdir(OLD_CHECKS) if n.endswith(".patch") and n not in SKIP)
for name in names:
    reset()
    r = sh(f"patch -p1 -l -s < {OLD_CHECKS}/{name}", check=False)
    if r.returncode != 0:
        print(f"{name}: APPLY_FAIL {r.stdout[:200]} {r.stderr[:200]}")
        continue
    copy("fragment-handler.fixed.ts", FRAG)
    copy("rewrite-handler.fixed.ts", RWT)
    sh("git add -A")
    sh(f"git diff inj > {OUT}/{name}")
    print(f"{name}: ok {len(open(f'{OUT}/{name}').read().splitlines())} lines")
