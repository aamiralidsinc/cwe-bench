import csv,collections,statistics
rows=list(csv.DictReader(open('review_rows.tsv'),delimiter='\t'))
G=['div-chunk1','scale-b5','scale-b6','scale-b3','scale-b1']
OC=['solved_both','one','breaker','bothfail_unfair']
def grp(r): return 'b5-6' if r['group'] in ('scale-b5','scale-b6') else r['group']
GG=['div-chunk1','b5-6','scale-b3','scale-b1']
def show(title,f):
    print('\n##',title)
    print('group | all | '+' | '.join(OC))
    for g in GG:
        rs=[r for r in rows if grp(r)==g]
        def cell(sub):
            n=len(sub); k=sum(1 for r in sub if f(r)); return f'{k}/{n} ({100*k/n:.0f}%)' if n else '-'
        print(g,'|',cell(rs),'|',' | '.join(cell([r for r in rs if r['outcome']==o]) for o in OC))
show('one_search ALL', lambda r:r['one_search']=='ALL')
show('one_search ALL or MOST', lambda r:r['one_search'] in('ALL','MOST'))
show('injected same idiom >=1 (reviewer count)', lambda r:(int(r['n_inj_same'] or 0))>=1)
show('has injected sites', lambda r:int(r['n_inj'])>0)
show('one_guard YES', lambda r:r['one_guard']=='YES')
show('listing FAIL', lambda r:r['listing']=='FAIL')
show('any hidden NAMED', lambda r:int(r['named'])>0)
show('spec>=4', lambda r:int(r['spec'] or 0)>=4)
show('weak: one_search ALL or one_guard YES or listing FAIL', lambda r:r['one_search']=='ALL' or r['one_guard']=='YES' or r['listing']=='FAIL')
show('clean: none of ALL/MOST, guard YES, listing FAIL', lambda r:not(r['one_search'] in ('ALL','MOST') or r['one_guard']=='YES' or r['listing']=='FAIL'))
print()
for g in GG:
    rs=[r for r in rows if grp(r)==g]
    sp=[int(r['spec']) for r in rs if r['spec']]
    nd=sum(int(r['named'])+int(r['described']) for r in rs); nh=sum(int(r['n_hidden']) for r in rs)
    print(g,'spec mean',round(statistics.mean(sp),2),'dist',sorted(collections.Counter(sp).items()),'hidden traps named/described',nd,'/',nh, f'{100*nd/nh:.0f}%', 'traps median',statistics.median(int(r['n_traps']) for r in rs))
