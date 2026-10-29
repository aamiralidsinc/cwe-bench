"""export_delivery.py: comments pointing at internal paths are cut from the exported package (owner 2026-10-28)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import export_delivery as ed  # noqa: E402


def test_internal_path_comments_are_cut_and_nothing_else_changes(tmp_path):
    t = tmp_path / "pkg"
    (t / "environment").mkdir(parents=True)
    (t / "tests" / "support").mkdir(parents=True)
    (t / "tests" / "pristine").mkdir(parents=True)
    docker = ("FROM python:3.12\n# Task source state (see build/spark-s3/notes.md).\n"
              "RUN mkdir -p build/classes && echo '# see build/spark-s3/notes.md'\n# plain comment\n")
    (t / "environment" / "Dockerfile").write_text(docker)
    (t / "tests" / "support" / "refusal.ts").write_text(
        "/**\n// Adapted from common/builder/templates/support/refusal/refusal.mjs; same semantics.\nexport const x = 1;\n")
    (t / "tests" / "test.sh").write_text("#!/bin/bash\n# peer (built by build/spark-s3/make_peer.py). Runs below.\n"
                                         "rm -rf core/build/test-results/test\n")
    (t / "tests" / "c.c").write_text('#include "build/spark-s3/x.h"\n')
    (t / "tests" / "pristine" / "up.py").write_text("# see build/spark-s3/notes.md\n")      # upstream copy: untouched
    (t / "task.toml").write_text('advisory = "see notes.md"\n')
    changed = ed.strip_internal_comments(t, "spark-s3")
    assert (t / "environment" / "Dockerfile").read_text() == docker.replace(" (see build/spark-s3/notes.md)", "")
    assert "common/builder" not in (t / "tests" / "support" / "refusal.ts").read_text()
    assert "export const x = 1;" in (t / "tests" / "support" / "refusal.ts").read_text()
    assert (t / "tests" / "test.sh").read_text() == "#!/bin/bash\n# peer. Runs below.\nrm -rf core/build/test-results/test\n"
    assert (t / "tests" / "c.c").read_text() == '#include "build/spark-s3/x.h"\n'               # not a comment in C
    assert (t / "tests" / "pristine" / "up.py").read_text() == "# see build/spark-s3/notes.md\n"
    assert (t / "task.toml").read_text() == 'advisory = "see notes.md"\n'
    assert sorted(changed) == ["environment/Dockerfile:2: path reference cut", "tests/support/refusal.ts:2: comment removed",
                               "tests/test.sh:2: path reference cut"]
