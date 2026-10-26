"""A policy that exists but cannot be loaded must not behave like no policy at all."""

import support

DENY_POLICY = {'policy': {'denyList': [support.DENIED_COMMAND], 'elicitList': []}}


def test_unparseable_policy_does_not_allow_a_denied_command(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    # Truncated JSON: the file exists and the operator meant to deny this command.
    support.write_policy('{"policy": {"denyList": ["%s"]' % support.DENIED_COMMAND)

    outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=support.FakeIndex())

    support.refused(outcome)
    outcome.executor.assert_not_called()


def test_unreadable_policy_does_not_allow_a_denied_command(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    support.make_policy_unreadable()

    outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=support.FakeIndex())

    support.refused(outcome)
    outcome.executor.assert_not_called()


def test_empty_policy_does_not_allow_a_denied_command(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    support.write_policy('')

    outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=support.FakeIndex())

    support.refused(outcome)
    outcome.executor.assert_not_called()
