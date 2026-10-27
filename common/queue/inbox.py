"""The decisions inbox: one page of every decision waiting on the owner.

    cweq inbox                 print it
    cweq inbox --html PATH     write it as one self-contained HTML file (no external assets)

Sections, all read from the files (taskstate, fairness_verdict, HUMAN-DECISION.md, the job table, prepared delivery
packages); nothing is inferred beyond what those say:
  1. keep           both models failed, audited, fairness READY: KEEP / REPAIR / DROP (the reviewer's human-review
                    question is quoted from FAIRNESS.md when there is one)
  2. not_ready      fairness NOT_READY: repair or drop (the reviewer's required change is quoted)
  3. deliver        KEEP recorded, not delivered yet (with the prepared package when delivery_prep has run)
  4. blocked        queue jobs blocked for a person
  5. person         tasks the pipeline cannot move on its own: listing check failed, trials stuck
"""
import html
import json
import re

import qdb
from taskstate import paths

SECTIONS = (
    ("keep", "Keep, repair or drop", "Both models failed every run, the failing runs are audited, and the fairness "
                                     "review is READY."),
    ("not_ready", "Fairness not ready", "The fairness review asks for a change: repair or drop."),
    ("deliver", "Kept, not delivered yet", "KEEP is recorded; the task is not in the delivery register."),
    ("blocked", "Blocked jobs", "Queue jobs that stopped for a person."),
    ("person", "Needs a person", "Tasks the pipeline cannot move on its own."),
)


def _read(p):
    try:
        return p.read_text(errors="replace")
    except OSError:
        return ""


def quote(slug, *labels):
    """The paragraph after the first `<label>:` line in build/<slug>/FAIRNESS.md (the reviewer's own words)."""
    text = _read(paths.BUILD / slug / "FAIRNESS.md")
    for label in labels:
        m = re.search(rf"(?ims)^[\W_]*{label}[\W_]*:?[*_]*\s*(.+?)(?:\n\s*\n|\n#|\nGATE_A|\nNEEDS_HUMAN|\Z)", text)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()[:700]
    return ""


def scores(t):
    out = []
    for m in ("deepseek", "mimo"):
        mm = t["models"].get(m, {})
        out.append(f"{m} {mm.get('ledger') or mm.get('launch') or '-'}")
    return ", ".join(out)


def collect(conn, states, packages=None):
    """{section: [item dict]} — each item has task, summary and detail."""
    items = {k: [] for k, _t, _d in SECTIONS}
    pk = {}
    for p in packages or []:
        pk.setdefault(p.get("slug"), p)                 # newest first: keep the newest per task
    for slug, t in sorted(states.items()):
        st = t["stage"]
        if st == "awaiting_decision":
            q = quote(slug, "Human review")
            items["keep"].append({"task": slug, "summary": f"fairness {t['fairness'].split(':')[0]}; {scores(t)}",
                                  "detail": f"Reviewer asks: {q}" if q else "No question from the reviewer."})
        elif st == "fairness_not_ready":
            q = quote(slug, "Required change", "Human review")
            items["not_ready"].append({"task": slug, "summary": f"{t['fairness'][:160]}; {scores(t)}",
                                       "detail": q or "See FAIRNESS.md."})
        elif st == "kept":
            p = pk.get(slug)
            if p:
                d = (f"Package {'ready' if p.get('ready') else 'NOT ready: ' + '; '.join(p.get('problems', []))} at "
                     f"{p.get('out')} as `{p.get('name')}`; rollouts {p.get('rollouts')}")
            else:
                d = "No package prepared yet (delivery_prep)."
            items["deliver"].append({"task": slug, "summary": f"{t['decision']}; {scores(t)}", "detail": d})
        elif st in ("listing_fail", "trials_stuck"):
            items["person"].append({"task": slug, "summary": st.replace("_", " "), "detail": t["next"]})
    for r in conn.execute("SELECT * FROM jobs WHERE state='blocked' ORDER BY id"):
        items["blocked"].append({"task": r["task"], "summary": f"job #{r['id']} {r['kind']} {qdb.canon(qdb.args_of(r))[:120]}",
                                 "detail": r["result"] or ""})
    return items


def text(items, stamp=None):
    out = [f"Decisions inbox ({stamp or qdb.utc()})"]
    for key, head, desc in SECTIONS:
        rows = items.get(key, [])
        out.append("")
        out.append(f"== {head} ({len(rows)}) — {desc}")
        for it in rows:
            out.append(f"  {it['task']}: {it['summary']}")
            if it["detail"]:
                out.append(f"      {it['detail']}")
    return "\n".join(out) + "\n"


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a66;--line:#e3e0d8;--card:#fff;--acc:#2f5d50}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--mut:#a3a19a;--line:#33322f;--card:#1f1f1d;--acc:#8fc3b0}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,Segoe UI,Helvetica,Arial,sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 16px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 4px}
.mut{color:var(--mut)}.n{color:var(--acc);font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:8px 0}
.task{font-family:ui-monospace,Menlo,monospace;font-size:14px;font-weight:600;overflow-wrap:anywhere}
.d{margin-top:4px;overflow-wrap:anywhere}
"""


def page(items, stamp=None):
    e = html.escape
    total = sum(len(v) for v in items.values())
    body = [f"<h1>Decisions inbox</h1><p class='mut'>{e(stamp or qdb.utc())} · {total} items</p>"]
    for key, head, desc in SECTIONS:
        rows = items.get(key, [])
        body.append(f"<h2>{e(head)} <span class='n'>{len(rows)}</span></h2><p class='mut'>{e(desc)}</p>")
        if not rows:
            body.append("<p class='mut'>Nothing waiting.</p>")
        for it in rows:
            body.append(f"<div class='card'><div class='task'>{e(it['task'])}</div><div>{e(it['summary'])}</div>"
                        + (f"<div class='d mut'>{e(it['detail'])}</div>" if it["detail"] else "") + "</div>")
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'><title>Decisions inbox</title>"
            f"<style>{CSS}</style></head><body><main>{''.join(body)}</main></body></html>\n")


def as_json(items):
    return json.dumps(items, indent=2)
