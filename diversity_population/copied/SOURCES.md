# Copied files

One row per file copied from the main pipeline. Only the copy is run or changed.

| Copy | Original path | Copied from commit | Changes |
|---|---|---|---|
| copied/sourcer/osv_sourcer.py | sourcer/osv_sourcer.py | 75d3f696 | 2026-10-28: sends `GITHUB_TOKEN` (from the environment, if set) to api.github.com only, and lifts the repo-meta budget of 55 when a token is set |
| copied/sourcer/index_db.py | sourcer/index_db.py | 75d3f696 | none |
| copied/sourcer/patchmetrics.py | sourcer/patchmetrics.py | 75d3f696 | none |
| copied/sourcer/weights.json | sourcer/weights.json | 75d3f696 | none |
| copied/sourcer/review/annotations.tsv | sourcer/review/annotations.tsv | 75d3f696 | none |
| copied/docs/research/cwe_top25_2025.tsv | docs/research/cwe_top25_2025.tsv | 75d3f696 | none (kept at the same relative path the copied weights.json expects) |
| copied/docs/research/cwe_attack_classes.tsv | docs/research/cwe_attack_classes.tsv | 75d3f696 | none (kept at the same relative path the copied weights.json expects) |
| copied/docs/research/owasp2025_cwe_map.json | docs/research/owasp2025_cwe_map.json | 75d3f696 | none (kept at the same relative path the copied weights.json expects) |
| copied/docs/research/cwe_hierarchy.tsv | docs/research/cwe_hierarchy.tsv | 75d3f696 | none (kept at the same relative path the copied weights.json expects) |
| out/index/candidates.sqlite | sourcer/reserve/index/candidates.sqlite (the sources2 index, 2026-10-24 22:29) | data, not in git | statuses reset by prepare_index.py (see README) |
| copied/screener/run_screener.py | common/screener/run_screener.py | ff4d1e7c | no import of common/paths.py (runs outside the checkout; work folder from DIV_WORK, default ~/.tb-graders/cwe/diversity), own folders (records in out/screener, jobs in out/screener_jobs.jsonl, clones and trees under ~/.tb-graders/cwe/diversity/), uses the copied prompt, fills {{PATTERN_HINT}}, deletes each worktree and fix diff when its job ends and the clone after the repo's last job, waits while the disk has under 8 GB free. Picking (--pick, with its DoS skip) is not used: the job list is written by make_screener_jobs.py |
| copied/screener/SCREENER-PROMPT-v2.md | common/screener/SCREENER-PROMPT-v2.md | ff4d1e7c | one input line added: the per-pattern "where sibling sites usually are" hint (patterns.json other_places_hint), marked as a pointer, not evidence |
| copied/sibling/3-rank/rerank.py | pipelines/sibling/3-rank/rerank.py | f4239081 | no import of common/paths.py (unused); reads the sourcer weights from the copied sourcer (--sourcer-weights) instead of <db>/../weights.json |
| copied/sibling/3-rank/screen-weights.json | pipelines/sibling/3-rank/screen-weights.json | f4239081 | none |
| copied/sibling/3-rank/validate_screen.py | pipelines/sibling/3-rank/validate_screen.py | f4239081 | reads the screener prompts from copied/screener/ instead of common/ (no common/paths.py), so it runs outside the checkout |
| copied/sibling/4-select/make_pool.py | pipelines/sibling/4-select/make_pool.py | f4239081 | no common/paths.py; --recs, --out and an optional --ids list instead of fixed paths |
| copied/sibling/4-select/select.sh | pipelines/sibling/4-select/select.sh | f4239081 | pool, output folder and N are arguments; uses the copied drive.sh and prompt; claude from CLAUDE_BIN; falls back to gtimeout or a perl alarm where timeout(1) is missing (macOS). Model call, prompt assembly and answer parsing unchanged |
| copied/sibling/4-select/SELECT-PROMPT.md | pipelines/sibling/4-select/SELECT-PROMPT.md | f4239081 | none |
| copied/sibling/4-select/combine.py | pipelines/sibling/4-select/combine.py | f4239081 | none |
| copied/launch/drive.sh | common/launch/drive.sh | f4239081 | no common/paths.sh; key file from CWE_MODELS_ENV |
| copied/screener/SCREENER-PROMPT-v1.md | common/archive/old-prompts/SCREENER-PROMPT-v1.md | f4239081 | none (the validator copy's fallback prompt) |
| actions/reference/* (10 files) | experiments/precision_validation/actions/ (local only, not in git; files dated 2026-10-22/24) | n/a | none: unchanged reference copies; mapping in actions/README.md section 9. Not run. |
