# common/markers.sh: shell twin of common/markers.py for the gate and pipeline scripts. Source it:
#   . "$CWE_COMMON/markers.sh"
# Every function takes the build folder (build/<slug>) first. Names and meanings: common/markers.py (MARKERS),
# contracts: common/stage_contracts.toml, docs/STAGE-CONTRACTS.md.

# Create a flag file (empty marker); never truncates an existing one.
cwe_mark() { [ -e "$1/$2" ] || : > "$1/$2"; }

# Remove markers; missing ones are fine.
cwe_unmark() { local b=$1; shift; local n; for n in "$@"; do rm -f "$b/$n"; done; }

# Exactly one gate verdict flag: .sound | .unsound | .gate_error (gate_one_ds.sh's rule).
cwe_gate_verdict() {
  case "$2" in .sound|.unsound|.gate_error) ;; *) echo "cwe_gate_verdict: bad flag $2" >&2; return 2 ;; esac
  rm -f "$1/.sound" "$1/.unsound" "$1/.gate_error"; : > "$1/$2"
}

# The gate passed: hold trials (.gate_passed) until the post-gate checks are done.
cwe_hold_after_gate() { mv -f "$1/.sound" "$1/.gate_passed" 2>/dev/null; return 0; }

# All post-gate checks done: the task is sound.
cwe_mark_sound() { rm -f "$1/.gate_passed"; : > "$1/.sound"; }

# Stacking: the listing check still fails; the task is not sound.
cwe_mark_listing_fail() { rm -f "$1/.sound" "$1/.gate_passed" "$1/.listing_warn"; : > "$1/.listing_fail"; }

# Write a record file atomically (readers see the old or the new content, never half of it).
cwe_write_atomic() { local t; t=$(mktemp "$(dirname "$1")/.$(basename "$1").XXXXXX") && cat > "$t" && mv -f "$t" "$1"; }

# Is a marker or record file present (a regular file, like the scripts' `[ -f ... ]` tests)?
cwe_has() { [ -f "$1/$2" ]; }

# Print a record file; non-zero (and nothing printed) when it is missing, like `cat ... 2>/dev/null`.
cwe_read() { cat "$1/$2" 2>/dev/null; }

# Write the current UTC time (YYYY-MM-DDTHH:MM:SSZ) into a record file atomically (start_utc.txt, end_utc.txt, ...).
cwe_stamp() { date -u +%FT%TZ | cwe_write_atomic "$1/$2"; }

# Slugs whose build folder holds marker $1 (under $CWE_BUILD), one per line.
cwe_tasks_with() { local f; for f in "$CWE_BUILD"/*/"$1"; do [ -e "$f" ] && basename "$(dirname "$f")"; done; return 0; }
