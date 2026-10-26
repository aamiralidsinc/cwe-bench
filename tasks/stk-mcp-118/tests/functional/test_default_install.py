"""A deployment with no operator policy file keeps running commands the policy allows."""

import support


def test_command_runs_without_a_policy_file(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))

    outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=support.FakeIndex())

    support.ran(outcome)


def test_read_only_command_runs_without_a_policy_file(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    ir = support.make_ir('s3api', 'ListBuckets')

    outcome = support.drive(
        support.ALLOWED_COMMAND,
        ir,
        index=support.FakeIndex(read_only=[('s3api', 'ListBuckets')]),
    )

    support.ran(outcome)
