import hashlib, pathlib
root = pathlib.Path("/workspace")
lines = (root / "pyproject.toml").read_text().splitlines()
files, inside = [], False
for line in lines:
    t = line.strip()
    if not inside and t.startswith("[tool.uv.workspace]"):
        inside = True
    elif inside:
        if t.startswith("#"):
            continue
        if t.startswith('"'):
            path = t.split('"')[1]
            if t.startswith('"providers/'):
                files += [root / path / "pyproject.toml", root / path / "provider.yaml"]
        elif t.startswith("]"):
            break
h = hashlib.sha256()
for f in sorted(files):
    h.update(f.read_bytes())
(root / "generated" / "provider_dependencies.json.sha256sum").write_text(h.hexdigest())
