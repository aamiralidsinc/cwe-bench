#!/usr/bin/env python3
"""Final analysis, fixed before any build (pre-registered in PREREGISTRATION.md).

Input: results/outcomes.csv, filled from build/audit_results.py at the end (one row per slug):
  slug, build_ok (1 = gated sound and trialed, 0 = build or gate failed), breaker (1 = both models
  failed 3/3, fairness READY, audited; 0 otherwise). Hardening never applies.

  python3 -I analyze.py            -> prints the report and writes results/REPORT.md
"""
import csv, json, os, sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.dirname(HERE)
RES = os.path.join(PV, 'results')


def fisher_one_sided(a, n1, c, n2):
    """P(arm 1 has >= a successes | both margins fixed): one-sided test that arm 1 > arm 2."""
    k, n = a + c, n1 + n2
    return sum(comb(k, i) * comb(n - k, n1 - i) for i in range(a, min(k, n1) + 1)) / comb(n, n1)


def auc(pairs):
    pos = [s for s, y in pairs if y]; neg = [s for s, y in pairs if not y]
    if not pos or not neg:
        return None
    return sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg))


def reading(ra, rb, p):
    if ra <= rb:
        return 'NOT VALIDATED: A <= B; do not build the pipeline around the score'
    if p < 0.10 and ra - rb >= 0.10 and (rb == 0 or ra >= 1.5 * rb):
        return 'VALIDATED: A > B (p < 0.10), at least 10 points and 1.5x'
    return 'PARTIAL: A > B but short of the validated bar; keep the score as a soft prior and refit'


def main():
    slugs = {r['slug']: r for r in csv.DictReader(open(os.path.join(RES, 'build_slugs.csv')))}
    out = {r['slug']: r for r in csv.DictReader(open(os.path.join(RES, 'outcomes.csv')))}
    missing = [s for s, r in slugs.items() if r['arm'] in 'AB' and s not in out]
    if missing:
        sys.exit(f'outcomes missing for {len(missing)} arm A/B slugs, e.g. {missing[:5]}')
    score = {}
    for f in ('predictions.csv', 'predictions_stacking21.csv'):
        for r in csv.DictReader(open(os.path.join(RES, f))):
            score[r['entry']] = float(r['score'])
    lines, stats = ['# Precision validation: result', ''], {}
    for arm in 'ABC':
        rows = [(s, r) for s, r in slugs.items() if r['arm'] == arm and s in out]
        n = len(rows); y = sum(int(out[s]['breaker']) for s, _ in rows)
        ok = [s for s, _ in rows if out[s]['build_ok'] == '1']; yo = sum(int(out[s]['breaker']) for s in ok)
        stats[arm] = (y, n)
        if n:
            lines.append(f"- Arm {arm}: {y}/{n} breakers = {y / n:.0%} (intent to treat); "
                         f"{yo}/{len(ok)} = {yo / max(1, len(ok)):.0%} per sound task")
    (ya, na), (yb, nb) = stats['A'], stats['B']
    ra, rb = ya / na, yb / nb
    p = fisher_one_sided(ya, na, yb, nb)
    lines += ['', f'- A vs B: {ra:.0%} vs {rb:.0%}; difference {100 * (ra - rb):.0f} points; '
                  f'ratio {ra / rb if rb else float("inf"):.2f}; one-sided Fisher p = {p:.3f}',
              f'- Reading: **{reading(ra, rb, p)}**',
              f'- Context: A {"reached" if ya >= 9 else "did not reach"} 9/21 (the yield target on its own)']
    a = auc([(score[slugs[s]['entry']], int(out[s]['breaker'])) for s in slugs if slugs[s]['arm'] in 'AB' and s in out])
    lines.append(f'- AUC of the frozen score over arms A+B: {a:.2f}' if a is not None else '- AUC: undefined (one class)')
    pp = os.path.join(RES, 'postbuild_predictions.csv')
    if os.path.exists(pp):
        lines.append('')
        for k in ('primary', 'secondary'):
            pr = [r for r in csv.DictReader(open(pp)) if r['arm'] in 'AB' and r['slug'] in out]
            sel = [r for r in pr if r[f'pred_{k}'] == '1']; hit = sum(int(out[r['slug']]['breaker']) for r in sel)
            tot = sum(int(out[r['slug']]['breaker']) for r in pr)
            lines.append(f'- Post-build {k}: predicted {len(sel)}, of which {hit} breakers '
                         f'(precision {hit / max(1, len(sel)):.0%}; keeps {hit}/{tot} breakers)')
    rep = '\n'.join(lines) + '\n'
    open(os.path.join(RES, 'REPORT.md'), 'w').write(rep)
    print(rep)


if __name__ == '__main__':
    main()
