import csv,json
DIV={'openemr':'breaker','seanime':'breaker','laravel-mongodb':'one','databasement':'one','mingo':'one','open-web-analytics':'one'}
DIV_SOLVED_EXTRA={'relevanssi','a2a-rs','phplist3','laravel-medialibrary'}
def outcome_map():
    o={}
    for r in csv.DictReader(open('all-b1-b6.tsv'),delimiter='\t'):
        x=r['outcome']
        c={'S_both':'solved_both','S_ds_only':'one','S_mimo_only':'one','B_delivered':'breaker','B_kept':'breaker','B_dropped':'bothfail_unfair','B_withdrawn':'bothfail_unfair'}.get(x,'none')
        o[r['task']]=(r['batch'],c,x)
    v=json.load(open('/Users/dev/terminal-bench/cwe-bench/diversity_population/out/regrade-chunk1/verdicts.json'))
    vs={x['task'] for x in v}
    import os
    for s in os.listdir('/Users/dev/terminal-bench/cwe-bench/diversity_population/out/audits/2026-10-28-chunk1/tasks'):
        short=s.replace('diversity-','')
        if short in DIV: c=DIV[short]
        elif s in vs: c='solved_both'
        else: c='none'
        o[s]=('div-chunk1',c,c)
    return o
