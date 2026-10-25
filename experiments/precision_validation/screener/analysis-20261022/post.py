import json,os,re,glob,statistics as st
R='/private/tmp/claude-501/-Users-dev-terminal-bench/8fe2c226-bbaf-4e42-97ca-80d166c4414f/scratchpad/share/cwe-bench-share-20261021/repo-vm'
rows=json.load(open(os.path.dirname(os.path.abspath(__file__))+'/rows.json'))
def auc(xs,ys):
    pos=[x for x,y in zip(xs,ys) if y]; neg=[x for x,y in zip(xs,ys) if not y]
    return sum((a>b)+0.5*(a==b) for a in pos for b in neg)/(len(pos)*len(neg))
def ntests(d):
    n=0
    for f in glob.glob(d+'/**/*',recursive=True):
        if not os.path.isfile(f) or '/project/' in f: continue
        try: t=open(f,errors='ignore').read()
        except: continue
        n+=len(re.findall(r'^\s*(?:async\s+)?def test_|^\s*func Test|@Test\b|^\s*(?:it|test)\(|#\[test\]|#\[tokio::test',t,re.M))
    return n
for r in rows:
    s=r['slug']; m={}
    try: m=json.load(open(f'{R}/build/{s}/manifest.json'))
    except: pass
    ver=m.get('verified',{}) or {}
    sites=ver.get('sites',[]) if isinstance(ver,dict) else []
    r['sites']=len(sites)
    r['inj_sites']=sum(1 for x in sites if 'inject' in x.lower())
    r['traps']=len(m.get('traps') or [])
    r['wrongfix']=len(m.get('wrong_fix_catalogue') or [])
    r['patches']=len(m.get('patch_checks') or [])
    ins=f'{R}/tasks/{s}/instruction.md'
    r['instr_words']=len(open(ins).read().split()) if os.path.exists(ins) else 0
    r['sec_tests']=ntests(f'{R}/tasks/{s}/tests/security')
    r['fun_tests']=ntests(f'{R}/tasks/{s}/tests/functional')
    sp=f'{R}/tasks/{s}/tests/score.py'
    t=open(sp).read() if os.path.exists(sp) else ''
    r['fun_zero']=int('reward = 0.0' in t or 'forced to 0' in t)
    r['coupled_traps']=sum(1 for x in (m.get('traps') or []) if re.search(r'coupl|keep|legit|over-?block|preserv',json.dumps(x),re.I))
json.dump(rows,open(os.path.dirname(os.path.abspath(__file__))+'/rows2.json','w'),indent=1)
use=[r for r in rows if not r['amb']]; ys=[r['y'] for r in use]
for k in ['sites','inj_sites','traps','coupled_traps','wrongfix','patches','instr_words','sec_tests','fun_tests','fun_zero']:
    xs=[r[k] for r in use]
    print(f"{k:14} AUC={auc(xs,ys):.2f} breaker med={st.median([x for x,y in zip(xs,ys) if y])} other med={st.median([x for x,y in zip(xs,ys) if not y])}")
