"""Allowed help and customization operations are still dispatched."""

import support


def test_help_operation_is_served(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    ir = support.make_ir('s3api', 'ListBuckets', help_operation=True)

    outcome = support.drive('aws s3api help', ir, index=support.FakeIndex())

    outcome.help_document.assert_called_once()
    assert outcome.result[0].error is None


def test_customization_is_dispatched(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    ir = support.make_ir('s3', 'Ls', customization=True, cli_service='s3', cli_operation='ls')

    outcome = support.drive('aws s3 ls', ir, index=support.FakeIndex())

    outcome.customization.assert_called_once()
    assert outcome.result[0].error is None
