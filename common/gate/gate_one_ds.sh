#!/bin/bash
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
. "$CWE_DOCKER_TUNING" 2>/dev/null || true
# gate_one_ds.sh <slug> : gate one built task through static, then nop/oracle/patches IN PARALLEL, and leave exactly ONE
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
cd "$CWE_ROOT" || exit 2
B="build/$s"; LOG="$B/recover.log"
[ -d "$B" ] || { echo "$s: no $B"; exit 2; }
# One gate per task at a time: two gates on one slug overwrite each other's reports and markers.
exec 9>"$B/.gate.lock"
flock -n 9 || { echo "$s: another gate already holds $B/.gate.lock; not starting a second" | tee -a "$LOG"; exit 2; }

# Task-level gate mutex (owner decision 2026-10-26): at most GATE_TASK_SLOTS (default 6) tasks gate at once on this
# VM. Scale batch 1 put 56 tasks into their gates together (~15 Harbor runs each, ~650 runs, load ~1000 on 64 CPUs).
# A slot is one of N lock files; the lock lives on fd 8 for this script's lifetime (its stage subshells inherit it),
# so a killed gate never leaks its slot. gate.py also caps Harbor runs VM-wide (GATE_GLOBAL_SLOTS). 0 disables.
TS=${GATE_TASK_SLOTS:-6}
if [ "$TS" -gt 0 ]; then
  SD="$HOME/.tb-graders/cwe/slots/task-gate"; mkdir -p "$SD"; got=""
  while [ -z "$got" ]; do
    for i in $(seq 1 "$TS"); do
      exec 8>"$SD/slot-$i.lock"
      if flock -n 8; then got=$i; break; fi
      exec 8>&-
    done
    [ -n "$got" ] || sleep $((10 + RANDOM % 10))
  done
  echo "  $s task-gate slot $got/$TS taken $(date -u +%FT%TZ)" >> "$LOG"
fi

MAX_INFRA=4
verdict=pass; vstage=""; vkind=""; verror=""
echo "=== gate $s start $(date -u +%FT%TZ) ===" >> "$LOG"

# One stage, with its infra retries. Each stage has its OWN report (gate_report.partial.<stage>.json),
# stage record (.stage_result.<stage>.json) and log (recover.<stage>.log), so stages can run at once.
# Result line "kind<TAB>summary" goes to .stage.<stage>.res.
run_stage() {
  local st=$1 a rc res kind err
  local SP="$B/gate_report.partial.$st.json" KEEP="$B/.stage_result.$st.json" SL="$B/recover.$st.log"
  : > "$SL"
  for a in $(seq 1 $MAX_INFRA); do
    rm -f "$SP"
    python3 -I common/gate/gate.py "$s" --only "$st" --report "gate_report.partial.$st.json" >> "$SL" 2>&1
    rc=$?
    # kind<TAB>one-line summary, validated against slug + stage; anything else is "internal".
    res=$(python3 - "$SP" "$s" "$st" "$rc" "$KEEP" "$SL" <<'PY'
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
  printf '%s\n' "$res" > "$B/.stage.$st.res"
}

# static needs no Docker and is quick: it runs first, alone. Then nop, oracle and patches run AT THE SAME
# TIME (2026-10-25; they are independent Harbor runs), unless GATE_STAGES_PARALLEL=0. The verdict is read
# in the fixed order static, nop, oracle, patches, so it names the same failing stage the old one-at-a-time
# loop would have named.
STAGES="static nop oracle patches"
rm -f "$B"/.stage.*.res
run_stage static
if [ "$(cut -f1 "$B/.stage.static.res")" = pass ]; then
  if [ "${GATE_STAGES_PARALLEL:-1}" = 0 ]; then
    for st in nop oracle patches; do
      run_stage "$st"; [ "$(cut -f1 "$B/.stage.$st.res")" = pass ] || break
    done
  else
    pids=()
    for st in nop oracle patches; do run_stage "$st" & pids+=($!); sleep 2; done
    wait "${pids[@]}"
  fi
fi
for st in $STAGES; do cat "$B/recover.$st.log" >> "$LOG" 2>/dev/null; done
for st in $STAGES; do
  f="$B/.stage.$st.res"
  if [ ! -f "$f" ]; then
    # a later stage never ran because an earlier one failed (or was not reached): verdict already set
    break
  fi
  res=$(cat "$f"); kind=${res%%$'\t'*}; err=${res#*$'\t'}
  if [ "$kind" != pass ]; then
    verdict=$kind; vstage=$st; vkind=$kind; verror=$err
    cp -f "$B/.stage_result.$st.json" "$B/.stage_result.json" 2>/dev/null
    break
  fi
done
# Combined report (gate_report.json), the file run_stack_pipeline.sh and older tools read for "passed".
python3 - "$B" "$s" "$verdict" "$vstage" <<'PY'
import json, sys, time, glob, os
b, slug, verdict, stage = sys.argv[1:5]
stages = {}
for st in ("static", "nop", "oracle", "patches"):
    try:
        stages[st] = json.load(open(os.path.join(b, f"gate_report.partial.{st}.json"))).get("stages", {}).get(st)
    except Exception:
        pass
json.dump({"slug": slug, "passed": verdict == "pass", "verdict": verdict, "failed_stage": stage or None,
           "stages": stages, "via": "common/gate/gate_one_ds.sh (stages in parallel)",
           "finished": time.strftime("%Y-%m-%dT%H:%M:%S")}, open(os.path.join(b, "gate_report.json"), "w"), indent=1)
PY

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
# A SOUND is valid only for the files it gated (common/gate/fingerprint.py): record them, so a later
# change to tests/solution/environment/checks makes run_trial.sh and regrade.py refuse until re-gated.
if [ "$mark" = .sound ]; then python3 -I "$CWE_ROOT/common/gate/fingerprint.py" write "$s" >> "$LOG" 2>&1; else rm -f "$B/gate_fingerprint.json"; fi
echo "  $s RESULT $word $(date -u +%FT%TZ)" >> "$LOG"
echo "$s $word${verror:+ :: ${verror:0:400}}"
exit $code
