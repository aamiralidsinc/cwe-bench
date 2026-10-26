"""With read-only mode in force, reads run and mutations are refused."""

import support


def test_mutation_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))

    outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=support.FakeIndex())

    support.refused(outcome)
    outcome.executor.assert_not_called()


def test_read_only_operation_still_runs(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    ir = support.make_ir('s3api', 'ListBuckets')

    outcome = support.drive(
        support.ALLOWED_COMMAND,
        ir,
        index=support.FakeIndex(read_only=[('s3api', 'ListBuckets')]),
    )

    support.ran(outcome)
