"""Repo locations for cwe-bench: the single source of truth.

Every Python script that needs another part of the repo imports this module instead of building paths from its own
location. If a file moves, only this module changes. The shell twin is common/paths.sh; keep the two in step.

Import it from any script, at any depth:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
    import paths  # noqa: E402

The repo root is the folder holding the `.cwe-bench-root` marker file. On the VM that is ~/cwe-bench.

Code and data (versioned releases, docs/RELEASES.md): ROOT is the folder this code runs from (CODE_ROOT). Run data
(build/, tasks/, reports/, the pipelines' out/ folders, ...) lives under DATA_ROOT. DATA_ROOT comes from
$CWE_DATA_ROOT, else from the `.cwe-data-root` file a release writes next to its `.cwe-bench-root`, else it is ROOT
itself (a plain checkout, as before). A release also links each data folder back to DATA_ROOT, so repo-relative paths
such as `build/<slug>` work from either root.
"""
import os
from pathlib import Path


def _find_root() -> Path:
    here = Path(__file__).resolve().parent
    for d in (here, *here.parents):
        if (d / ".cwe-bench-root").is_file():
            return d
    raise RuntimeError("cwe-bench root not found: no .cwe-bench-root marker above " + str(here))


def _find_data_root(code_root: Path) -> Path:
    env = os.environ.get("CWE_DATA_ROOT", "").strip()
    if env:
        return Path(env).expanduser()
    marker = code_root / ".cwe-data-root"
    if marker.is_file():
        text = marker.read_text().strip()
        if text:
            return Path(text).expanduser()
    return code_root


ROOT = _find_root()
CODE_ROOT = ROOT                          # the code this process runs (a release, or a plain checkout)
DATA_ROOT = _find_data_root(ROOT)         # the shared run data (== ROOT outside releases)

# Data folders: never part of a release; a release links each one to DATA_ROOT (common/util/release.py).
DATA_PATHS = (
    "build", "tasks", "reports", "experiments",
    "sourcer/index", "sourcer/reserve/index", "sourcer/reserve/out",
    "pipelines/router/out", "pipelines/sibling/out", "pipelines/stacking/out",
    "pipelines/stacking/1-select/calibration",
    "common/screener/records", "common/archive/logs", "docs/peers",
)

# ---- run data (stays at the data root; never moved)
BUILD = DATA_ROOT / "build"               # build/<slug>/: build records, markers, manifests
TASKS = DATA_ROOT / "tasks"               # tasks/<slug>/: the Harbor task packages
BUILD_PIPELINE = BUILD / "pipeline"       # batch-1 lane state, night logs
AUDIT_DIR = BUILD / "audit"               # ledger.md, reviews.tsv, awaiting_audit.tsv
REPORTS = DATA_ROOT / "reports"

# ---- top-level areas
COMMON = ROOT / "common"
SOURCER = ROOT / "sourcer"
PIPELINES = ROOT / "pipelines"
SIBLING = PIPELINES / "sibling"
STACKING = PIPELINES / "stacking"
SIBLING_OUT = DATA_ROOT / "pipelines" / "sibling" / "out"
STACKING_OUT = DATA_ROOT / "pipelines" / "stacking" / "out"
ROUTER_OUT = DATA_ROOT / "pipelines" / "router" / "out"
EXPERIMENTS = DATA_ROOT / "experiments"
PRECISION_VALIDATION = EXPERIMENTS / "precision_validation"   # failed experiment; read only for exclusions

# ---- sourcer
CANDIDATES_DB = DATA_ROOT / "sourcer" / "index" / "candidates.sqlite"

# ---- common/launch
DRIVE = COMMON / "launch" / "drive.sh"
RUN_BUILD = COMMON / "launch" / "run_build.sh"

# ---- common/builder
BUILDER_DIR = COMMON / "builder"
BUILD_TEMPLATE = BUILDER_DIR / "TASK-BUILD-PROMPT-v1.md"
BUILDER_RULES = BUILDER_DIR / "BUILDER.md"
BUILD_PREPARE = BUILDER_DIR / "build_prepare.py"
TEMPLATES = BUILDER_DIR / "templates"
CONFORMANCE_SPEC = BUILDER_DIR / "FRONTIER-CONFORMANCE-SPEC.md"
CONFORMANCE_CHECK = BUILDER_DIR / "conformance_check.py"

# ---- common/screener
SCREENER_PROMPT = COMMON / "screener" / "SCREENER-PROMPT-v2.md"
SCREENER_RUNNER = COMMON / "screener" / "run_screener.py"
SCREENER_RECORDS = DATA_ROOT / "common" / "screener" / "records"    # the screened pool (screener-v2 records, 10-17)

# ---- common/gate
GATE_DIR = COMMON / "gate"
GATE = GATE_DIR / "gate.py"
GATE_ONE = GATE_DIR / "gate_one_ds.sh"
DOCKER_TUNING = GATE_DIR / "docker-tuning.env"

# ---- common/blindfix
RUN_BLINDFIX = COMMON / "blindfix" / "run_blindfix.sh"
BLIND_BRIEF = COMMON / "blindfix" / "BLIND-FIX-BRIEF.md"

# ---- common/trial
TRIAL_DIR = COMMON / "trial"
TRIAL = TRIAL_DIR / "trial.py"
TRIAL_STATE = TRIAL_DIR / "trial_state.py"
TRIAL_SET = TRIAL_DIR / "trial_set.sh"
TRIAL_SUMMARY = TRIAL_DIR / "trial_summary.py"
RUN_TRIAL = TRIAL_DIR / "run_trial.sh"

# ---- common/audit
AUDIT_TOOLS = COMMON / "audit"
POSTMORTEM = AUDIT_TOOLS / "postmortem.py"
AUDIT_RESULTS = AUDIT_TOOLS / "audit_results.py"
REVIEW_FLAGS = AUDIT_TOOLS / "review_flags.py"
REGRADE = AUDIT_TOOLS / "regrade.py"
REGRADE_FROM_CODE = AUDIT_TOOLS / "regrade_from_code.py"
HARVEST_CODE = AUDIT_TOOLS / "harvest_code.py"
INTERNET_USE = AUDIT_TOOLS / "internet_use.py"
ARCHIVE_RUNS = AUDIT_TOOLS / "archive_runs.py"

# ---- common/queue (work queue: docs/WORK-QUEUE.md)
QUEUE_DIR = COMMON / "queue"
CWEQ = QUEUE_DIR / "cweq.py"

# ---- common/fairness, common/versioning, common/util
FAIRNESS_BRIEF = COMMON / "fairness" / "FAIRNESS-REVIEW-BRIEF.md"
FAIRNESS_VERDICT = COMMON / "fairness" / "fairness_verdict.py"
SNAPSHOT = COMMON / "versioning" / "snapshot_experiment.sh"
RESTORE = COMMON / "versioning" / "restore_snapshot.sh"
UTIL = COMMON / "util"
AGENT_STATUS = UTIL / "agent_status.py"
EVIDENCE = UTIL / "evidence.py"
