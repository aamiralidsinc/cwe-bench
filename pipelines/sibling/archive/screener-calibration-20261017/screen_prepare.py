"""Prepare screener-v1 runs: candidate JSON + filled prompt per (model, host), and hosts.tsv.

The prompt is cut verbatim from builder/SCREENER-PROMPT-v1.md (between the ---8<--- markers) and
the lessons digest from its "## lessons-v1" code block; slots are filled by string replacement.
Nothing in the prompt is retyped here.

  python3 -I screen_prepare.py OUT_DIR --calibration --models opus sonnet fable \
      --remote-root /home/mara/screen
  python3 -I screen_prepare.py OUT_DIR --ids GHSA-... GHSA-... --models ...

--calibration takes the advisories from the prompt file's "Calibration set" table.
An entry rejected as duplicate_fix_commit_of_entry_N is screened with entry N's fix commit.
Reads the index read-only. No network.
"""
import argparse, json, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT = os.path.join(HERE, "..", "..", "builder", "SCREENER-PROMPT-v1.md")
DB = os.path.join(HERE, "..", "index", "candidates.sqlite")
MARK = "---8<---"
LESSONS_VERSION = "lessons-v1"


def cut(path):
    text = open(path, encoding="utf-8").read()
    parts = text.split(MARK)
    prompt = parts[1].strip("\n") + "\n"
    m = re.search(r"## lessons-v1 .*?```\n(.*?)\n```", text, re.S)
    if not m:
        raise SystemExit("lessons-v1 block not found")
    return text, prompt, m.group(1)


def calibration_rows(text):
    sec = text.split("### Calibration set", 1)[1].split("\n### ", 1)[0]
    rows = []
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.fullmatch(r"GHSA-[\w-]+", cells[1]):
            rows.append({"host": cells[0], "advisory": cells[1], "pattern": cells[2], "outcome": cells[3]})
    return rows


def candidate(con, adv):
    r = con.execute("select e.* from entry_ids i join entries e using(entry_id) where i.id = ?",
                    (adv.upper(),)).fetchone()
    if r is None:
        raise SystemExit(f"{adv}: not in the index")
    src, note = r, ""
    m = re.match(r"duplicate_fix_commit_of_entry_(\d+)", r["reject_reason"] or "")
    if m:
        src = con.execute("select * from entries where entry_id = ?", (int(m.group(1)),)).fetchone()
        note = f"fix commit shared with entry {src['entry_id']} ({src['primary_id']})"
    if not src["fix_commit"]:
        raise SystemExit(f"{adv}: no fix commit fetched yet (run the diffs stage)")
    cand = {
        "entry_id": r["entry_id"],
        "advisory_ids": (r["ids"] or "").split(),
        "repo": r["repo"],
        "cwe_ids": (r["cwe_ids"] or "").split(),
        "summary": r["summary"],
        "parent_commit": src["parent_commit"],
        "fix_commit": src["fix_commit"],
        "fix_commits": (src["fix_commits"] or "").split(),
        "published": r["published"],
    }
    for k in src.keys():
        if k.startswith("c_") and src[k] is not None:
            cand[k] = src[k]
    if note:
        cand["note"] = note
    return cand


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--calibration", action="store_true")
    g.add_argument("--ids", nargs="+")
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--remote-root", default="/home/mara/screen",
                    help="where hosts/ and runs/ live on the machine that runs the screener")
    ap.add_argument("--time-box", default="20")
    ap.add_argument("--prompt", default=PROMPT, help="screener prompt file (default v1)")
    a = ap.parse_args(argv)

    text, prompt, digest = cut(a.prompt)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    if a.calibration:
        rows = calibration_rows(text)
        advs = list(dict.fromkeys(r["advisory"] for r in rows))  # one screening per advisory
    else:
        rows, advs = [], a.ids
    os.makedirs(a.out, exist_ok=True)
    hosts = []
    for adv in advs:
        c = candidate(con, adv)
        eid = str(c["entry_id"])
        hdir = f"{a.remote_root}/hosts/{eid}"
        os.makedirs(os.path.join(a.out, "hosts", eid), exist_ok=True)
        json.dump(c, open(os.path.join(a.out, "hosts", eid, "candidate.json"), "w"), indent=1)
        hosts.append((eid, c["repo"], c["fix_commit"], c["parent_commit"] or "", adv))
        for model in a.models:
            run = f"{a.remote_root}/runs/{model}/{eid}"
            filled = (prompt
                      .replace("{{LESSONS_DIGEST}}", digest)
                      .replace("{{LESSONS_VERSION}}", LESSONS_VERSION)
                      .replace("{{CANDIDATE}}", json.dumps(c, indent=1))
                      .replace("{{CODE_LOCATION}}",
                               f"`{hdir}/repo` (the code at the pinned commit) and `{hdir}/fix.diff` "
                               f"(the published fix)")
                      .replace("{{LATEST_LOCATION}}", f"`{hdir}/latest` (see `{hdir}/latest.txt`)")
                      .replace("{{OUTPUT_PATH}}", f"`{run}/host.json`")
                      .replace("{{TIME_BOX_MIN}}", a.time_box))
            left = re.findall(r"\{\{[A-Z_]+\}\}", filled)
            if left:
                raise SystemExit(f"unfilled slots: {left}")
            d = os.path.join(a.out, "runs", model, eid)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "prompt.md"), "w").write(filled)
    with open(os.path.join(a.out, "hosts.tsv"), "w") as f:
        for h in hosts:
            f.write("\t".join(h) + "\n")
    if rows:  # labels stay local: they never go to the screening machine
        with open(os.path.join(a.out, "labels.tsv"), "w") as f:
            f.write("host\tadvisory\tpattern\toutcome\n")
            for r in rows:
                f.write("\t".join(r[k] for k in ("host", "advisory", "pattern", "outcome")) + "\n")
    print(f"{len(hosts)} hosts x {len(a.models)} models -> {a.out}")
    for h in hosts:
        print("  ", *h)


if __name__ == "__main__":
    sys.exit(main())
