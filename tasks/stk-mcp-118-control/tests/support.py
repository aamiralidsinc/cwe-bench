"""Shared helpers for the hidden suites.

Nothing here imports product code at module load; each helper imports the server
lazily so a module's environment is fixed before the product reads it.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

POLICY_RELATIVE = Path('.aws') / 'aws-api-mcp' / 'mcp-security-policy.json'
DENIED_COMMAND = 'aws iam create-access-key'
ALLOWED_COMMAND = 'aws s3api list-buckets'


def policy_path():
    """The operator policy file the product reads."""
    return Path.home() / POLICY_RELATIVE


def write_policy(document):
    """Write the operator policy file; a str is written verbatim (to make it malformed)."""
    path = policy_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        path.rmdir()
    elif path.is_file():
        path.unlink()
    path.write_text(document if isinstance(document, str) else json.dumps(document))
    return path


def make_policy_unreadable():
    """Put a directory where the policy file goes: it exists but cannot be opened."""
    path = policy_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        path.unlink()
    path.mkdir()
    return path


class FakeIndex:
    """A read-only operations index that answers per service and operation."""

    def __init__(self, read_only=()):
        self.read_only = {(service, operation) for service, operation in read_only}

    def has(self, service, operation):
        return (service, operation) in self.read_only


class Ctx:
    """Minimal MCP context: records errors; elicitation is never expected here."""

    def __init__(self):
        self.errors = []

    async def error(self, message, logger_name=None, extra=None):
        self.errors.append(str(message))

    async def elicit(self, message, response_type=None):
        raise AssertionError('unexpected elicitation request: %s' % message)


class Outcome:
    """What one call through the public tool did."""

    def __init__(self, result, executor, help_document, customization, ctx):
        self.result = result
        self.executor = executor
        self.help_document = help_document
        self.customization = customization
        self.ctx = ctx


def make_ir(
    service='iam',
    operation='CreateAccessKey',
    *,
    cli_service=None,
    cli_operation=None,
    customization=False,
    help_operation=False,
):
    """An interpreted command whose metadata says what the policy should see."""
    ir = MagicMock()
    metadata = MagicMock()
    metadata.service_sdk_name = service
    metadata.operation_sdk_name = operation
    ir.command_metadata = metadata
    command = MagicMock()
    command.is_awscli_customization = customization
    command.is_help_operation = help_operation
    command.service_name = cli_service or service
    command.operation_cli_name = cli_operation or operation
    ir.command = command
    return ir


def drive(command, ir, *, index, ctx=None):
    """Call the public command tool with only the translator and executors stubbed.

    The product's own validation, gate, policy loading and dispatch all run.
    """
    import awslabs.aws_api_mcp_server.server as server
    from awslabs.aws_api_mcp_server.core.common.models import ProgramInterpretationResponse

    ctx = ctx or Ctx()
    success = ProgramInterpretationResponse()
    executor = MagicMock(name='interpret_command', return_value=success)
    help_document = AsyncMock(name='get_help_document', return_value=success)
    customization = MagicMock(name='execute_awscli_customization', return_value=success)
    validation = MagicMock(name='validate_response')
    validation.validation_failed = False
    with (
        patch.object(server, 'translate_cli_to_ir', return_value=ir),
        patch.object(server, 'validate', return_value=validation),
        patch.object(server, 'interpret_command', executor),
        patch.object(server, 'get_help_document', help_document),
        patch.object(server, 'execute_awscli_customization', customization),
        patch.object(server, 'READ_OPERATIONS_INDEX', index),
    ):
        result = asyncio.run(server.call_aws(command, ctx))
    return Outcome(result, executor, help_document, customization, ctx)


def refused(outcome):
    """A refusal is an error for every command in the result and produces no response."""
    result = outcome.result
    assert result, 'no result returned'
    for item in result:
        assert getattr(item, 'error', None), 'the command was not refused: %r' % (item,)
        assert getattr(item, 'response', None) is None, (
            'a refused command still produced a response'
        )


def ran(outcome):
    """A command that the policy allows runs exactly once and reports no error."""
    assert len(outcome.result) == 1
    assert outcome.result[0].error is None, outcome.result[0].error
    outcome.executor.assert_called_once()
