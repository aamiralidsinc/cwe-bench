import json, re, sys, csv
from pathlib import Path
from datetime import datetime
S = Path(sys.argv[1]); JOBS = Path.home()/".tb-graders/cwe/jobs"
def jl(p):
    try: return json.loads(Path(p).read_text())
    except Exception: return None
def ts(s): return datetime.fromisoformat(s.replace("Z","+00:00")) if s else None
cat = {(l.split("\t")[0], l.split("\t")[1]): l.split("\t")[2].strip() for l in open(S/"out/categories.tsv")}
rows = list(csv.DictReader(open(S/"out/trials.tsv"), delimiter="\t"))
BASH_EDIT = re.compile(r"sed\s+-i|perl\s+-[a-z]*i|\bpatch\b|git\s+apply|\btee\b|cat\s*>|>\s*/app|python3?\s+-\s*<<|python3?\s+-c|\bmv\b|\bcp\b|open\([^)]*['\"]w")
out = []
for r in rows:
    d = JOBS/r["job"]/r["trial"]
    cfg = jl(d/"config.json") or {}; res = jl(d/"result.json") or {}
    ag = cfg.get("agent") or {}; kw = ag.get("kwargs") or {}
    ae = res.get("agent_execution") or {}
    a0, a1 = ts(ae.get("started_at")), ts(ae.get("finished_at"))
    dur = (a1-a0).total_seconds()/60 if a0 and a1 else None
    last_edit = last_edit_bash = first_edit = last_step = None; n_edit_after60 = 0
    tj = jl(d/"agent/trajectory.json")
    if tj and a0:
        for st in tj.get("steps") or []:
            t = ts(st.get("timestamp"));
            if not t: continue
            m = (t-a0).total_seconds()/60; last_step = m
            for tc in st.get("tool_calls") or []:
                fn = tc.get("function_name"); args = tc.get("arguments") or {}
                if fn in ("Edit","Write","MultiEdit","NotebookEdit"):
                    fp = str(args.get("file_path",""))
                    if fp.startswith("/tmp"): continue
                    last_edit = m; first_edit = first_edit if first_edit is not None else m
                    if m > 60: n_edit_after60 += 1
                elif fn == "Bash":
                    c = str(args.get("command",""))
                    if BASH_EDIT.search(c) and "/app" in c:
                        last_edit_bash = m
    out.append(dict(task=r["task"], model="deepseek" if "deepseek" in r["model"] else "mimo",
        effort=kw.get("reasoning_effort",""), mtt=kw.get("max_thinking_tokens",""), webtools_off="disallowed_tools" in kw,
        start=r["start_utc"], limit=r["limit_sec"], timed_out=r["timed_out"], reward=r["reward"], grading=r["grading"],
        cat=cat.get((r["job"],r["trial"]),"?"), dur=None if dur is None else round(dur,1),
        first_edit=None if first_edit is None else round(first_edit,1), last_edit=None if last_edit is None else round(last_edit,1),
        last_bash_edit=None if last_edit_bash is None else round(last_edit_bash,1), edits_after60=n_edit_after60,
        last_step=None if last_step is None else round(last_step,1), traj=bool(tj), job=r["job"], trial=r["trial"]))
cols = list(out[0].keys())
with open(S/"runs.tsv","w") as f:
    f.write("\t".join(cols)+"\n")
    for o in out: f.write("\t".join("" if o[c] is None else str(o[c]) for c in cols)+"\n")
print(len(out))
