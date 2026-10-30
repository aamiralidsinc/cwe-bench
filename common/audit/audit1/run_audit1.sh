#!/bin/bash
# Audit 1, step 2: the DeepSeek dossier agent for ONE failing run (design: docs/AUDIT-TWO-STAGE-DESIGN.md).
#
#   cd <run-folder> && common/launch/drive.sh deepseek bash <repo>/common/audit/audit1/run_audit1.sh
#   common/launch/drive.sh deepseek bash common/audit/audit1/run_audit1.sh <run-folder>
#
# <run-folder> is a prepared postmortem folder (evidence/, PREPARED.json) on which facts.py has written FACTS.json and
# facts-input/. The run folder may be given as the argument, as $AUDIT1_DIR, or as the current directory (the last
# form keeps task names out of the process command line, which the work queue reads to find busy tasks).
#
# Launched the same way as the fairness review (pipelines/sibling/9-fairness/run_fairness.sh): through drive.sh, which
# points Claude Code at DeepSeek and exports MODEL; read-only tools plus Write; --restricted confines the file tools to
# the run folder, so the agent cannot open verdict.json, POSTMORTEM.*, other runs or any review. The prompt goes in on
# stdin (common/audit/audit1/AUDIT1-PROMPT.md below its scissors line).
#
# Then quote_check.py checks every quote. On a failure the agent gets ONE retry that sees only the quote-check report
# and its own first dossier (DOSSIER.try1.json) and must fix or drop the failing quotes ($AUDIT1_RETRY=0 turns it off).
#
# Writes in the run folder: DOSSIER.json, DOSSIER.md, audit1-stream-<n>.jsonl, audit1-run-<n>.json (the result event),
# audit1-status-<n>.json, QUOTECHECK-<n>.json, and AUDIT1.json (summary: status, attempts, quote check per attempt,
# tokens per attempt, wall time). Exit 0 = a dossier that passed the quote check; 1 = anything else.
set -uo pipefail
. "$(d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); while [ ! -f "$d/.cwe-bench-root" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/common/paths.sh"
HERE=$CWE_COMMON/audit/audit1
DIR=${1:-${AUDIT1_DIR:-$PWD}}
DIR=$(cd "$DIR" && pwd -P) || exit 1
cd "$DIR" || exit 1
[ -n "${MODEL:-}" ] || { echo '{"status":"error: MODEL not set; launch through common/launch/drive.sh deepseek"}' > AUDIT1.json; exit 1; }
[ -s FACTS.json ] || { echo '{"status":"error: no FACTS.json (run facts.py first)"}' > AUDIT1.json; exit 1; }
[ -d evidence ] || { echo '{"status":"error: no evidence/ folder"}' > AUDIT1.json; exit 1; }
TIMEOUT=${AUDIT1_TIMEOUT:-2700}
TEMPLATE=$(sed -n '/^---8<---$/,$p' "$HERE/AUDIT1-PROMPT.md" | tail -n +2)
START=$(date -u +%s)

attempt() {   # attempt <n> <extra text>
  local n=$1 extra=$2
  python3 -I -c '
import sys
t = sys.stdin.read()
print(t.replace("{{DIR}}", sys.argv[1]).replace("{{EXTRA}}", sys.argv[2]))' "$DIR" "$extra" <<<"$TEMPLATE" > "prompt-$n.txt"
  date -u +%FT%TZ > "audit1-start-$n.txt"
  timeout "$TIMEOUT" "$HOME/.local/bin/claude" -p --model "$MODEL" \
    --restricted --safe-mode --strict-mcp-config --no-session-persistence \
    --tools "Read,Grep,Glob,Write" --permission-mode acceptEdits \
    --output-format stream-json --verbose < "prompt-$n.txt" > "audit1-stream-$n.jsonl" 2> "audit1-stream-$n.err"
  local rc=$?
  echo "$rc" > "audit1-exit-$n.txt"
  date -u +%FT%TZ > "audit1-end-$n.txt"
  python3 -I -c '
import json, sys
last = {}
for line in open(sys.argv[1], errors="replace"):
    try:
        e = json.loads(line)
    except ValueError:
        continue
    if isinstance(e, dict) and e.get("type") == "result":
        last = e
json.dump(last, open(sys.argv[2], "w"))' "audit1-stream-$n.jsonl" "audit1-run-$n.json"
  cp "audit1-stream-$n.err" "audit1-run-$n.err" 2>/dev/null
  python3 "$CWE_AGENT_STATUS" "audit1-run-$n.json" "$rc" --details "audit1-status-$n.json" > /dev/null
  python3 -I "$HERE/quote_check.py" "$DIR" --json "QUOTECHECK-$n.json" > "QUOTECHECK-$n.txt" 2>&1
  return 0
}

attempt 1 ""
QC1=$(head -n 1 QUOTECHECK-1.txt 2>/dev/null)
if [ -s DOSSIER.json ] && ! grep -q '^quote check: PASS' QUOTECHECK-1.txt && [ "${AUDIT1_RETRY:-1}" != 0 ]; then
  mv DOSSIER.json DOSSIER.try1.json
  [ -f DOSSIER.md ] && mv DOSSIER.md DOSSIER.try1.md
  EXTRA="
## RETRY: your first dossier failed the quote check

Your first dossier is $DIR/DOSSIER.try1.json. The quote check reported these failures:

$(sed -n '2,80p' QUOTECHECK-1.txt)

Re-open each cited file, find the exact text and its real line, and correct the quote (file, line, text). If a quote
cannot be found because the claim was wrong, drop the quote and correct the claim. Keep everything else from the
first dossier unless the corrected quotes change it. Then write the corrected $DIR/DOSSIER.json and DOSSIER.md."
  attempt 2 "$EXTRA"
fi
END=$(date -u +%s)
python3 -I - "$DIR" "$START" "$END" <<'PY'
import json, sys
from pathlib import Path
d, start, end = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
att = []
for n in (1, 2):
    run = d / f"audit1-run-{n}.json"
    if not run.exists():
        continue
    r = json.loads(run.read_text() or "{}")
    st = json.loads((d / f"audit1-status-{n}.json").read_text()) if (d / f"audit1-status-{n}.json").exists() else {}
    qc = json.loads((d / f"QUOTECHECK-{n}.json").read_text()) if (d / f"QUOTECHECK-{n}.json").exists() else None
    u = r.get("usage") or {}
    att.append({"attempt": n, "status": st.get("status"), "num_turns": r.get("num_turns"),
                "duration_ms": r.get("duration_ms"), "cost_usd": r.get("total_cost_usd"),
                "tokens": {"input": u.get("input_tokens"), "cache_read": u.get("cache_read_input_tokens"),
                           "cache_creation": u.get("cache_creation_input_tokens"), "output": u.get("output_tokens")},
                "model_usage": r.get("modelUsage"),
                "quote_check": None if qc is None else {"pass": qc["pass"], "quotes": qc["quotes"],
                                                        "failed": qc["failed"], "error": qc.get("error")}})
final = att[-1] if att else {}
ok = bool(final) and final.get("status") == "ok" and (final.get("quote_check") or {}).get("pass") is True
s = {"status": "ok" if ok else ("unverified" if final.get("status") == "ok" else f"error: {final.get('status')}"),
     "attempts": att, "wall_sec": end - start,
     "first_try_quote_pass": bool(att) and (att[0].get("quote_check") or {}).get("pass") is True}
(d / "AUDIT1.json").write_text(json.dumps(s, indent=1))
print(f"audit1: {s['status']}; attempts {len(att)}; first-try quote check "
      f"{'pass' if s['first_try_quote_pass'] else 'fail'}; {s['wall_sec']} s")
sys.exit(0 if ok else 1)
PY
