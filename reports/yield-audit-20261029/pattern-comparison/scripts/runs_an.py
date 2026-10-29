import csv,json,os,re,collections,statistics,datetime
rows={r['slug']:r for r in csv.DictReader(open('../pcmine/review_rows.tsv'),delimiter='\t')}
BUND='/Users/dev/terminal-bench/cwe-bench/diversity_population/out/audits/2026-10-28-chunk1'
def ts(x):
    try: return datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
    except Exception: return None
def files(cf):
    out=[]
    if not os.path.exists(cf): return None
    for r in csv.DictReader(open(cf),delimiter='\t'):
        p=r['path']
        if re.search(r'(^|/)(tests?|spec|__tests__|testdata)/|_test\.|\.test\.|test_[^/]*\.py$|Test\.(java|php)$|\.spec\.',p): continue
        out.append(p)
    return out
runs=[]
for r in csv.DictReader(open('../pcmine/runs.tsv'),delimiter='\t'):
    if r['slug'] not in rows: continue
    try: rw=float(r['reward'])
    except: continue
    a,b=ts(r['agent_start']),ts(r['agent_end'])
    runs.append(dict(slug=r['slug'],model=r['model'],run=r['run'],reward=rw,mins=((b-a).total_seconds()/60 if a and b else None),files=files(f"runs/{r['job']}/changed_files.tsv")))
for r in csv.DictReader(open('/Users/dev/terminal-bench/cwe-bench/diversity_population/out/regrade-chunk1/attempts.tsv'),delimiter='\t'):
    if r['outcome']!='graded' or r['task'] not in rows: continue
    t=os.path.join(BUND,r['trial'].strip())
    try: res=json.load(open(t+'/result.json')); ae=res.get('agent_execution') or {}
    except Exception: ae={}
    a,b=ts(ae.get('started_at','')),ts(ae.get('finished_at',''))
    m=re.search(r'-r(\d+)-',r['trial']); 
    runs.append(dict(slug=r['task'],model=r['model'],run='r'+(m.group(1) if m else '?'),reward=float(r['reward']),mins=((b-a).total_seconds()/60 if a and b else None),files=files(t+'/final-code/changed_files.tsv')))
def trapfiles(s,g):
    p=f'{BUND}/tasks/{s}/builder/manifest.json' if g=='div-chunk1' else f'main/build/{s}/manifest.json'
    m=json.load(open(p)); fs=set()
    for t in m.get('traps',[]):
        for w in re.split(r'[,;]\s*|\s+and\s+',str(t.get('where',''))):
            w=w.strip().split(':')[0].strip()
            if '/' in w or '.' in w: fs.add(w)
    return fs
def grp(g): return 'b5-6' if g in('scale-b5','scale-b6') else g
GG=['div-chunk1','b5-6','scale-b3','scale-b1']
print('group | model | first-run solve | median min of solved runs | solved runs touching <=1 non-test file | solved runs touching fewer files than distinct trap files')
for g in GG:
    for mdl in ('deepseek','mimo'):
        rr=[x for x in runs if grp(rows[x['slug']]['group'])==g and x['model']==mdl]
        r1=[x for x in rr if x['run']=='r1']
        sol=[x for x in rr if x['reward']>=1.0]
        mins=[x['mins'] for x in sol if x['mins']]
        f1=[x for x in sol if x['files'] is not None]
        one=sum(1 for x in f1 if len(x['files'])<=1)
        few=0;nn=0
        for x in f1:
            tf=trapfiles(x['slug'],rows[x['slug']]['group'])
            if len(tf)>=2:
                nn+=1
                if len(x['files'])<len(tf): few+=1
        print(g,'|',mdl,'|',f"{sum(x['reward']>=1 for x in r1)}/{len(r1)} ({100*sum(x['reward']>=1 for x in r1)/max(1,len(r1)):.0f}%)",'|',round(statistics.median(mins)) if mins else '-','|',f'{one}/{len(f1)}','|',f'{few}/{nn}')
