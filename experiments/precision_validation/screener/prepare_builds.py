#!/usr/bin/env python3
"""Write one build spec + BUILD-PROMPT.md per candidate of arms A, B and group C.

Modelled on the VM's pipeline/prepare_lane.py (10-21 snapshot): the same constant self-design plan
for every candidate (root/builder/SELFDESIGN-PLAN.md), track=injected, pattern from the screener
record. Differences: slugs are `pv-<repo>` (no arm, no score: the builder is blind to both), the
records and template are the frozen copies under root/, and the arm map is kept OUTSIDE root/.

  python3 -I prepare_builds.py [--project-root /home/mara/cwe-bench/precision_validation/root]

Writes root/build/<slug>/{spec.json,BUILD-PROMPT.md}, results/build_slugs.csv (slug -> arm, entry,
build order), and results/prompt_checks.csv (integrity checks per prompt).
"""
import argparse, csv, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.dirname(HERE)
ROOT = os.path.join(PV, 'root')
RES = os.path.join(PV, 'results')
PLAN = open(os.path.join(ROOT, 'builder', 'SELFDESIGN-PLAN.md')).read().strip()
PREPARE = os.path.join(ROOT, 'sourcer', 'build_prepare.py')
SURFACE_RULE = 'Pick wording that cannot be read as one surface.'   # last line of the rule in the template
LIST_ALL = 'First list EVERY possible sibling site and route'        # latest SELFDESIGN-PLAN step


def arms():
    out = []
    for arm, f in (('A', 'arm_A_above_bar.csv'), ('B', 'arm_B_control.csv')):
        for r in csv.DictReader(open(os.path.join(RES, f))):
            out.append(dict(arm=arm, entry=r['entry'], repo=r['repo'], build_order=int(r['build_order'])))
    for i, e in enumerate(('17039', '18845'), 1):   # group C: stacking-sourced, above the bar
        rec = json.load(open(os.path.join(ROOT, 'screener_records', f'{e}.json')))
        out.append(dict(arm='C', entry=e, repo=rec['repo'], build_order=i))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-root', default='/home/mara/cwe-bench/precision_validation/root')
    a = ap.parse_args()
    rows, used = arms(), set()
    for r in rows:
        rec = json.load(open(os.path.join(ROOT, 'screener_records', f"{r['entry']}.json")))
        base = 'pv-' + rec['repo'].split('/')[-1].lower().replace('_', '-').replace('.', '-')
        slug = base if base not in used else f"{base}-{r['entry']}"
        used.add(slug); r['slug'] = slug
        pf = rec.get('pattern_fit') if rec.get('pattern_fit') in ('A', 'B', 'A+B') else 'A+B'
        adv = rec.get('advisory_ids'); adv = adv if isinstance(adv, str) else json.dumps(adv)
        fc = rec.get('fix_commits'); fc = fc if isinstance(fc, list) else ([fc] if fc else ['(none given)'])
        spec = {'slug': slug, 'entry_id': r['entry'], 'pattern': pf, 'track': 'injected',
                'advisory': f"{adv}; {rec['repo']}; {rec.get('O9_family', '')}",
                'vuln_commit': str(rec.get('pinned_commit', '(see record)')),
                'fix_commits': fc, 'design_plan': PLAN, 'host_notes': 'none', 'project_root': a.project_root}
        d = os.path.join(ROOT, 'build', slug); os.makedirs(d, exist_ok=True)
        sp = os.path.join(d, 'spec.json'); json.dump(spec, open(sp, 'w'), indent=1)
        rc = subprocess.run([sys.executable, '-I', PREPARE, sp], capture_output=True, text=True)
        r['prepare_rc'] = rc.returncode
        if rc.returncode:
            print('prepare failed:', slug, rc.stderr.strip()[-200:])
    checks = []
    for r in rows:
        p = os.path.join(ROOT, 'build', r['slug'], 'BUILD-PROMPT.md')
        t = open(p).read() if os.path.exists(p) else ''
        checks.append(dict(slug=r['slug'], arm_hidden_in_prompt=int(not re.search(r'above_bar|predictions|arm_[ABC]|bar_top40|rule\.json|build_slugs|results/', t)),
                           unfilled_slots=len(re.findall(r'\{\{[A-Z_]+\}\}', t)), surface_rule=int(SURFACE_RULE in t),
                           list_all_step=int(LIST_ALL in t), root_ok=int(f"Project root: `{a.project_root}`" in t),
                           words=len(t.split())))
    with open(os.path.join(RES, 'build_slugs.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['arm', 'build_order', 'slug', 'entry', 'repo', 'prepare_rc'])
        w.writeheader(); w.writerows(sorted(({k: r[k] for k in w.fieldnames} for r in rows), key=lambda x: (x['arm'], x['build_order'])))
    with open(os.path.join(RES, 'prompt_checks.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(checks[0].keys())); w.writeheader(); w.writerows(checks)
    ok = [c for c in checks if c['unfilled_slots'] == 0 and c['surface_rule'] and c['list_all_step'] and c['root_ok']]
    print(f"{len(rows)} prompts; {len(ok)} pass integrity checks; "
          f"{sum(1 for c in checks if not c['arm_hidden_in_prompt'])} mention arm/score words (review)")


if __name__ == '__main__':
    main()
