import csv,re,json,collections,sys
rows=list(csv.DictReader(open('prompt_hashes.tsv'),delimiter='\t'))
ev='/Users/dev/terminal-bench/cwe-bench/diversity_population/out/audits/2026-10-28-chunk1/evidence'
import glob
divp={f.split('/')[-2]:f for f in glob.glob(ev+'/*/build/*/root/build/*/BUILD-PROMPT.md')}
out=[]
for r in rows:
    f = divp[r['slug']] if r['group']=='div-chunk1' else f"main/build/{r['slug']}/BUILD-PROMPT.md"
    t=open(f,errors='replace').read()
    m=re.search(r'The screener\'s record.*?```json\n(.*?)\n\s*```',t,re.S)
    rec={}
    if m:
        try: rec=json.loads(m.group(1))
        except Exception as e: rec={'_err':str(e)[:40]}
    ub = re.search(r'Uncovered routes to confirm \(pattern B\):(.*?)\n- Design plan',t,re.S)
    nub = len(re.findall(r'\n\s+- ', '\n'+ub.group(1))) if ub else 0
    fs = re.search(r'Published fix sites:(.*?)\n- (Uncovered|Design)',t,re.S)
    nfs = len(re.findall(r'\n\s+- ', '\n'+fs.group(1))) if fs else 0
    lead = 'No lead plan is provided' in t
    out.append((r['group'], r['slug'], rec.get('screener_version','?'), rec.get('lessons_version','?'), rec.get('model','?'), nfs, nub, lead, rec.get('score', rec.get('total','')) ))
w=csv.writer(open('inputs.tsv','w'),delimiter='\t'); w.writerow(['group','slug','sv','lv','model','n_fix_sites','n_uncovered','self_design','score']); w.writerows(out)
c=collections.Counter((o[0],o[2],o[3],o[4],o[7]) for o in out)
for k,v in sorted(c.items()): print(k,v)
import statistics
for g in sorted(set(o[0] for o in out)):
    xs=[o[6] for o in out if o[0]==g]; ys=[o[5] for o in out if o[0]==g]
    print(g,'uncovered median',statistics.median(xs),'mean',round(statistics.mean(xs),2),'fixsites median',statistics.median(ys))
