#!/usr/bin/env python3
"""Post-build checkpoint: extract task features after the gate and BEFORE any trial, then predict.

  python3 -I postbuild.py freeze    -> results/postbuild_rule.json + .sha256 (done once, before any build)
  python3 -I postbuild.py extract   -> results/postbuild.csv (needs root/build + root/tasks after gating)
  python3 -I postbuild.py predict   -> results/postbuild_predictions.csv + .sha256 (run BEFORE trials)

Features are computed exactly as in the 2026-10-22 analysis (screener/analysis-20261022/post.py):
sites = len(manifest.verified.sites); traps = len(manifest.traps); patches = len(manifest.patch_checks);
instr_words = words in tasks/<slug>/instruction.md; test functions per group, vendored project/ excluded.
"""
import csv, glob, hashlib, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.dirname(HERE)
ROOT = os.path.join(PV, 'root')
RES = os.path.join(PV, 'results')
TEST_RE = r'^\s*(?:async\s+)?def test_|^\s*func Test|@Test\b|^\s*(?:it|test)\(|#\[test\]|#\[tokio::test'

# Pre-registered thresholds, taken from the 48 training tasks (in-sample: sites >= 9 -> 9/17 breakers;
# instruction >= 500 words -> 8/13). The instruction threshold comes from builds without the
# latest builder's wording rules, so it is the weaker of the two and reported as secondary.
RULE = {'primary': {'feature': 'sites', 'min': 9},
        'secondary': {'feature': 'instr_words', 'min': 500},
        'note': 'thresholds from batch 2 (48 tasks); sites>=9 9/17, instr_words>=500 8/13, in-sample'}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def ntests(d):
    n = 0
    for f in glob.glob(d + '/**/*', recursive=True):
        if os.path.isfile(f) and '/project/' not in f:
            n += len(re.findall(TEST_RE, open(f, errors='ignore').read(), re.M))
    return n


def gate_state(b):
    if os.path.exists(os.path.join(b, '.sound')):
        return 'sound'
    if os.path.exists(os.path.join(b, '.unsound')):
        return 'unsound'
    return 'no-gate'


def cmd_freeze():
    p = os.path.join(RES, 'postbuild_rule.json')
    json.dump(RULE, open(p, 'w'), indent=1, sort_keys=True)
    open(p + '.sha256', 'w').write(sha(p) + '\n')
    print('frozen', p, sha(p)[:16])


def cmd_extract():
    rows = []
    for r in csv.DictReader(open(os.path.join(RES, 'build_slugs.csv'))):
        s = r['slug']; b = os.path.join(ROOT, 'build', s); t = os.path.join(ROOT, 'tasks', s)
        m = {}
        try:
            m = json.load(open(os.path.join(b, 'manifest.json')))
        except (OSError, ValueError):
            pass
        ver = m.get('verified') if isinstance(m.get('verified'), dict) else {}
        ins = os.path.join(t, 'instruction.md')
        rows.append(dict(slug=s, arm=r['arm'], gate=gate_state(b), has_manifest=int(bool(m)),
                         sites=len(ver.get('sites') or []), traps=len(m.get('traps') or []),
                         patches=len(m.get('patch_checks') or []),
                         instr_words=len(open(ins).read().split()) if os.path.exists(ins) else 0,
                         sec_tests=ntests(os.path.join(t, 'tests', 'security')),
                         fun_tests=ntests(os.path.join(t, 'tests', 'functional'))))
    with open(os.path.join(RES, 'postbuild.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} rows; gates: {dict((g, sum(r['gate'] == g for r in rows)) for g in ('sound', 'unsound', 'no-gate'))}")


def cmd_predict():
    rule = json.load(open(os.path.join(RES, 'postbuild_rule.json')))
    if sha(os.path.join(RES, 'postbuild_rule.json')) != open(os.path.join(RES, 'postbuild_rule.json.sha256')).read().strip():
        sys.exit('postbuild_rule.json changed since it was frozen')
    rows = list(csv.DictReader(open(os.path.join(RES, 'postbuild.csv'))))
    for r in rows:
        for k in ('primary', 'secondary'):
            f = rule[k]
            r[f'pred_{k}'] = int(r['gate'] == 'sound' and int(r[f['feature']]) >= f['min'])
    out = os.path.join(RES, 'postbuild_predictions.csv')
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    open(out + '.sha256', 'w').write(f"{sha(out)}  written {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    print(f"predicted; primary positives {sum(r['pred_primary'] for r in rows)}, secondary {sum(r['pred_secondary'] for r in rows)}")


if __name__ == '__main__':
    {'freeze': cmd_freeze, 'extract': cmd_extract, 'predict': cmd_predict}[sys.argv[1]]()
