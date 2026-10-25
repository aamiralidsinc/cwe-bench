import json,sys,re
from datetime import datetime
from pathlib import Path
J=Path.home()/".tb-graders/cwe/jobs"
ts=lambda s: datetime.fromisoformat(s.replace("Z","+00:00"))
TEST=re.compile(r"(/tests?/|_test\.|Test\.java|test_|\.md$|/spec/|\.test\.|conftest)")
for jt in sys.argv[1:]:
    job,trial=jt.split("/"); d=J/job/trial
    res=json.load(open(d/"result.json")); a0=ts(res["agent_execution"]["started_at"])
    tj=json.load(open(d/"agent/trajectory.json"))
    src=[];tst=[]
    for s in tj["steps"]:
        m=(ts(s["timestamp"])-a0).total_seconds()/60
        for tc in s.get("tool_calls") or []:
            a=tc.get("arguments") or {}; fn=tc["function_name"]
            if fn in("Edit","Write","MultiEdit"):
                fp=a.get("file_path","")
                if fp.startswith(("/tmp","/logs","/root")): continue
                (tst if TEST.search(fp) else src).append((round(m,1),fp.split("/")[-1]))
    after=[x for x in src if x[0]>60]
    print(jt.split("/")[1], "last_src", src[-1] if src else None, "n_src_after60", len(after), after[:4])
