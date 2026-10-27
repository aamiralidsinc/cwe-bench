"""Settings history: every version of the settings file the queue loaded, in the `settings` table.

The TOML file in git (common/queue/queue.toml) stays the source of the values in force. A version is the sha256 of the
file's bytes (16 hex digits, config.file_hash). The reconcile, dispatch and monitor loops record the version they start
with and, at every tick, notice a changed file: they record the new version and continue with it. Every job records
the version its worker started with (jobs.settings_hash), so `cweq explain` shows which settings a job ran under and
`cweq config` shows the current version and the history.
"""
import subprocess
from pathlib import Path

import config
import qdb


def git_commit(path):
    """Short commit of the repository holding the file, '+local' when the file differs from that commit; None outside
    git."""
    d = str(Path(path).resolve().parent)
    try:
        head = subprocess.run(["git", "-C", d, "rev-parse", "--short=12", "HEAD"], capture_output=True, text=True,
                              timeout=10)
        if head.returncode != 0 or not head.stdout.strip():
            return None
        dirty = subprocess.run(["git", "-C", d, "diff", "--quiet", "HEAD", "--", str(Path(path).resolve())],
                               capture_output=True, timeout=10).returncode != 0
        return head.stdout.strip() + ("+local" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return None


def record(conn, cfg, by):
    """Record (or touch) the version cfg was loaded from. Returns its hash."""
    h, now = cfg.get("_settings_hash"), qdb.utc()
    if not h:
        return None
    with qdb.tx(conn):
        cur = conn.execute("INSERT OR IGNORE INTO settings (hash, file, git_commit, text, first_loaded, last_loaded,"
                           " loads, loaded_by) VALUES (?,?,?,?,?,?,0,?)",
                           (h, cfg.get("_file"), None, cfg.get("_settings_text", ""), now, now, by))
        new = cur.rowcount == 1
        conn.execute("UPDATE settings SET last_loaded=?, loads=loads+1, loaded_by=? WHERE hash=?", (now, by, h))
    if new:                                          # git runs outside the write lock
        conn.execute("UPDATE settings SET git_commit=? WHERE hash=?", (git_commit(cfg.get("_file", "")), h))
    return h


def current_hash(cfg):
    p = Path(cfg.get("_file", ""))
    return config.file_hash(p.read_bytes() if p.is_file() else b"")


def refresh(conn, cfg, by):
    """(cfg, changed): the settings reloaded and recorded when the file changed since cfg was loaded."""
    try:
        if current_hash(cfg) == cfg.get("_settings_hash"):
            return cfg, False
        new = config.load(cfg["_file"])
    except Exception:                                # a half-written or invalid file: keep the settings in force
        return cfg, False
    for k in ("db",):                                # a running loop keeps its database
        new[k] = cfg[k]
    record(conn, new, by)
    return new, True


def history(conn, limit=20):
    return conn.execute("SELECT hash, file, git_commit, first_loaded, last_loaded, loads, loaded_by FROM settings"
                        " ORDER BY first_loaded DESC, rowid DESC LIMIT ?", (limit,)).fetchall()


def text_of(conn, prefix):
    row = conn.execute("SELECT hash, text FROM settings WHERE hash LIKE ? ORDER BY first_loaded DESC LIMIT 1",
                       (prefix + "%",)).fetchone()
    return row
