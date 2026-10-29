import sys,re,hashlib,os,glob,csv,collections
def norm(t, slug):
    # drop Inputs section
    t = re.sub(r'\n## Inputs\n.*?(?=\n## )', '\n## Inputs\n<INPUTS>\n', t, flags=re.S)
    t = re.sub(r'Project root: `[^`]*`\. Task: `[^`]*`\. Pattern: `[^`]*`\. Track: `[^`]*`\.', 'PROJECTLINE', t)
    t = t.replace(slug, '<SLUG>')
    t = re.sub(r'/home/[^ `\)]*cwe-bench-releases/[0-9a-f]+', '<ROOT>', t)
    t = re.sub(r'/home/runner[^ `\)]*', '<ROOT>', t)
    return t
out = {}
def run(paths_by_group):
    rows=[]
    for g, paths in paths_by_group.items():
        for p in paths:
            slug = p.rstrip('/').split('/')[-2]
            t = open(p, errors='replace').read()
            n = norm(t, slug)
            h = hashlib.sha1(n.encode()).hexdigest()[:8]
            pl = re.search(r'Pattern: `([^`]*)`\. Track: `([^`]*)`', t)
            ver = re.search(r'\((build-[^)]*)\)', t.splitlines()[0])
            rows.append((g, slug, h, ver.group(1) if ver else '?', pl.group(1) if pl else '?', pl.group(2) if pl else '?'))
            d = 'norm/'+h; os.makedirs('norm', exist_ok=True)
            open(d+'.md','w').write(n)
    return rows
