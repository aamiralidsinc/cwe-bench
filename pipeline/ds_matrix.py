#!/usr/bin/env python3
import glob, os, re
def rw(p):
    try: return [float(x) for x in re.findall(r"reward=([0-9.]+)", open(p).read())]
    except Exception: return []
def solved(x): return any(abs(v-1) < 1e-6 for v in x)
def status(x):
    if not x: return "none"
    if solved(x): return "SOLVED"
    if len(x) >= 3: return "FAILED3/3"
    return "inprog(%d)" % len(x)

rows = []
for d in sorted(glob.glob("build/*-ds")):
    s = os.path.basename(d)
    ds = rw(d + "/runs_deepseek.log"); mm = rw(d + "/runs_mimo.log")
    if ds or mm:
        rows.append((s, ds, mm))

built = sum(1 for d in glob.glob("build/*-ds") if os.path.exists(d + "/build-exit.txt"))
sound = sum(1 for d in glob.glob("build/*-ds") if os.path.exists(d + "/.sound"))
ds_done = ds_prog = mm_done = mm_prog = both_solved = 0
breakers = []; ds_fail = []; mm_fail = []

print("%-28s %-20s %-20s %s" % ("task", "DeepSeek", "MiMo", "verdict"))
for s, ds, mm in rows:
    dss = status(ds); mms = status(mm)
    if dss in ("SOLVED", "FAILED3/3"): ds_done += 1
    elif "inprog" in dss: ds_prog += 1
    if mms in ("SOLVED", "FAILED3/3"): mm_done += 1
    elif "inprog" in mms: mm_prog += 1
    v = ""
    if dss == "FAILED3/3" and mms == "FAILED3/3": v = "** BREAKER **"; breakers.append(s)
    elif dss == "SOLVED" and mms == "SOLVED": v = "both-solved"; both_solved += 1
    if dss == "FAILED3/3": ds_fail.append(s)
    if mms == "FAILED3/3": mm_fail.append(s)
    print("%-28s %-20s %-20s %s/%s %s" % (s, ds, mm, dss, mms, v))

print()
print("DS tasks: built=%d  sound=%d  trialed(either model)=%d" % (built, sound, len(rows)))
print("DeepSeek trials: completed=%d  in-progress=%d" % (ds_done, ds_prog))
print("MiMo    trials: completed=%d  in-progress=%d" % (mm_done, mm_prog))
print("BOTH-MODELS BREAKERS=%d: %s" % (len(breakers), breakers))
print("both-solved=%d" % both_solved)
print("DeepSeek-failed(3/3)=%s" % ds_fail)
print("MiMo-failed(3/3)=%s" % mm_fail)
