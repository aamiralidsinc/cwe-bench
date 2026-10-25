#!/usr/bin/env python3
"""Pre-build breaker screener for the precision-validation experiment.

Reads ONLY from ../inputs (copies). Writes ONLY to ../results.

  python3 screen.py label    -> results/train_labels.csv  (the 50 DeepSeek-lane candidates + outcome)
  python3 screen.py loo      -> leave-one-out check of the rule on the 48 usable training rows
  python3 screen.py freeze   -> results/rule.json (rule fitted on all 48) + its sha256
  python3 screen.py score    -> results/predictions.csv for the 100 unseen pool entries

Label = first-build both-model breaker (both models fail 3/3, fairness + audit confirmed,
fairfix allowed, no hardening). typo3-ds and hermes-agent-ds are ambiguous and excluded.
Model = the one tested on 2026-10-22: 5 spread features thresholded (learned split) +
4 x smoothed breaker rate of the weakness family + 4 x smoothed breaker rate of the language.
"""
import csv, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, '..', 'inputs')
OUT = os.path.join(HERE, '..', 'results')

# Outcomes as of the 2026-10-21 register (inputs/pipeline/BREAKERS-20261021.md, AUTO-STATE.md).
BREAKERS = {'protobuf.js-ds', 'seaweedfs-ds', 'electron-builder-ds', 'litellm-ds', 'mockoon-ds',
            'hubuum-client-rust-ds', 'siyuan-ds', 'theia-ds', 'openbao-ds', 'tinacms-ds',
            'knowns-ds', 'yamcs-ds'}
AMBIGUOUS = {'typo3-ds', 'hermes-agent-ds'}
AUTHZ = {'862', '863', '639', '285', '287', '306', '269', '829', '640', '284', '441'}
PATH = {'22', '73'}
SPREAD = ['entry_points', 'd_files', 'd_pkgs', 'fix_min', 'inj_n']


def j(x):
    if isinstance(x, str):
        try:
            return json.loads(x)
        except ValueError:
            return x
    return x


def lang(l):
    l = (l or '').lower()
    if 'typescript' in l or l.startswith('javascript'):
        return 'js/ts'
    for k in ('go', 'python', 'php', 'java', 'rust'):
        if l.startswith(k):
            return k
    return 'other'


def features(p):
    d = j(p.get('distance')) or {}
    d = d if isinstance(d, dict) else {}
    cwes = re.findall(r'CWE-(\d+)', p.get('family', ''))
    cwe = cwes[0] if cwes else '?'
    return dict(entry=p['entry_id'], repo=p.get('repo'), cwe=cwe,
                fam='authz' if cwe in AUTHZ else 'path' if cwe in PATH else 'other',
                L=lang(p.get('language')),
                entry_points=p.get('entry_points') or 0, d_files=d.get('files') or 0,
                d_pkgs=d.get('packages') or 0, fix_min=p.get('fix_minutes') or 0,
                inj_n=p.get('injection_room_n') or 0)


def pool():
    return [json.loads(l) for l in open(os.path.join(IN, 'pipeline', 'pool.jsonl'))]


def train_rows():
    by_entry = {p['entry_id']: p for p in pool()}
    rows = []
    for f in sorted(os.listdir(os.path.join(IN, 'pipeline', 'specs_deepseek'))):
        s = json.load(open(os.path.join(IN, 'pipeline', 'specs_deepseek', f)))
        r = features(by_entry[s['entry_id']])
        r.update(slug=s['slug'], y=int(s['slug'] in BREAKERS), amb=s['slug'] in AMBIGUOUS)
        rows.append(r)
    return rows


def fit(train):
    th = {}
    for f in SPREAD:
        best = None
        for t in sorted({r[f] for r in train}):
            hi = [r['y'] for r in train if r[f] >= t]
            lo = [r['y'] for r in train if r[f] < t]
            if len(hi) < 5 or len(lo) < 5:
                continue
            gap = sum(hi) / len(hi) - sum(lo) / len(lo)
            if best is None or gap > best[0]:
                best = (gap, t)
        th[f] = best[1] if best else 0

    def rates(key):
        vals = {r[key] for r in train}
        return {v: (sum(r['y'] for r in train if r[key] == v) + 1) /
                   (sum(1 for r in train if r[key] == v) + 4) for v in vals}
    return dict(thresholds=th, fam_rate=rates('fam'), lang_rate=rates('L'), prior=1 / 4)


def score(r, rule):
    s = sum(r[f] >= rule['thresholds'][f] for f in SPREAD)
    s += 4 * rule['fam_rate'].get(r['fam'], rule['prior'])
    s += 4 * rule['lang_rate'].get(r['L'], rule['prior'])
    return round(s, 4)


def usable():
    return [r for r in train_rows() if not r['amb']]


def cmd_label():
    rows = train_rows()
    with open(os.path.join(OUT, 'train_labels.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} rows, {sum(r['y'] for r in rows)} breakers, {sum(r['amb'] for r in rows)} ambiguous")


def cmd_loo():
    use = usable()
    sc = sorted(((score(r, fit(use[:i] + use[i + 1:])), r['y']) for i, r in enumerate(use)), reverse=True)
    n, P = len(sc), sum(y for _, y in sc)
    print(f"base rate {P}/{n} = {P / n:.0%}")
    for keep in (0.3, 0.4, 0.5, 0.7):
        k = round(n * keep); tp = sum(y for _, y in sc[:k])
        print(f"keep top {keep:.0%} ({k}): {tp}/{P} breakers kept, precision {tp / k:.0%}")


def cmd_freeze():
    use = usable()
    rule = fit(use)
    tr = sorted((score(r, rule) for r in use), reverse=True)
    rule['bar_top40_train'] = tr[round(len(tr) * 0.4) - 1]   # absolute score bar = training top-40% cut
    rule['trained_on'] = f"{len(use)} DeepSeek-lane candidates, {sum(r['y'] for r in use)} breakers"
    blob = json.dumps(rule, indent=1, sort_keys=True)
    open(os.path.join(OUT, 'rule.json'), 'w').write(blob)
    h = hashlib.sha256(blob.encode()).hexdigest()
    open(os.path.join(OUT, 'rule.sha256'), 'w').write(h + '\n')
    print(blob); print('sha256', h)


def cmd_score():
    rule = json.load(open(os.path.join(OUT, 'rule.json')))
    seen = {json.load(open(os.path.join(IN, 'pipeline', 'specs_deepseek', f)))['entry_id']
            for f in os.listdir(os.path.join(IN, 'pipeline', 'specs_deepseek'))}
    rows = [features(p) for p in pool() if p['entry_id'] not in seen]
    for r in rows:
        r['score'] = score(r, rule)
        r['above_bar'] = int(r['score'] >= rule['bar_top40_train'])
    rows.sort(key=lambda r: -r['score'])
    for i, r in enumerate(rows, 1):
        r['rank'] = i
    with open(os.path.join(OUT, 'predictions.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['rank', 'entry', 'repo', 'score', 'above_bar', 'fam', 'cwe', 'L'] + SPREAD)
        w.writeheader(); w.writerows({k: r[k] for k in w.fieldnames} for r in rows)
    print(f"{len(rows)} unseen scored; {sum(r['above_bar'] for r in rows)} above the bar ({rule['bar_top40_train']})")


def cmd_score_stacking():
    """Score the stacking H3 entries from results/pool_stacking21.jsonl (screener_v2/make_pool.py output)."""
    rule = json.load(open(os.path.join(OUT, 'rule.json')))
    rows = [features(json.loads(l)) for l in open(os.path.join(OUT, 'pool_stacking21.jsonl'))]
    for r in rows:
        r['score'] = score(r, rule)
        r['above_bar'] = int(r['score'] >= rule['bar_top40_train'])
    rows.sort(key=lambda r: -r['score'])
    with open(os.path.join(OUT, 'predictions_stacking21.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['entry', 'repo', 'score', 'above_bar', 'fam', 'cwe', 'L'] + SPREAD)
        w.writeheader(); w.writerows({k: r[k] for k in w.fieldnames} for r in rows)
    print(f"{len(rows)} stacking entries scored; {sum(r['above_bar'] for r in rows)} above the bar")


if __name__ == '__main__':
    {'label': cmd_label, 'loo': cmd_loo, 'freeze': cmd_freeze, 'score': cmd_score,
     'score-stacking': cmd_score_stacking}[sys.argv[1]]()
