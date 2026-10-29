import json,sys,re,datetime
# usage: grepscan.py trapfiles.json slug transcript
tf=json.load(open(sys.argv[1]))[sys.argv[2]]
need=set(tf)
first_ts=None; pend={}; res={'n_search':0,'max_cov':0,'all_at_search':None,'min_all':None,'n_tf':len(need)}
def ts(x):
    try: return datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
    except Exception: return None
k=0
for line in open(sys.argv[3],errors='replace'):
    try: d=json.loads(line)
    except Exception: continue
    t=d.get('timestamp')
    if d.get('type')=='assistant':
        for c in (d.get('message') or {}).get('content') or []:
            if c.get('type')=='tool_use':
                k+=1
                cmd=json.dumps(c.get('input',{}))
                if re.search(r'\b(grep|rg|ag)\b',cmd) or c.get('name')=='Grep':
                    pend[c['id']]=k
    elif d.get('type')=='user':
        for c in (d.get('message') or {}).get('content') or []:
            if isinstance(c,dict) and c.get('type')=='tool_result' and c.get('tool_use_id') in pend:
                txt=c.get('content'); txt=json.dumps(txt) if not isinstance(txt,str) else txt
                nfiles=len(set(re.findall(r'[\w./-]+\.[A-Za-z]{1,5}(?=:)',txt)))
                cov={f for f in need if f in txt} if nfiles<=40 else set()
                res['n_search']+=1
                if len(cov)>res['max_cov']: res['max_cov']=len(cov)
                if need and cov==need and res['all_at_search'] is None:
                    res['all_at_search']=res['n_search']; res['all_at_call']=pend[c['tool_use_id']]
print(json.dumps(res))
