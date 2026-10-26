#!/bin/bash
# rca_rerun.sh SLUG PATCH : re-run a task's hidden tests in its own image, with PATCH applied, and
# keep EVERYTHING for root-cause analysis. No agent, no model, no Harbor; nothing in the task changes.
#   PATCH = nop (untouched code) | oracle (solution/fix.patch) | a checks/ patch name (blind.patch)
#           | a path to any patch file
# Output: build/SLUG/rca/<UTC>-<patch>/
#   report.txt   failing tests with their complete output (common/util/evidence.py), then the
#                full test stdout
#   stdout.txt   everything test.sh printed;  verifier/  JUnit XML, results.json, reward
# For JS/TS tests, the hidden test COPIES used here get common/util/rca/jest-explain-errors.cjs
# prepended, so an assertion like expect(error).toBeInstanceOf(InputError) prints the received
# error's message and stack instead of only its class (stack line numbers shift by one).
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
SLUG=${1:?usage: rca_rerun.sh SLUG nop|oracle|<checks patch>|<patch path>}; PATCH=${2:?patch}
R="$CWE_ROOT"; T="$R/tasks/$SLUG"; B="$R/build/$SLUG"; IMG="cwe-blind-src:$SLUG"
cd "$R" || exit 2
case "$PATCH" in
  nop) PF="" ;;
  oracle) PF="$T/solution/fix.patch" ;;
  *) if [ -f "$B/checks/$PATCH" ]; then PF="$B/checks/$PATCH"; elif [ -f "$PATCH" ]; then PF=$(readlink -f "$PATCH");
     else echo "rca: no patch $PATCH (not in build/$SLUG/checks, not a file)" >&2; exit 2; fi ;;
esac
OUT="$B/rca/$(date -u +%Y%m%dT%H%M%SZ)-$(basename "${PATCH%.patch}")"; mkdir -p "$OUT/verifier" "$OUT/tests" "$OUT/rca"
echo "[rca] $SLUG with $PATCH -> $OUT"
docker build -t "$IMG" "$T/environment" > "$OUT/image-build.log" 2>&1 \
  || { echo "[rca] image build failed: $OUT/image-build.log" >&2; exit 3; }
cp -a "$T/tests/." "$OUT/tests/"
# WHAT-IF (optional): TEST_PATCH=<patch> is applied to the test COPIES only (paths relative to
# tests/), e.g. to show that a harness defect, not the fix, makes a test fail. The task never changes.
if [ -n "${TEST_PATCH:-}" ]; then
  patch -p1 -d "$OUT/tests" < "$TEST_PATCH" > "$OUT/test-patch.log" 2>&1 \
    || { echo "[rca] TEST_PATCH did not apply: $OUT/test-patch.log" >&2; exit 2; }
  cp "$TEST_PATCH" "$OUT/what-if-test.patch"; echo "[rca] WHAT-IF: test copies patched with $TEST_PATCH"
fi
cp "$R/common/util/rca/jest-explain-errors.cjs" "$OUT/rca/"
n=0
while IFS= read -r f; do
  { printf 'require("/rca/jest-explain-errors.cjs");\n'; cat "$f"; } > "$f.rca" && mv "$f.rca" "$f"; n=$((n+1))
done < <(find "$OUT/tests" -type f \( -name '*.test.[jt]s' -o -name '*.test.[jt]sx' -o -name '*.spec.[jt]s' -o -name '*.spec.[jt]sx' \))
echo "[rca] explain-errors hook added to $n JS/TS test file copies"
[ -n "$PF" ] && cp "$PF" "$OUT/rca/fix.patch"
# Same layout as a Harbor trial: tests at /tests, results in /logs/verifier, repo at /app.
timeout 3600 docker run --rm --network none --name "rca-$SLUG-$$" \
  -v "$OUT/tests:/tests:ro" -v "$OUT/rca:/rca:ro" -v "$OUT/verifier:/logs/verifier" "$IMG" \
  bash -c 'set -o pipefail; cd /app || exit 90
    if [ -f /rca/fix.patch ]; then echo "[rca] applying patch"; patch -p1 --forward --no-backup-if-mismatch < /rca/fix.patch || exit 91; fi
    bash /tests/test.sh' > "$OUT/stdout.txt" 2>&1
rc=$?
echo "[rca] test.sh exit $rc (90 = no /app, 91 = patch did not apply, 124 = timeout)"
python3 - "$OUT" "$SLUG" "$PATCH" "$rc" "$CWE_COMMON/util" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[5])
import evidence as ev
out, slug, patch, rc = sys.argv[1:5]
d = {"failing_tests": ev.junit_failures(out), "verifier_stdout_tail": ev.read(Path(out, "stdout.txt"), 400_000),
     "results_json": ev.read(Path(out, "verifier", "results.json"))}
summary = f"{slug} with {patch}: test.sh exit {rc}; {len(d['failing_tests'])} failing test case(s)"
rec = {"what": f"rca re-run {slug} {patch}", "kind": "rca", "utc": Path(out).name, "summary": summary, "details": d}
Path(out, "report.txt").write_text(ev.render(rec))
print(f"[rca] {summary}\n[rca] report: {out}/report.txt")
for t in d["failing_tests"][:8]:
    for p in t.get("problems") or []:
        print(f"  FAIL {t.get('name')}\n    {ev.one_line(p.get('text') or p.get('message'), 700)}")
PY
