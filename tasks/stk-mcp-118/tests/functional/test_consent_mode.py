"""With mutation consent in force, mutations ask and reads do not."""

import support


def _index():
    return support.FakeIndex(read_only=[('s3api', 'ListBuckets')])


def test_mutation_requests_consent(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    from unittest.mock import AsyncMock, patch

    import awslabs.aws_api_mcp_server.server as server

    with patch.object(server, 'request_consent', new=AsyncMock()) as consent:
        outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=_index())

    consent.assert_awaited_once()
    support.ran(outcome)


def test_read_only_operation_does_not_request_consent(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    from unittest.mock import AsyncMock, patch

    import awslabs.aws_api_mcp_server.server as server

    ir = support.make_ir('s3api', 'ListBuckets')
    with patch.object(server, 'request_consent', new=AsyncMock()) as consent:
        outcome = support.drive(support.ALLOWED_COMMAND, ir, index=_index())

    consent.assert_not_awaited()
    support.ran(outcome)
