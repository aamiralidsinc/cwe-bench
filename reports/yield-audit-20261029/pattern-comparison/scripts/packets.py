import csv,json,os,re,glob,random,shutil
B='/Users/dev/terminal-bench/cwe-bench/diversity_population/out/audits/2026-10-28-chunk1/tasks'
groups={}
for r in csv.DictReader(open('all-b1-b6.tsv'),delimiter='\t'):
    if r['batch'] in ('scale-b1','scale-b3','scale-b5','scale-b6'):
        groups[r['task']]=(r['batch'],'main')
for s in os.listdir(B): groups[s]=('div-chunk1','div')
def paths(s,kind):
    if kind=='div':
        t=f'{B}/{s}/task-package'; b=f'{B}/{s}/builder'
    else:
        t=f'main/tasks/{s}'; b=f'main/build/{s}'
    return t,b
items=list(groups.items()); random.seed(7); random.shuffle(items)
key={}
shutil.rmtree('packets',ignore_errors=True); os.makedirs('packets')
n=0
for s,(g,kind) in items:
    t,b=paths(s,kind)
    if not (os.path.exists(f'{t}/instruction.md') and os.path.exists(f'{b}/manifest.json')): continue
    n+=1; pid=f'T{n:03d}'; key[pid]=(s,g)
    short=s.replace('diversity-','')
    def anon(x): return x.replace(s,pid).replace(short,pid) if len(short)>3 else x.replace(s,pid)
    d=f'packets/{pid}'; os.makedirs(d)
    open(f'{d}/instruction.md','w').write(open(f'{t}/instruction.md',errors='replace').read())
    m=json.load(open(f'{b}/manifest.json'))
    keep={k:m.get(k) for k in ('pattern','track','verified','entry_point','traps','stacking') if k in m}
    if 'verified' in keep and isinstance(keep['verified'],dict): keep['verified']={k:v for k,v in keep['verified'].items() if k in ('entry_point','sites','routes')}
    open(f'{d}/manifest.json','w').write(anon(json.dumps(keep,indent=1)))
    for src,dst,cap in ((f'{t}/environment/injection.patch','injection.patch',60000),(f'{t}/solution/fix.patch','fix.patch',80000)):
        if os.path.exists(src):
            x=open(src,errors='replace').read()
            if len(x)>cap: x=x[:cap]+f'\n[... truncated, {len(x)} bytes total]\n'
            open(f'{d}/{dst}','w').write(x)
    bp=f'{b}/BUILD-PROMPT.md'
    if os.path.exists(bp):
        x=open(bp,errors='replace').read()
        mm=re.search(r'\n- Published fix sites:(.*?)\n- (Uncovered routes|Design plan)',x,re.S)
        mu=re.search(r'\n- Uncovered routes to confirm \(pattern B\):(.*?)\n- Design plan',x,re.S)
        txt='PUBLISHED (UPSTREAM) FIX SITES, as the screener recorded them:\n'+(mm.group(1) if mm else '(not recorded)')+'\n'
        if mu: txt+='\nREAL UNCOVERED UPSTREAM ROUTES the screener proposed (the builder may or may not have used them):\n'+mu.group(1)+'\n'
        open(f'{d}/advisory_sites.txt','w').write(anon(txt))
    sec=f'{t}/tests/security'; acc=''
    if os.path.isdir(sec):
        for f in sorted(glob.glob(sec+'/**/*',recursive=True)):
            if os.path.isfile(f) and os.path.getsize(f)<200000:
                acc+=f'\n===== {os.path.relpath(f,sec)} =====\n'+open(f,errors='replace').read()
    if len(acc)>50000: acc=acc[:50000]+'\n[... truncated]\n'
    open(f'{d}/security_tests.txt','w').write(anon(acc))
json.dump(key,open('packet_key.json','w'),indent=0)
import collections; print(n, collections.Counter(g for s,g in key.values()))
