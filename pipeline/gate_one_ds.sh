#!/bin/bash
. "$HOME/cwe-bench/pipeline/docker-tuning.env" 2>/dev/null || true
# gate_one_ds.sh <slug> : gate one built task through nop/oracle/patches and leave exactly ONE
# marker in build/<slug>/:
#   .sound       every stage passed                                         (exit 0)
#   .unsound     a stage failed on the TASK itself; deterministic, so it is
#                not retried                                                (exit 1)
#   .gate_error  infrastructure kept failing (Docker/Harbor/host) or the gate
#                crashed: says nothing about the task, so re-gate it        (exit 2)
# The verdict, failing stage, kind, error and test evidence go to build/<slug>/gate_verdict.json;
# per-attempt output to build/<slug>/recover.log.
#
# Each attempt's outcome comes from gate.py's exit code (0 pass, 1 task, 2 infra, 3 internal)
# cross-checked with a report it wrote for THIS slug and stage in THIS attempt. Until 2026-10-20
# a real task failure left no stage key, read as ok=None, and was retried as an "infra flake";
# a missing or stale report now counts as an internal error, never as a pass or a fail.
s=${1:?usage: gate_one_ds.sh <slug>}
cd "$HOME/cwe-bench" || exit 2
B="build/$s"; LOG="$B/recover.log"; P="$B/gate_report.partial.json"
[ -d "$B" ] || { echo "$s: no $B"; exit 2; }
# One gate per task at a time: two gates on one slug overwrite each other's reports and markers.
exec 9>"$B/.gate.lock"
flock -n 9 || { echo "$s: another gate already holds $B/.gate.lock; not starting a second" | tee -a "$LOG"; exit 2; }

MAX_INFRA=4
verdict=pass; vstage=""; vkind=""; verror=""
echo "=== gate $s start $(date -u +%FT%TZ) ===" >> "$LOG"
for st in nop oracle patches; do
  for a in $(seq 1 $MAX_INFRA); do
    rm -f "$P"
    python3 -I builder/gate.py "$s" --only "$st" >> "$LOG" 2>&1
    rc=$?
    # kind<TAB>one-line summary, validated against slug + stage; anything else is "internal".
    # The failing stage's FULL record (complete error, evidence lines, evidence_file) is kept in
    # $B/.stage_result.json for gate_verdict.json; the log line names the evidence file.
    res=$(python3 - "$P" "$s" "$st" "$rc" "$B/.stage_result.json" "$LOG" <<'PY'
import json, sys
path, slug, stage, rc, keep, log = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6]
def out(kind, summary, record):
    json.dump({"kind": kind, **record}, open(keep, "w"), indent=1)
    print(f"{kind}\t{' '.join(str(summary).split())[:400]}")
    sys.exit()
try:
    r = json.load(open(path))
except Exception as e:
    out("internal", f"gate.py exited {rc} without a readable report ({type(e).__name__}: {e}); see {log}",
        {"error": f"gate.py exited {rc} without a readable report: {type(e).__name__}: {e}", "log": log})
if r.get("slug") != slug or r.get("only") != stage:
    out("internal", f"report is for {r.get('slug')}/{r.get('only')}, not {slug}/{stage}", {"report": r})
st = r.get("stages", {}).get(stage, {})
verdict = r.get("verdict")
want = {"pass": 0, "task": 1, "infra": 2, "internal": 3}.get(verdict)
if want is None or want != rc:
    out("internal", f"gate.py exit {rc} disagrees with report verdict {verdict!r}", {"report": r})
if verdict == "pass":
    if st.get("ok") is True:
        out("pass", "", {})
    out("internal", "verdict pass but stage not ok", {"report": r})
err = str(st.get("error") or r.get("failure") or "")
ef = st.get("evidence_file")
out(verdict, err + (f" || full evidence: {ef}" if ef else ""), st)
PY
)
    kind=${res%%$'\t'*}; err=${res#*$'\t'}
    echo "  $s $st attempt=$a rc=$rc -> $kind${err:+: $err}" >> "$LOG"
    [ "$kind" = infra ] || break
    [ "$a" -lt "$MAX_INFRA" ] && sleep $((30 * a))
  done
  if [ "$kind" != pass ]; then verdict=$kind; vstage=$st; vkind=$kind; verror=$err; break; fi
done

case "$verdict" in
  pass) mark=.sound;       code=0; word=SOUND ;;
  task) mark=.unsound;     code=1; word="unsound ($vstage: task failure)" ;;
  infra) mark=.gate_error; code=2; word="GATE-ERROR ($vstage: infrastructure failed $MAX_INFRA times; not a task verdict)" ;;
  *)    mark=.gate_error;  code=2; word="GATE-ERROR ($vstage: gate internal error; not a task verdict)" ;;
esac
python3 - "$B/gate_verdict.json" "$s" "$verdict" "$vstage" "$verror" "$B/.stage_result.json" <<'PY'
import json, sys, time
p, slug, verdict, stage, summary, keep = sys.argv[1:7]
rec = {}
if verdict != "pass":
    try:
        rec = json.load(open(keep))
    except Exception as e:
        rec = {"error": f"(stage record unreadable: {type(e).__name__}: {e})"}
json.dump({"slug": slug, "verdict": verdict, "stage": stage or None, "summary": summary or None,
           "error": rec.get("error"), "evidence": rec.get("evidence"),
           "evidence_file": rec.get("evidence_file"),
           "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, open(p, "w"), indent=1)
PY
rm -f "$B/.sound" "$B/.unsound" "$B/.gate_error"; touch "$B/$mark"
echo "  $s RESULT $word $(date -u +%FT%TZ)" >> "$LOG"
echo "$s $word${verror:+ :: ${verror:0:400}}"
exit $code
