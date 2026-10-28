"""divq releases: build an encrypted payload from one cwe-bench commit + the batch's prepared BUILD-PROMPTs.

A release is a read-only, content-addressed payload (its id is the payload's sha256). The build workflow decrypts
it on the runner and runs the pipeline's own scripts from it, so a build on Actions uses the same code as the VM.
Activating a release repoints `release.current`; running jobs keep the release they started on; rollback repoints.

The payload carries code only (git archive, no run data) plus, under build/<slug>/, a BUILD-PROMPT.md prepared by
that same code's `common/builder/build_prepare.py` from the diversity screener record — so the prompt always matches
the code. The runner path the prompts name is `runner_root` (default /tmp/divq/root), masked in the public log.

  divq release build  <commit> [--note TEXT]
  divq release list
  divq release activate <id>
  divq release rollback
"""
import csv, hashlib, json, os, shutil, subprocess, tarfile, tempfile
from pathlib import Path

import divq_core as core

CWE = core.DIV.parent                 # .../cwe-bench
RUNNER_ROOT = "/tmp/divq/root"        # where the payload decrypts on the runner; baked into the prompts


def _slugs(s):
    """(slug, entry_id, pattern_fit) for every batch task, pattern_fit from its screener record."""
    out = []
    for r in csv.DictReader(open(s.p("chunks") / "all_chunks.tsv"), delimiter="\t"):
        rec_path = s.p("results").parent / "screener" / f"{r['entry_id']}.json"
        pat = "A+B"
        if rec_path.is_file():
            pf = json.loads(rec_path.read_text()).get("pattern_fit")
            pat = pf if pf in ("A", "B", "A+B") else "A+B"
        out.append((r["slug"], r["entry_id"], pat))
    return out


def _prepare(s, root):
    """Write root/build/<slug>/BUILD-PROMPT.md for every batch slug, via the archived build_prepare.py."""
    recs_dir = root / "common" / "screener" / "records"
    recs_dir.mkdir(parents=True, exist_ok=True)
    plan = (root / "pipelines" / "sibling" / "5-prepare" / "SELFDESIGN-PLAN.md").read_text().strip()
    prep = root / "common" / "builder" / "build_prepare.py"
    ids, specdir = {}, root / "build" / "_specs"
    specdir.mkdir(parents=True, exist_ok=True)
    done = 0
    for i, (slug, eid, pat) in enumerate(_slugs(s), 1):
        src_rec = s.p("results").parent / "screener" / f"{eid}.json"
        if not src_rec.is_file():
            print("skip (no screener record):", slug); continue
        shutil.copy2(src_rec, recs_dir / f"{eid}.json")
        rec = json.loads(src_rec.read_text())
        adv = rec.get("advisory_ids"); adv = adv if isinstance(adv, str) else json.dumps(adv)
        fc = rec.get("fix_commits"); fc = fc if isinstance(fc, list) else ([fc] if fc else ["(none)"])
        spec = {"slug": slug, "entry_id": eid, "pattern": pat, "track": "injected",
                "advisory": f"{adv}; {rec.get('repo','')}; {rec.get('O9_family','')}",
                "vuln_commit": str(rec.get("pinned_commit", "(see record)")), "fix_commits": fc,
                "design_plan": plan, "host_notes": "none", "project_root": RUNNER_ROOT}
        sp = specdir / f"{slug}.json"; sp.write_text(json.dumps(spec, indent=1))
        r = subprocess.run(["python3", "-I", str(prep), str(sp)], cwd=str(root), capture_output=True, text=True)
        if r.returncode == 0 and (root / "build" / slug / "BUILD-PROMPT.md").is_file():
            ids[f"d{i:03d}"] = slug; done += 1
        else:
            print("prepare failed:", slug, r.stderr.strip()[:160])
    (root / "ids.json").write_text(json.dumps(ids, indent=1))
    (root / "pv_path").write_text(RUNNER_ROOT)       # the runner path the prompts name (masked in the log)
    shutil.rmtree(specdir, ignore_errors=True)
    return done, len(ids)


def build(s, c, commit, note=""):
    key_file = s.p("key_file")
    if not key_file.is_file():
        raise SystemExit(f"payload key missing: {key_file} (create: openssl rand -base64 48 > FILE; chmod 600 FILE)")
    sha = subprocess.run(["git", "-C", str(CWE), "rev-parse", commit], capture_output=True, text=True, check=True).stdout.strip()
    rel_dir = s.p("releases"); rel_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "root"; root.mkdir()
        # code only: git archive excludes the (gitignored) data folders
        arch = subprocess.run(["git", "-C", str(CWE), "archive", sha], capture_output=True)
        if arch.returncode:
            raise SystemExit("git archive failed")
        with tarfile.open(fileobj=__import__("io").BytesIO(arch.stdout)) as tf:
            tf.extractall(root, filter="data")
        n_prompts, n_ids = _prepare(s, root)
        tgz = Path(td) / "payload.tar.gz"
        with tarfile.open(tgz, "w:gz") as tf:
            tf.add(root, arcname="root")
        rid = hashlib.sha256(tgz.read_bytes()).hexdigest()[:12]
        out = rel_dir / rid; out.mkdir(parents=True, exist_ok=True)
        enc = out / "payload.tgz.gpg"
        subprocess.run(["gpg", "--batch", "--quiet", "--pinentry-mode", "loopback", "--passphrase-file",
                        str(key_file), "--symmetric", "--cipher-algo", "AES256", "-o", str(enc), str(tgz)], check=True)
        meta = {"id": rid, "commit": sha, "created": core.utc(), "tasks": n_ids, "prompts": n_prompts,
                "payload_bytes": enc.stat().st_size, "note": note, "runner_root": RUNNER_ROOT}
        (out / "RELEASE.json").write_text(json.dumps(meta, indent=1))
    c.execute("INSERT OR REPLACE INTO releases(id,created,commit_sha,tasks,payload,payload_bytes,note) "
              "VALUES(?,?,?,?,?,?,?)", (rid, meta["created"], sha, n_ids, str(enc), meta["payload_bytes"], note))
    print(json.dumps(meta, indent=1))
    return rid


def activate(s, c, rid, reason="activate"):
    if not c.execute("SELECT 1 FROM releases WHERE id=?", (rid,)).fetchone():
        raise SystemExit(f"no such release: {rid} (divq release list)")
    prev = core.kv_get(c, "release.current")
    if prev:
        core.kv_set(c, "release.previous", prev)
    core.kv_set(c, "release.current", rid)
    c.execute("INSERT INTO release_log VALUES(?,?,?,?)", (core.utc(), prev or "", rid, reason))
    print(f"active release: {rid}" + (f" (was {prev})" if prev else ""))


def rollback(s, c):
    prev = core.kv_get(c, "release.previous")
    if not prev:
        raise SystemExit("no previous release to roll back to")
    activate(s, c, prev, reason="rollback")


def payload_path(s, c, rid):
    r = c.execute("SELECT payload FROM releases WHERE id=?", (rid,)).fetchone()
    return r["payload"] if r else None
