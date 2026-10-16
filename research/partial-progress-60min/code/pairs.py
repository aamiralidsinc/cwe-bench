import csv, sys, statistics as st
S=sys.argv[1]
R=list(csv.DictReader(open(S+"/runs.tsv"),delimiter="\t"))
f=lambda x: float(x) if x not in ("",None) else None
for r in R:
    r["d"]=f(r["dur"]); r["rw"]=f(r["reward"]); r["le"]=max([v for v in (f(r["last_edit"]),f(r["last_bash_edit"])) if v is not None], default=None)
    r["to"]=r["timed_out"]=="True"
    # graded at the 1 h cutoff: ran under the 3600 limit and timed out (graded at timeout)
    r["at60"]= r["d"] is not None and (r["d"]<=60.05 or (r["to"] and r["limit"]=="3600"))
def fmt(r):
    s=f'{r["d"]:.1f}' if r["d"] is not None else "?"
    s+=("T" if r["to"] else "")
    if r["d"] and r["d"]>60 and not r["at60"]: s+=f'(last edit {r["le"]})'
    return s
tasks=sorted({r["task"] for r in R})
lines=[]; flip=[]; summary={}
for t in tasks:
  for m in ("deepseek","mimo"):
    rs=[r for r in R if r["task"]==t and r["model"]==m]
    cs=[r for r in rs if r["cat"]=="counted" and r["rw"]==1.0]
    cf=[r for r in rs if r["cat"]=="counted" and r["rw"] is not None and r["rw"]<1]
    other=[r for r in rs if r["cat"]!="counted" and r["rw"]==1.0]
    strict=any(r["at60"] for r in cs)
    est=strict or any(r["le"] is not None and r["le"]<=60 for r in cs)
    aw60=any(r["at60"] for r in other if r["cat"]=="awaiting")
    oth60={r["cat"] for r in other if r["at60"]}
    summary[(t,m)]=(strict,est,aw60,oth60)
    lines.append(f'{t}\t{m}\t{", ".join(fmt(r) for r in cs) or "-"}\t{", ".join(fmt(r)+"="+r["reward"] for r in cf) or "-"}\t{"; ".join(r["cat"]+":"+fmt(r) for r in other) or "-"}\t{"Y" if strict else "N"}\t{"Y" if est else "N"}\t{"Y" if aw60 else "N"}\t{",".join(sorted(oth60)) or "-"}')
open(S+"/pairs.tsv","w").write("task\tmodel\tcounted_solves_min\tcounted_fails\tother_solves\tcounted_solve_le60_strict\tcounted_le60_by_last_edit\tawaiting_solve_le60\tother_le60_cats\n"+"\n".join(lines)+"\n")
print("\n".join(lines))
print()
for t in tasks:
    sd,ed,ad,od=summary[(t,"deepseek")]; sm,em,am,om=summary[(t,"mimo")]
    print(t, "strict:",("DS" if sd else "--"),("MI" if sm else "--"), " est:",("DS" if ed else "--"),("MI" if em else "--"), " +awaiting:",("DS" if sd or ad else "--"),("MI" if sm or am else "--"), " any<=60:",("DS" if sd or ad or od else "--"),("MI" if sm or am or om else "--"), od, om)
