#!/bin/bash
# Blind fix for one built task (strict-gate prerequisite): a second complete fix that proves the hidden tests
# accept a correct fix other than the reference. Written with everything in view (owner decision 2026-10-25). The AGENT needs Bash (compile/diff) -> --permission-mode bypassPermissions,
# so a PERSON must launch this script (the orchestrator is blocked from spawning such agents).
#
# Launch through the model driver; there is deliberately no default model, so this can never fall
# back to the capped Claude account:
#     common/launch/drive.sh deepseek bash common/blindfix/run_blindfix.sh <slug>
#
# The blind agent must see the SAME tree a trial agent sees: the product tree of the task's own image
# (upstream + injection + build steps). Until 2026-10-20 it got a fresh upstream clone, so the
# injected sites were missing and blind.patch could never cover them (astro-ds, flyto-core-ds,
# prompty-path-read-inj). The tree now comes from the image, and every patch in environment/ must
# be present in it before the agent starts.
#
# Exit codes (also written to build/<slug>/blind_status.txt):
#   0 blind.patch wired   2 bad input/setup      3 image build or tree extract failed
#   4 injection missing   5 agent failed/no patch 6 blind.patch does not apply to the tree
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
SLUG=${1:?usage: common/blindfix/run_blindfix.sh <slug>}
R="$CWE_ROOT"; ENV="$R/tasks/$SLUG/environment"; B="$R/build/$SLUG"
WORK="$HOME/.tb-graders/cwe/blind/$SLUG"; LOG="$B/blindfix.log"; IMG="cwe-blind-src:$SLUG"
mkdir -p "$B"; : > "$LOG"
log() { echo "[$(date -u +%T)] $SLUG blind: $*" | tee -a "$LOG"; }
die() { log "ERROR($1): $2"; echo "error $1: $2" > "$B/blind_status.txt"; exit "$1"; }
echo "running" > "$B/blind_status.txt"

[ -n "${MODEL:-}" ] || die 2 "MODEL not set; launch via common/launch/drive.sh deepseek bash common/blindfix/run_blindfix.sh $SLUG"
[ -f "$ENV/Dockerfile" ] || die 2 "no $ENV/Dockerfile"
[ -f "$R/tasks/$SLUG/instruction.md" ] || die 2 "no instruction.md"
# The VM builds with DOCKER_BUILDKIT=0, which silently drops heredoc bodies (fission-ds, 2026-10-20).
grep -nE '^[^#]*<<-?[[:space:]]*["'\'']?[A-Za-z_]+' "$ENV/Dockerfile" >/dev/null \
  && die 2 "Dockerfile uses a heredoc; the classic builder drops its body. Move it into a COPY'd file"

log "model=$MODEL; building $IMG from environment/"
docker build -t "$IMG" "$ENV" > "$B/blind-image-build.log" 2>&1 \
  || die 3 "image build failed (build/$SLUG/blind-image-build.log)"

rm -rf "$WORK"; mkdir -p "$WORK/pristine"
cid=$(docker create "$IMG" 2>>"$LOG") || die 3 "docker create $IMG failed"
trap 'docker rm -f "$cid" >/dev/null 2>&1' EXIT
# The product tree is the image's working directory (where a trial agent starts): /workspace for the
# stacking and precision-validation builds, /app for older ones. Until 2026-10-25 this was hard-coded to
# /app, so every /workspace task ended in "error 3: could not extract /app".
SRC=""
for d in "$(docker image inspect -f '{{.Config.WorkingDir}}' "$IMG" 2>/dev/null)" /workspace /app; do
  [ -n "$d" ] && [ "$d" != / ] || continue
  # Count entries with wc (reads the whole stream): head/grep -q would close the pipe early, and under
  # pipefail the SIGPIPE makes an existing tree look empty.
  n_ent=$(docker cp "$cid:$d/." - 2>/dev/null | tar -t 2>/dev/null | wc -l)
  if [ "${n_ent:-0}" -gt 1 ]; then SRC=$d; break; fi
done
[ -n "$SRC" ] || die 3 "no product tree in $IMG (tried the image WORKDIR, /workspace, /app)"
log "product tree: $SRC"
# Dependency and cache dirs stay out: the agent reads source, and diff -ruN must stay fast.
docker cp "$cid:$SRC" - 2>>"$LOG" | tar -x -C "$WORK/pristine" --strip-components=1 \
  --exclude=.git --exclude=node_modules --exclude=.venv --exclude=__pycache__ --exclude='*.pyc' \
  2>>"$LOG" || die 3 "could not extract $SRC from $IMG"
[ -n "$(ls -A "$WORK/pristine")" ] || die 3 "$SRC in $IMG is empty"

# Every patch the environment ships must already be applied in the extracted tree.
n=0
for p in "$ENV"/*.patch "$ENV"/*.diff; do
  [ -f "$p" ] || continue
  if ! patch -p1 -R --dry-run -s -f -d "$WORK/pristine" < "$p" >/dev/null 2>&1 \
     && ! patch -p0 -R --dry-run -s -f -d "$WORK/pristine" < "$p" >/dev/null 2>&1; then
    die 4 "$(basename "$p") is not applied in the image's $SRC; the blind tree would miss it"
  fi
  n=$((n+1))
done
log "tree: $(du -sh "$WORK/pristine" | cut -f1) from $IMG ($(docker image inspect -f '{{.Id}}' "$IMG" | cut -c8-19)); $n environment patch(es) verified present"
if [ "${BLIND_PREPARE_ONLY:-0}" = 1 ]; then echo "prepared" > "$B/blind_status.txt"; log "prepare-only: stopping before the agent"; exit 0; fi

cp -a "$WORK/pristine" "$WORK/app"
cp "$R/tasks/$SLUG/instruction.md" "$WORK/instruction.md"
[ -d "$B/libs" ] && cp -r "$B/libs" "$WORK/libs"
# Full view (owner decision 2026-10-25, BLIND-FIX-BRIEF.md, fairness rule of 2026-10-20): the blind patch is a
# SOUNDNESS control, written with everything in view: hidden tests, reference fix, trap list, build notes.
cp -r "$R/tasks/$SLUG/tests" "$WORK/tests"
cp "$R/tasks/$SLUG/solution/fix.patch" "$WORK/reference.patch" 2>/dev/null || true
[ -f "$B/notes.md" ] && cp "$B/notes.md" "$WORK/build-notes.md"
python3 - "$B/manifest.json" "$WORK/injected-sites.md" <<'PY' || true
import json, sys
m = json.load(open(sys.argv[1]))
lines = ["# Trap list (private; from build/<slug>/manifest.json)", ""]
for t in m.get("traps") or []:
    lines.append(f"- {t.get('id','?')}: {t.get('shape') or t.get('lever') or ''}")
    if t.get("where"): lines.append(f"  where: {t['where']}")
    if t.get("security_tests"): lines.append(f"  security tests: {', '.join(map(str, t['security_tests']))}")
    if t.get("coupled_functional_tests"): lines.append(f"  must keep working: {', '.join(map(str, t['coupled_functional_tests']))}")
open(sys.argv[2], "w").write("\n".join(lines) + "\n")
PY
BRIEF=$(cat "$CWE_BLIND_BRIEF") || die 2 "no common/blindfix/BLIND-FIX-BRIEF.md"
P="$BRIEF

WORK=$WORK . Everything you may use is under \$WORK: instruction.md, app/ (the vulnerable tree; edit it), tests/ (the hidden tests), reference.patch (the reference fix), injected-sites.md (the trap list), build-notes.md, libs/ if present. Do NOT open anything under $R or elsewhere. Write \$WORK/blind.patch and \$WORK/mechanisms.md as the brief says."
date -u +%FT%TZ > "$B/blind_start.txt"
log "agent start"
timeout 5400 "$HOME/.local/bin/claude" -p "$P" --model "$MODEL" \
  --permission-mode bypassPermissions --add-dir "$WORK" \
  --output-format json > "$B/blind-run.json" 2> "$B/blind-run.err"
rc=$?
# Full agent details (result text, errors, stderr tail) -> build/<slug>/blind_status.json.
st=$(python3 "$CWE_AGENT_STATUS" "$B/blind-run.json" "$rc" --details "$B/blind_status.json")
log "agent exit $rc: $st"
# An agent cut off by an API error, quota or crash may leave a half-finished patch; wiring that in
# as an expected-pass fix would mark a fair task unsound (backstage-ds, 2026-10-20).
[ "$st" = ok ] || die 5 "agent did not finish cleanly: $st; its patch is not used"
[ -s "$WORK/blind.patch" ] || die 5 "agent finished but wrote no blind.patch; see build/$SLUG/blind_status.json (agent_result)"

# The gate applies it with patch -p1 inside the product tree: prove that works on a fresh copy of it.
chk=$(mktemp -d); trap 'docker rm -f "$cid" >/dev/null 2>&1; rm -rf "$chk"' EXIT
cp -a "$WORK/pristine" "$chk/t"
patch -p1 --dry-run -f -d "$chk/t" < "$WORK/blind.patch" > "$B/blind-apply-check.log" 2>&1 \
  || die 6 "blind.patch does not apply cleanly to the task tree (build/$SLUG/blind-apply-check.log)"

# Wire the blind patch in (deterministic; not agent work):
cp "$WORK/blind.patch" "$B/checks/blind.patch"
python3 - "$B/manifest.json" "$MODEL" <<'PY' || die 2 "could not update manifest.json"
import json, sys
p, model = sys.argv[1], sys.argv[2]
m = json.load(open(p)); pc = m.setdefault("patch_checks", [])
entry = {"patch": "blind.patch", "expect": "pass", "kind": "blind",
         "why": f"fresh agent ({model}), full view (instruction, tree, tests, reference, trap list)"}
for i, c in enumerate(pc):
    if c.get("patch") == "blind.patch":
        pc[i] = entry
        break
else:
    pc.append(entry)
json.dump(m, open(p, "w"), indent=1)
PY
echo "ok" > "$B/blind_status.txt"
log "blind.patch placed ($(wc -l < "$WORK/blind.patch") lines) and wired as pass/blind"
