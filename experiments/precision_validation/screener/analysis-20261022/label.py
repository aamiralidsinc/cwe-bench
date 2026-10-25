import json,glob,os,csv,collections
R='/private/tmp/claude-501/-Users-dev-terminal-bench/8fe2c226-bbaf-4e42-97ca-80d166c4414f/scratchpad/share/cwe-bench-share-20261021'
P=R+'/repo-vm/build/pipeline'
pool={json.loads(l)['entry_id']:json.loads(l) for l in open(P+'/pool.jsonl')}
sel={d['entry_id']:d for d in json.load(open(P+'/selection_deepseek.json'))}
selm={d['entry_id']:d for d in json.load(open(P+'/selection_mimo.json'))}
BREAK={'protobuf.js-ds','seaweedfs-ds','electron-builder-ds','litellm-ds','mockoon-ds','hubuum-client-rust-ds','siyuan-ds','theia-ds','openbao-ds','tinacms-ds','knowns-ds','yamcs-ds'}
SOLVED={'astro-ds','keras-ds','flyto-core-ds','portainer-ds','fission-ds','coreutils-ds','orval-ds','vibe-trading-ds','airflow-ds','backstage-ds','flowise-ds'}
trials=collections.defaultdict(list)
for r in csv.DictReader(open(R+'/TRIALS-INDEX.csv')):
    t=r['task'].split('/')[-1]
    if t.endswith('-ds'): trials[t].append((r['model'],r['reward']))
abandoned=set(open(P+'/abandoned_ds.txt').read().split()) if os.path.exists(P+'/abandoned_ds.txt') else set()
out=[]
for f in sorted(glob.glob(P+'/specs_deepseek/*.json')):
    s=json.load(open(f)); slug=s['slug']; e=s['entry_id']
    b=R+'/repo-vm/build/'+slug
    sound=os.path.exists(b+'/.sound'); unsound=os.path.exists(b+'/.unsound')
    tr=trials.get(slug,[])
    if slug in BREAK: lab='BREAKER'
    elif slug in SOLVED: lab='solved'
    elif tr: lab='trialed-other'
    elif sound: lab='sound-untrialed'
    else: lab='not-built/unsound'
    out.append(dict(slug=slug,entry=e,label=lab,sound=sound,unsound=unsound,abandoned=slug in abandoned,
        ntr=len(tr),ds=[x[1] for x in tr if x[0]=='deepseek'][:6],mm=[x[1] for x in tr if x[0]=='mimo'][:6],
        selscore=sel.get(e,{}).get('score'),in_mm=e in selm))
json.dump(out,open(os.path.dirname(__file__)+'/labels.json','w'),indent=1)
c=collections.Counter(o['label'] for o in out); print(c)
for o in out: print(f"{o['label']:18} {o['slug']:28} sel={o['selscore']} mm={o['in_mm']} ab={o['abandoned']} ds={o['ds']} mm={o['mm']}")
