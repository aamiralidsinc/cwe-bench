import json,glob,sys,collections,csv
sys.path.insert(0,'../scripts'); from outcomes import outcome_map
o=outcome_map(); key=json.load(open('packet_key.json'))
R={}
for f in glob.glob('results/c*.jsonl'):
    for l in open(f):
        if l.strip(): d=json.loads(l); R[d['id']]=d
rows=[]
for pid,d in R.items():
    s,g=key[pid]; oc=o[s][1]
    traps=d.get('traps',[])
    hidden=[t for t in traps if not t.get('is_advisory_route')]
    cov=collections.Counter(str(t.get('coverage','')).upper() for t in hidden)
    lfail = cov['NAMED']>0 or cov['DESCRIBED']>1
    nd = cov['NAMED']+cov['DESCRIBED']
    inj=[t for t in traps if t.get('injected')]
    inj_hit=sum(1 for t in inj if t.get('search_hit'))
    rows.append(dict(pid=pid,slug=s,group=g,outcome=oc,n_traps=len(traps),n_hidden=len(hidden),
        named=cov['NAMED'],described=cov['DESCRIBED'],general=cov['GENERAL'],absent=cov['ABSENT'],listing=('FAIL' if lfail else 'PASS'),
        one_search=d.get('one_search'),n_inj=len(inj),n_inj_hit=inj_hit,
        n_inj_same=d.get('n_injected_same_idiom'),n_inj_rep=d.get('n_injected_sites'),
        one_guard=d.get('one_guard'),spec=d.get('instr_specificity'),
        chokepoint=d.get('chokepoint',''),why=d.get('one_guard_why',''),note=d.get('note','')))
w=csv.DictWriter(open('review_rows.tsv','w'),fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
print(len(rows))
