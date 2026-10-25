#!/bin/bash
# Informed blind fix: build the INJECTED tree, hand the agent the PRIVATE trap list,
# Opus 5.5 edits every site, diff -> checks/blind.patch. NO tests, NO reference fix seen.
set -uo pipefail
SLUG=$1
R="$HOME/cwe-bench"; DF="$R/tasks/$SLUG/environment/Dockerfile"
LOG="$R/build/$SLUG/blind-informed.log"; : > "$LOG"
URL=$(grep -oE '^ARG REPO_URL=[^ ]+' "$DF" | sed -E 's/^ARG REPO_URL=//; s/"//g' | head -1); URL=${URL%.git}
[ -n "$URL" ] || URL=$(grep -oE 'https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+' "$DF" | head -1 | sed 's/\.git$//')
COMMIT=$(grep -oE '[0-9a-f]{40}' "$DF" | head -1)
INJ=$(ls "$R"/tasks/$SLUG/environment/inject*.patch "$R"/tasks/$SLUG/environment/injection.patch "$R"/tasks/$SLUG/environment/inject-siblings.patch 2>/dev/null | head -1)
echo "[$SLUG] url=$URL commit=${COMMIT:0:12} inj=$(basename "$INJ")" >> "$LOG"
[ -n "$URL" ] && [ -n "$COMMIT" ] && [ -n "$INJ" ] || { echo "[$SLUG] PARSE FAIL" >> "$LOG"; exit 2; }
WORK="$HOME/.tb-graders/cwe/blind-informed/$SLUG"; rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"
git init -q app && ( cd app && git remote add origin "$URL" && git fetch -q --depth 1 origin "$COMMIT" && git checkout -q FETCH_HEAD && rm -rf .git )
( cd app && patch -p1 < "$INJ" ) >> "$LOG" 2>&1 || { echo "[$SLUG] INJECT APPLY FAIL" >> "$LOG"; exit 3; }
( cd app && git init -q . && git add -A && git -c user.email=x@x -c user.name=x commit -qm injected-baseline )
cp "$R/tasks/$SLUG/instruction.md" instruction.md
python3 - "$R/build/$SLUG/manifest.json" > injected-sites.md <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
print("# PRIVATE injected-sibling / route site list — for this soundness fix ONLY\n")
print("Close EVERY site listed below AND the route in instruction.md. A real solver is NOT given this list; you are, so the fix is COMPLETE and scores 1.0. Do not weaken any legitimate behaviour.\n")
for t in m.get("traps",[]):
    print(f"## {t.get('id')}  @ {t.get('where')}")
    print(t.get('shape','')); print()
PY
PROMPT="You are writing a COMPLETE reference-quality security fix for a known vulnerability, as a soundness control (it proves a fully-informed fix passes every hidden test). You are confined to \$WORK=$WORK.

Read ONLY: \$WORK/instruction.md (the vulnerability and the required property) and \$WORK/injected-sites.md (the COMPLETE private list of every site you must fix). Edit the source tree under \$WORK/app to close the reported route AND every site in injected-sites.md, while keeping all legitimate behaviour working.

Rules: Do NOT read, search for, open, or infer the contents of any test files or any reference/solution patch — they are not present and you must not look for them. Do NOT touch anything outside \$WORK. Compile/build the project if the toolchain is available to check your work; if it is not, reason carefully instead. Do NOT create a patch file yourself — just edit files under \$WORK/app. When done, write \$WORK/mechanisms.md briefly describing the fix at each site.

WORK=$WORK"
echo "[$SLUG] launching Opus 5.5 agent $(date -u +%FT%TZ)" >> "$LOG"
date -u +%FT%TZ > "$R/build/$SLUG/blind_informed_start.txt"
timeout 7200 "$HOME/.local/bin/claude" -p "$PROMPT" --model claude-opus-5-5 \
  --permission-mode bypassPermissions --add-dir "$WORK" \
  --output-format json > "$R/build/$SLUG/blind-informed.json" 2> "$R/build/$SLUG/blind-informed.err"
echo "[$SLUG] agent exit $? $(date -u +%FT%TZ)" >> "$LOG"
( cd "$WORK/app" && git add -A && git diff --cached ) > "$WORK/blind.patch" 2>>"$LOG"
if [ -s "$WORK/blind.patch" ]; then
  cp "$WORK/blind.patch" "$R/build/$SLUG/checks/blind.patch"
  echo "[$SLUG] BLIND.PATCH WRITTEN: $(wc -l <"$WORK/blind.patch") lines, $(grep -c '^+++' "$WORK/blind.patch") files -> checks/blind.patch" >> "$LOG"
else echo "[$SLUG] EMPTY PATCH - agent made no edits" >> "$LOG"; fi
echo "BLIND-INFORMED-DONE-$SLUG" >> "$LOG"
