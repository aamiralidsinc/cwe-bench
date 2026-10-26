"""The server starts normally when its enforcement data loads."""

from unittest.mock import MagicMock, patch


def test_server_starts_when_enforcement_data_loads(monkeypatch):
    import awslabs.aws_api_mcp_server.server as server

    class Index:
        def has(self, service, operation):
            return False

    server_mock = MagicMock(name='server')
    monkeypatch.setattr(server, 'READ_OPERATIONS_INDEX', None)
    with (
        patch.object(server, 'server', server_mock),
        patch.object(server, 'get_read_only_operations', return_value=Index()),
        patch.object(server, 'validate_aws_region'),
        patch.object(server, 'DEFAULT_REGION', 'us-east-1'),
        patch.object(server, 'WORKING_DIRECTORY', '/tmp'),
        patch('os.chdir'),
    ):
        server.main()

    server_mock.run.assert_called_once()
