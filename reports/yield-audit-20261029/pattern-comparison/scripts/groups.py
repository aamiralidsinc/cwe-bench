import sys,csv,glob,collections
sys.path.insert(0, sys.argv[1]); from norm import run
batch = {}
for r in csv.DictReader(open('all-b1-b6.tsv'), delimiter='\t'): batch[r['task']] = (r['batch'], r['outcome'])
groups = collections.defaultdict(list)
for s,(b,o) in batch.items():
    p = f'main/build/{s}/BUILD-PROMPT.md'
    import os
    if os.path.exists(p): groups[b].append(p)
ev = '/Users/dev/terminal-bench/cwe-bench/diversity_population/out/audits/2026-10-28-chunk1/evidence'
groups['div-chunk1'] = glob.glob(ev+'/*/build/*/root/build/*/BUILD-PROMPT.md')
rows = run(groups)
w = csv.writer(open('prompt_hashes.tsv','w'), delimiter='\t')
w.writerow(['group','slug','hash','ver','pattern','track'])
for r in rows: w.writerow(r)
c = collections.Counter((r[0], r[3], r[2]) for r in rows)
for k,v in sorted(c.items()): print(k, v)
