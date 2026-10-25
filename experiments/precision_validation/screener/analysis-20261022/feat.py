import json,re,collections,statistics as st
R='/private/tmp/claude-501/-Users-dev-terminal-bench/8fe2c226-bbaf-4e42-97ca-80d166c4414f/scratchpad/share/cwe-bench-share-20261021/repo-vm/build/pipeline'
pool={json.loads(l)['entry_id']:json.loads(l) for l in open(R+'/pool.jsonl')}
L=json.load(open('/private/tmp/claude-501/-Users-dev-terminal-bench/8fe2c226-bbaf-4e42-97ca-80d166c4414f/scratchpad/predict/labels.json'))
AMB={'typo3-ds','hermes-agent-ds'}
def j(x):
    if isinstance(x,str):
        try: return json.loads(x)
        except: return x
    return x
rows=[]
for o in L:
    p=pool[o['entry']]
    d=j(p.get('distance')) or {}
    cb=j(p.get('coupled_behaviour'))
    ins=j(p.get('input_shapes'))
    oos=j(p.get('out_of_scope_site')) or {}
    cwe=re.findall(r'CWE-(\d+)',p.get('family',''))
    f=dict(slug=o['slug'],y=1 if o['label']=='BREAKER' else 0,amb=o['slug'] in AMB,
      sel=o['selscore'],in_mm=int(o['in_mm']),lang=p.get('language'),pattern=p.get('pattern_fit'),
      services=len(p.get('services') or []),fix_min=p.get('fix_minutes'),entry_points=p.get('entry_points'),
      oos_kind=(oos.get('kind') if isinstance(oos,dict) else str(oos)[:20]),
      d_files=d.get('files') if isinstance(d,dict) else None,d_pkgs=d.get('packages') if isinstance(d,dict) else None,
      repo_mb=d.get('repo_mb') if isinstance(d,dict) else None,
      unc_n=p.get('uncovered_routes_n'),inj_n=p.get('injection_room_n'),
      cb_len=len(json.dumps(cb)) if cb else 0, ins_n=len(ins) if isinstance(ins,list) else 0,
      rtd_len=len(p.get('reason_to_dismiss') or ''),dos=int(bool(p.get('dos'))),red=len(p.get('red_flags') or []),
      cwe=cwe[0] if cwe else '?',family=p.get('family','')[:70],offline=p.get('offline_ok'))
    rows.append(f)
json.dump(rows,open('/private/tmp/claude-501/-Users-dev-terminal-bench/8fe2c226-bbaf-4e42-97ca-80d166c4414f/scratchpad/predict/rows.json','w'),indent=1)
def auc(xs,ys):
    pos=[x for x,y in zip(xs,ys) if y==1]; neg=[x for x,y in zip(xs,ys) if y==0]
    if not pos or not neg: return None
    s=0
    for a in pos:
        for b in neg: s+= 1 if a>b else 0.5 if a==b else 0
    return s/(len(pos)*len(neg))
use=[r for r in rows if not r['amb']]
ys=[r['y'] for r in use]
print('n=',len(use),'pos=',sum(ys))
for k in ['sel','in_mm','services','fix_min','entry_points','d_files','d_pkgs','repo_mb','unc_n','inj_n','cb_len','ins_n','rtd_len','dos','red']:
    xs=[(r[k] if r[k] is not None else -1) for r in use]
    pm=[x for x,y in zip(xs,ys) if y]; nm=[x for x,y in zip(xs,ys) if not y]
    print(f"{k:12} AUC={auc(xs,ys):.2f}  breaker median={st.median(pm)}  other median={st.median(nm)}")
for k in ['lang','pattern','oos_kind','cwe']:
    c=collections.defaultdict(lambda:[0,0])
    for r in use: c[r[k]][0]+=r['y']; c[r[k]][1]+=1
    print(k, sorted(((v[0],v[1],kk) for kk,v in c.items()),key=lambda t:-t[1]))
