import json,sys
from datetime import datetime
from pathlib import Path
J=Path.home()/".tb-graders/cwe/jobs"
ts=lambda s: datetime.fromisoformat(s.replace("Z","+00:00"))
for jt in sys.argv[2:]:
    job,trial=jt.split("/"); d=J/job/trial
    res=json.load(open(d/"result.json")); a0=ts(res["agent_execution"]["started_at"])
    tj=json.load(open(d/"agent/trajectory.json"))
    print("=====",jt)
    for s in tj["steps"]:
        m=(ts(s["timestamp"])-a0).total_seconds()/60
        if m<float(sys.argv[1]): continue
        for tc in s.get("tool_calls") or []:
            a=tc.get("arguments") or {}
            print(f'{m:6.1f} {tc["function_name"]:6} {(a.get("command") or a.get("file_path") or "")[:150]!r}')
