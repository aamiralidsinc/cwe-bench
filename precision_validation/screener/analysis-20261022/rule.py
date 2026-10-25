import json,os,collections,itertools,random
rows=json.load(open(os.path.dirname(os.path.abspath(__file__))+'/rows2.json'))
AUTHZ={'862','863','639','285','287','306','269','829','640','284','441'}
def lang(l):
    l=l.lower()
    for k in ['typescript','javascript','go','python','php','java','rust']:
        if l.startswith(k) or (k=='typescript' and 'typescript' in l): return 'js/ts' if k in('typescript','javascript') else k
    return 'other'
for r in rows:
    r['L']=lang(r['lang']); r['fam']='authz' if r['cwe'] in AUTHZ else ('path' if r['cwe'] in('22','73') else 'other')
use=[r for r in rows if not r['amb']]
for k in ['L','fam']:
    c=collections.defaultdict(lambda:[0,0])
    for r in use: c[r[k]][0]+=r['y']; c[r[k]][1]+=1
    print(k,{a:f"{b[0]}/{b[1]}" for a,b in c.items()})
# pre-build score: features, each binary vs threshold learned in-fold
F=['entry_points','d_files','d_pkgs','fix_min','inj_n']
def fit(train):
    th={}
    for f in F:
        best=None
        for t in sorted(set(r[f] or 0 for r in train)):
            hi=[r['y'] for r in train if (r[f] or 0)>=t]; lo=[r['y'] for r in train if (r[f] or 0)<t]
            if len(hi)<5 or len(lo)<5: continue
            gap=sum(hi)/len(hi)-sum(lo)/len(lo)
            if best is None or gap>best[0]: best=(gap,t)
        th[f]=best[1] if best else 0
    rate=lambda key,v:( (sum(r['y'] for r in train if r[key]==v)+1)/(sum(1 for r in train if r[key]==v)+4) )
    return th,rate,train
def score(r,model):
    th,rate,train=model
    return sum((r[f] or 0)>=th[f] for f in F) + 4*rate('fam',r['fam']) + 4*rate('L',r['L'])
# leave-one-out
sc=[]
for i,r in enumerate(use):
    m=fit(use[:i]+use[i+1:]); sc.append((score(r,m),r['y'],r['slug']))
sc.sort(reverse=True)
n=len(sc); P=sum(y for _,y,_ in sc)
print(f"base rate {P}/{n} = {P/n:.0%}")
for keep in [0.3,0.4,0.5,0.6,0.7]:
    k=round(n*keep); kept=sc[:k]; tp=sum(y for _,y,_ in kept)
    print(f"keep top {keep:.0%} ({k}): breakers {tp}/{P} kept, precision {tp/k:.0%}")
print([ (round(s,2),y,sl) for s,y,sl in sc])
