import json,sys,re
from datetime import datetime
from pathlib import Path
J=Path.home()/".tb-graders/cwe/jobs"
ts=lambda s: datetime.fromisoformat(s.replace("Z","+00:00"))
MOD=re.compile(r"sed\s+-i|perl\s+-\w*i|(?<![0-9&])>(?!\s*/dev/null|&|\s*/tmp|\s*/logs)|\btee\b|\bmv\b|\bcp\b|\brm\b|\bpatch\b|git\s+(checkout|apply|stash|restore|reset)|<<|gofmt\s+-w|cargo\s+fmt(?!.*--check)|go\s+mod|npm\s+(i|install)|pnpm|yarn|bundle\s+install|pip\s+install|open\(.*['\"]w")
for jt in sys.argv[2:]:
    job,trial=jt.split("/"); d=J/job/trial
    res=json.load(open(d/"result.json")); a0=ts(res["agent_execution"]["started_at"])
    tj=json.load(open(d/"agent/trajectory.json"))
    lastsrc=None; late=[]
    for s in tj["steps"]:
        m=(ts(s["timestamp"])-a0).total_seconds()/60
        for tc in s.get("tool_calls") or []:
            a=tc.get("arguments") or {}; fn=tc["function_name"]
            if fn in("Edit","Write","MultiEdit"):
                fp=a.get("file_path","")
                if fp.startswith(("/tmp","/logs")): continue
                lastsrc=(m,fp)
                if m>=float(sys.argv[1]): late.append(f'{m:6.1f} {fn} {fp}')
            elif fn=="Bash" and m>=float(sys.argv[1]):
                c=a.get("command","")
                if MOD.search(c): late.append(f'{m:6.1f} Bash {c[:300]!r}')
    print("=====",jt,"last /app edit via Edit/Write:",None if not lastsrc else f"{lastsrc[0]:.1f} {lastsrc[1]}")
    for l in late: print("   ",l)
