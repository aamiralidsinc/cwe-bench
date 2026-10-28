"""Shared candidate index for every sourcer in the cwe-bench pipeline.

One SQLite file (index/candidates.sqlite) holds every record any sourcer has
looked at.  Nothing here is OSV-specific: a later sourcer (seeded search,
direct scan of GitHub history) uses the same three lookups before doing work:

    idx.seen_id("GHSA-xxxx" or "CVE-2026-1234")      -> entry_id or None
    idx.seen_commit("owner/repo", "<sha or prefix>")  -> entry_id or None
    idx.seen_repo("owner/repo")                       -> list of entry_ids

Tables
    entries     one row per vulnerability (a group of aliased advisory ids, or
                a bare repo+commit when a sourcer has no advisory)
    entry_ids   every advisory id / alias -> entry_id        (dedupe key 1)
    commits     every (repo, sha) looked at -> entry_id, with (dedupe key 2)
                the per-commit diff metrics
    runs        one row per stage execution with its funnel counts

Standard library only.
"""
import json
import os
import sqlite3
import time

SCHEMA_VERSION = 2

STATUSES = (
    "deferred",     # parsed, usable, but outside the recency window: not inspected yet
    "pending",      # inside the window, waiting for its diff to be fetched/classified
    "rejected",     # dropped; reject_reason says why
    "candidate",    # passed every filter and has a score
    "shortlisted",  # chosen for the current shortlist after a human/agent read
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS entries (
    entry_id       INTEGER PRIMARY KEY,
    sourcer        TEXT NOT NULL,      -- 'osv', later 'seeded', 'ghscan', ...
    primary_id     TEXT,               -- preferred advisory id (GHSA first); NULL if none
    ids            TEXT,               -- all advisory ids and aliases, space separated
    cve            TEXT,               -- CVE ids, space separated
    ecosystems     TEXT,               -- space separated
    packages       TEXT,               -- ' | ' separated  ecosystem:name
    repo           TEXT,               -- github owner/name, lower case
    fix_commits    TEXT,               -- every fix sha referenced, space separated
    n_fix_commits  INTEGER,
    fix_commit     TEXT,               -- the commit the metrics below describe (full sha)
    fix_commit_date TEXT,              -- author date of fix_commit, ISO (UTC)
    parent_commit  TEXT,               -- first parent of fix_commit = vulnerable state
    cwe_ids        TEXT,               -- space separated, e.g. 'CWE-22 CWE-59'
    published      TEXT,               -- ISO date of first publication
    modified       TEXT,
    severity       TEXT,               -- LOW / MODERATE / HIGH / CRITICAL
    cvss           TEXT,               -- vector string if present
    summary        TEXT,
    adv_signals    TEXT,               -- JSON: text signals taken from the advisory
    -- diff metrics of fix_commit
    src_files      INTEGER,
    src_added      INTEGER,
    src_removed    INTEGER,
    src_hunks      INTEGER,
    test_files     INTEGER,
    tests_in_fix   INTEGER,            -- 0/1
    other_files    INTEGER,            -- docs + manifests + lockfiles + config + ci + generated
    language       TEXT,               -- dominant language of the source change
    file_breakdown TEXT,               -- JSON: counts per file category
    -- optional repository facts (stage repo-meta)
    repo_stars     INTEGER,
    repo_size_kb   INTEGER,
    repo_flags     TEXT,
    -- difficulty signals: c_* are computed from diff/advisory, j_* are a reader's JUDGEMENT
    c_fix_sites            INTEGER, -- computed: hunks of the fix that change real source code
    c_site_files           INTEGER, -- computed: source files holding those hunks
    c_same_check_sites     INTEGER, -- computed: most sites that gained a call to one same new function
    c_same_check_name      TEXT,    -- computed: that function
    c_multi_site           INTEGER, -- computed 0/1: signal 1 proxy
    c_cause_layer_hint     INTEGER, -- computed 0/1: signal 2 proxy (advisory wording / fix spread over layers)
    c_defence_present      INTEGER, -- computed 0/1: signal 3 proxy (advisory wording or a modified check)
    c_modified_check_lines INTEGER, -- computed: removed lines that look like a condition/validator
    c_bypass_incomplete    INTEGER, -- computed 0/1: signal 4, advisory says earlier fix incomplete/bypassed
    c_sibling_advisories   INTEGER, -- computed: same package + shared CWE within 120 days
    c_class                TEXT,    -- computed from CWE ids: auth_session / authz / integrity / logic_design / other
    c_favoured_class       INTEGER, -- computed 0/1: signal 5
    c_single_compact_hunk  INTEGER, -- computed 0/1: signal 6 negative
    c_far_apart            INTEGER, -- computed 0/1: signal 6, hunks in 2+ files or >80 lines apart
    c_restructured         INTEGER, -- computed 0/1: signal 6, lines deleted/rewritten, not only added
    c_single_sink          INTEGER, -- computed 0/1: LOW signal, one injection sink fixed at one spot
    c_one_site_guard       INTEGER, -- computed 0/1: LOW signal, added-only guard in one compact hunk
    c_compact_small_repo   INTEGER, -- computed 0/1 (NULL when repo size unknown): LOW signal
    lang_tier              TEXT,    -- weakest (Java, Rust) / weak (Go, Ruby, PHP, C, C++) / strong (JS/TS) / python / other
    j_read                 INTEGER, -- JUDGEMENT 1 when a reviewer read advisory + diff
    j_multi_site           INTEGER, -- JUDGEMENT 0/1: signal 1
    j_sites_touched        TEXT,    -- JUDGEMENT: distinct sites the fix touched, as read
    j_sibling_sites        TEXT,    -- JUDGEMENT: yes / no / unknown, do sibling sites exist
    j_cause_other_layer    INTEGER, -- JUDGEMENT 0/1: signal 2
    j_defence_ineffective  INTEGER, -- JUDGEMENT 0/1: signal 3
    j_overbroad_breaks_legit INTEGER, -- JUDGEMENT 0/1: signal 7
    j_tempting_wrong_fix   TEXT,    -- JUDGEMENT: the plausible but wrong repair
    score_read             REAL,    -- score with the JUDGEMENT columns replacing the proxies for signals 1-3, 7
    shortlist_role         TEXT,    -- main / control when shortlisted
    -- outcome
    status         TEXT NOT NULL,
    reject_reason  TEXT,
    score          REAL,
    score_detail   TEXT,               -- JSON: signal -> points
    notes          TEXT,
    scanned_at     TEXT NOT NULL,      -- first time a sourcer recorded it (UTC)
    updated_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS entries_status ON entries(status);
CREATE INDEX IF NOT EXISTS entries_repo ON entries(repo);
CREATE INDEX IF NOT EXISTS entries_primary ON entries(primary_id);

CREATE TABLE IF NOT EXISTS entry_ids (
    id        TEXT PRIMARY KEY,        -- GHSA-..., CVE-..., PYSEC-..., GO-..., RUSTSEC-...
    entry_id  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS commits (
    repo          TEXT NOT NULL,       -- owner/name lower case
    sha           TEXT NOT NULL,       -- as referenced (may be abbreviated), lower case
    entry_id      INTEGER,
    source        TEXT,                -- 'reference' | 'git_range' | sourcer-specific
    full_sha      TEXT,
    parent_sha    TEXT,
    fetch_status  TEXT,                -- NULL = not fetched; 'ok' | 'http_404' | 'too_large' | ...
    is_merge      INTEGER,
    n_patches     INTEGER,             -- patch sections in the .patch (merge commits carry several)
    subject       TEXT,
    commit_date   TEXT,
    src_files     INTEGER,
    src_added     INTEGER,
    src_removed   INTEGER,
    src_hunks     INTEGER,
    test_files    INTEGER,
    other_files   INTEGER,
    language      TEXT,
    file_breakdown TEXT,
    src_paths     TEXT,                -- JSON list of changed source paths (first 40)
    shape         TEXT,                -- JSON from patchmetrics.shape_metrics
    fetched_at    TEXT,
    PRIMARY KEY (repo, sha)
);
CREATE INDEX IF NOT EXISTS commits_entry ON commits(entry_id);
CREATE INDEX IF NOT EXISTS commits_full ON commits(full_sha);

CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY,
    sourcer     TEXT,
    stage       TEXT,
    args        TEXT,
    started_at  TEXT,
    finished_at TEXT,
    counts      TEXT                   -- JSON funnel counts for that stage
);
"""

ADDED_COLUMNS = [
    ("c_fix_sites", "INTEGER"),
    ("c_site_files", "INTEGER"),
    ("c_same_check_sites", "INTEGER"),
    ("c_same_check_name", "TEXT"),
    ("c_multi_site", "INTEGER"),
    ("c_cause_layer_hint", "INTEGER"),
    ("c_defence_present", "INTEGER"),
    ("c_modified_check_lines", "INTEGER"),
    ("c_bypass_incomplete", "INTEGER"),
    ("c_sibling_advisories", "INTEGER"),
    ("c_class", "TEXT"),
    ("c_favoured_class", "INTEGER"),
    ("c_single_compact_hunk", "INTEGER"),
    ("c_far_apart", "INTEGER"),
    ("c_restructured", "INTEGER"),
    ("c_single_sink", "INTEGER"),
    ("c_one_site_guard", "INTEGER"),
    ("c_compact_small_repo", "INTEGER"),
    ("lang_tier", "TEXT"),
    ("j_read", "INTEGER"),
    ("j_multi_site", "INTEGER"),
    ("j_sites_touched", "TEXT"),
    ("j_sibling_sites", "TEXT"),
    ("j_cause_other_layer", "INTEGER"),
    ("j_defence_ineffective", "INTEGER"),
    ("j_overbroad_breaks_legit", "INTEGER"),
    ("j_tempting_wrong_fix", "TEXT"),
    ("score_read", "REAL"),
    ("shortlist_role", "TEXT"),
]

ENTRY_COLUMNS = [
    "entry_id", "sourcer", "primary_id", "ids", "cve", "ecosystems", "packages", "repo",
    "fix_commits", "n_fix_commits", "fix_commit", "fix_commit_date", "parent_commit", "cwe_ids", "published",
    "modified", "severity", "cvss", "summary", "adv_signals", "src_files", "src_added",
    "src_removed", "src_hunks", "test_files", "tests_in_fix", "other_files", "language",
    "file_breakdown", "repo_stars", "repo_size_kb", "repo_flags", "status", "reject_reason",
    "score", "score_detail", "notes", "scanned_at", "updated_at",
] + [name for name, _decl in ADDED_COLUMNS]


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def norm_repo(repo):
    """'https://github.com/Owner/Name.git' or 'Owner/Name' -> 'owner/name'."""
    r = (repo or "").strip()
    for prefix in ("https://", "http://", "git://", "git+", "ssh://git@", "git@"):
        if r.startswith(prefix):
            r = r[len(prefix):]
    if r.startswith("github.com/") or r.startswith("github.com:"):
        r = r[len("github.com/"):]
    r = r.strip("/")
    parts = r.split("/")
    if len(parts) < 2:
        return ""
    name = parts[1]
    if name.endswith(".git"):
        name = name[:-4]
    return (parts[0] + "/" + name).lower()


class Index(object):
    def __init__(self, path):
        d = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(d):
            os.makedirs(d)
        self.path = path
        self.db = sqlite3.connect(path, timeout=60)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        have = set(r[1] for r in self.db.execute("PRAGMA table_info(entries)"))
        for col, decl in [("fix_commit_date", "TEXT")] + ADDED_COLUMNS:   # added after version 1
            if col not in have:
                self.db.execute("ALTER TABLE entries ADD COLUMN %s %s" % (col, decl))
        if "shape" not in set(r[1] for r in self.db.execute("PRAGMA table_info(commits)")):
            self.db.execute("ALTER TABLE commits ADD COLUMN shape TEXT")
        self.db.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)",
                        (str(SCHEMA_VERSION),))
        self.db.commit()

    # ---- the general "have we seen this" lookups -------------------------
    def seen_id(self, any_id):
        row = self.db.execute("SELECT entry_id FROM entry_ids WHERE id = ?",
                              (any_id.strip().upper(),)).fetchone()
        return row[0] if row else None

    def seen_commit(self, repo, sha):
        """True for an exact sha, or when one is a prefix of the other (>= 7 chars)."""
        repo = norm_repo(repo)
        sha = (sha or "").strip().lower()
        if not repo or len(sha) < 7:
            return None
        row = self.db.execute(
            "SELECT entry_id FROM commits WHERE repo = ? AND "
            "(sha = ? OR full_sha = ? OR sha LIKE ? OR full_sha LIKE ? OR ? LIKE sha || '%') "
            "LIMIT 1", (repo, sha, sha, sha + "%", sha + "%", sha)).fetchone()
        return row[0] if row else None

    def seen_repo(self, repo):
        rows = self.db.execute("SELECT entry_id FROM entries WHERE repo = ?",
                               (norm_repo(repo),)).fetchall()
        return [r[0] for r in rows]

    # ---- writes ----------------------------------------------------------
    def add_entry(self, sourcer, ids, fields, commits=(), commit_source="reference"):
        """Insert one entry.  ids: list of advisory ids/aliases (may be empty).
        commits: list of shas in fields['repo'].  Returns entry_id."""
        t = now()
        fields = dict(fields)
        fields["sourcer"] = sourcer
        fields["ids"] = " ".join(ids)
        fields.setdefault("status", "pending")
        fields["scanned_at"] = t
        fields["updated_at"] = t
        cols = [c for c in ENTRY_COLUMNS if c in fields]
        cur = self.db.execute(
            "INSERT INTO entries (%s) VALUES (%s)" % (", ".join(cols), ", ".join("?" * len(cols))),
            [fields[c] for c in cols])
        eid = cur.lastrowid
        for i in ids:
            self.db.execute("INSERT OR IGNORE INTO entry_ids VALUES (?, ?)", (i.upper(), eid))
        repo = fields.get("repo") or ""
        for sha in commits:
            self.db.execute(
                "INSERT OR IGNORE INTO commits (repo, sha, entry_id, source) VALUES (?, ?, ?, ?)",
                (repo, sha.lower(), eid, commit_source))
        return eid

    def update_entry(self, entry_id, **fields):
        fields["updated_at"] = now()
        cols = sorted(fields)
        self.db.execute("UPDATE entries SET %s WHERE entry_id = ?" %
                        ", ".join(c + " = ?" for c in cols),
                        [fields[c] for c in cols] + [entry_id])

    def update_commit(self, repo, sha, **fields):
        cols = sorted(fields)
        self.db.execute("UPDATE commits SET %s WHERE repo = ? AND sha = ?" %
                        ", ".join(c + " = ?" for c in cols),
                        [fields[c] for c in cols] + [repo, sha])

    def start_run(self, sourcer, stage, args):
        cur = self.db.execute(
            "INSERT INTO runs (sourcer, stage, args, started_at) VALUES (?, ?, ?, ?)",
            (sourcer, stage, json.dumps(args, sort_keys=True), now()))
        self.db.commit()
        return cur.lastrowid

    def finish_run(self, run_id, counts):
        self.db.execute("UPDATE runs SET finished_at = ?, counts = ? WHERE run_id = ?",
                        (now(), json.dumps(counts, sort_keys=True), run_id))
        self.db.commit()

    def commit(self):
        self.db.commit()

    # ---- export ----------------------------------------------------------
    def export_tsv(self, path):
        """Flat TSV of the entries table, one row per record ever looked at."""
        def clean(v):
            if v is None:
                return ""
            return str(v).replace("\t", " ").replace("\r", " ").replace("\n", " ")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\t".join(ENTRY_COLUMNS) + "\n")
            for row in self.db.execute("SELECT %s FROM entries ORDER BY entry_id" %
                                       ", ".join(ENTRY_COLUMNS)):
                f.write("\t".join(clean(v) for v in row) + "\n")
        os.replace(tmp, path)
