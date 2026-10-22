#!/bin/bash
cd "$HOME/cwe-bench" || exit 1
. pipeline/docker-tuning.env 2>/dev/null || true
L=build/pipeline/verify_regate.log; : > "$L"
echo "=== INDEPENDENT verify re-gate START $(date -u +%FT%TZ) (serial, clean) ===" >> "$L"
for s in astro-ds keras-ds flyto-core-ds fission-ds yamcs-ds; do
  echo "--- $s $(date -u +%T) ---" >> "$L"
  rm -f build/$s/.sound build/$s/.unsound          # force a fresh verdict, no stale marker
  bash pipeline/gate_one_ds.sh "$s" >> "$L" 2>&1
  # read the fresh full report
  python3 - "$s" >> "$L" 2>&1 <<PY
import json,glob,sys
s=sys.argv[1]
f=sorted(glob.glob(f"build/{s}/gate_report*.json"))
m=json.load(open(f[-1])) if f else {}
st=m.get("stages",{})
import os
snd=os.path.exists(f"build/{s}/.sound"); uns=os.path.exists(f"build/{s}/.unsound")
summary={k:(v.get("ok") if isinstance(v,dict) else v) for k,v in st.items()} if isinstance(st,dict) else st
print(f"[VERDICT {s}] sound={snd} unsound={uns} verdict={m.get('verdict','?')} stages_ok={summary} report={os.path.basename(f[-1]) if f else 'NONE'}")
PY
done
echo "VERIFY-REGATE-DONE $(date -u +%FT%TZ)" >> "$L"
