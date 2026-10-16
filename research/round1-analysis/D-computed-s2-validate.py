"""Computed S2 (S2a, S2b) on the built round-1 tasks: research/round1-analysis/D-computed-s2.md.

Offline. Computes S2a from the advisory text (dumps) and from instruction.md against each task's
solution/fix.patch, S2b from fix.patch, and prints the index's own S2 labels for the advisory.

    python3 -I research/round1-analysis/D-computed-s2-validate.py [<extracted Hadi MCP task dir>]

The Hadi task comes from Hadi/mcp-ts-sdk-oauth-issuer-confusion_deepseek.zip (extract it outside
the repo, e.g. into a scratch directory, and pass .../mcp-ts-sdk-oauth-issuer-confusion_deepseek/task).
Note: S2b on a stacking or sibling task's combined fix.patch pairs sites of DIFFERENT flaws and is
not meaningful; the report uses the per-advisory values for those.
"""
import sys, json, os, re, glob, sqlite3, zipfile
sys.path.insert(0, '/Users/dev/terminal-bench/cwe-bench/sourcer')
import osv_sourcer as o, patchmetrics as pm
ROOT = '/Users/dev/terminal-bench/cwe-bench'
D = os.path.expanduser('~/.tb-graders/cwe/sourcer-data/dumps')
db = sqlite3.connect(ROOT + '/sourcer/index/candidates.sqlite'); db.row_factory = sqlite3.Row
zips = {e: zipfile.ZipFile(os.path.join(D, e + '.zip')) for e in o.ECOSYSTEMS}
def adv_text(aid):
    for z in zips.values():
        try:
            a = json.loads(z.read(aid + '.json')); return (a.get('summary') or '') + '\n' + (a.get('details') or '')
        except KeyError: pass
    return None
def entry(aid):
    return db.execute("select e.* from entry_ids i join entries e using(entry_id) where i.id=?", (aid.upper(),)).fetchone()
def label(shape):
    b = shape.get('s2b') or {}
    return ('S2b' + ('-strict' if b.get('strict') else '-loose') + ('+dir' if b.get('diff_dir') else '')) if b.get('fires') else '-'
HADI = sys.argv[1] if len(sys.argv) > 1 else ''   # extracted .../mcp-ts-sdk-oauth-issuer-confusion_deepseek/task
tasks = sorted(os.listdir(ROOT + '/tasks')) + (['HADI-mcp'] if HADI else [])
res = {}
for t in tasks:
    tdir = HADI if t == 'HADI-mcp' else ROOT + '/tasks/' + t
    fix = open(tdir + '/solution/fix.patch', errors='replace').read()
    if 'diff --git' not in fix:   # plain unified diff: add the git header parse_patch expects
        fix = re.sub(r'(?m)^--- a/(\S+)\n\+\+\+ b/(\S+)$', lambda m: 'diff --git a/%s b/%s\n%s' % (m.group(1), m.group(2), m.group(0)), fix)
    instr = open(tdir + '/instruction.md', errors='replace').read()
    instr = re.sub(r'`?/(app|opt)(/[\w./-]*)?`?', ' ', instr)   # container paths, not locations
    shape = pm.parse_patch(fix)['shape']
    man = {} if t == 'HADI-mcp' else json.load(open(ROOT + '/build/%s/manifest.json' % t))
    txt = json.dumps(man)
    ids = sorted(set(re.findall(r'GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}', txt))) if t != 'HADI-mcp' else ['GHSA-6qxp-vccf-f47h']
    repo = (man.get('candidate') or {}).get('repo', '') or ''
    repo = re.sub(r'^https://github.com/', '', repo).lower()
    advs = [adv_text(i) or '' for i in ids]
    sig_adv = {'named': o.named_locations('\n'.join(advs))} if any(advs) else {}
    sig_ins = {'named': o.named_locations(instr)}
    a_adv = o.s2a_signal(sig_adv, shape, repo) if sig_adv else {'state': 'n/a'}
    a_ins = o.s2a_signal(sig_ins, shape, repo)
    idx = []
    for i in ids:
        e = entry(i)
        if e is not None and e['status'] in ('candidate', 'shortlisted'):
            det = json.loads(e['score_detail']); det = det.get('computed', det)
            s2 = [k for k in det if k.startswith('S2a') or k.startswith('S2b')]
            idx.append((i, s2))
    res[t] = dict(ids=ids, a_adv=a_adv, a_ins=a_ins, s2b=shape['s2b'], lab=label(shape), idx=idx,
                  units=shape['units'], named_ins=sig_ins['named'], named_adv=sig_adv.get('named'))
    print('==', t, '| fixpatch S2a(adv)=%s S2a(instr)=%s %s' % (a_adv['state'], a_ins['state'], label(shape)))
    print('   instr named:', json.dumps(sig_ins['named'])[:250])
    print('   adv named  :', json.dumps(sig_adv.get('named'))[:250])
    b = shape['s2b']
    if b['fires']: print('   s2b check:', b['check_files'][:3], b['check_names'][:4], '| prod:', b['producer_files'][:3], b['producer_names'][:4])
    for i, s2 in idx: print('   index', i, s2)
