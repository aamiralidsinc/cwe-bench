"""The server must not begin serving when it cannot obtain its enforcement data."""


def _start_with_loader(loader, monkeypatch):
    import awslabs.aws_api_mcp_server.server as server
    from unittest.mock import MagicMock, patch

    server_mock = MagicMock(name='server')
    monkeypatch.setattr(server, 'READ_OPERATIONS_INDEX', None)
    with (
        patch.object(server, 'server', server_mock),
        patch.object(server, 'get_read_only_operations', side_effect=loader),
        patch.object(server, 'validate_aws_region'),
        patch.object(server, 'DEFAULT_REGION', 'us-east-1'),
        patch.object(server, 'WORKING_DIRECTORY', '/tmp'),
        patch('os.chdir'),
    ):
        try:
            server.main()
        except BaseException:
            pass
    return server_mock


def test_server_does_not_start_when_enforcement_data_cannot_be_loaded(monkeypatch):
    def loader():
        raise RuntimeError('the service reference document is unreachable')

    server_mock = _start_with_loader(loader, monkeypatch)
    server_mock.run.assert_not_called()


def test_server_does_not_start_when_enforcement_data_load_fails_unexpectedly(monkeypatch):
    def loader():
        raise ValueError('unexpected metadata document')

    server_mock = _start_with_loader(loader, monkeypatch)
    server_mock.run.assert_not_called()
