"""A valid operator policy keeps deciding: listed commands are refused, others run."""

import support


def test_a_listed_command_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    support.write_policy({'policy': {'denyList': [support.DENIED_COMMAND], 'elicitList': []}})

    outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=support.FakeIndex())

    support.refused(outcome)
    outcome.executor.assert_not_called()


def test_an_unlisted_command_still_runs(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    support.write_policy({'policy': {'denyList': [support.DENIED_COMMAND], 'elicitList': []}})
    ir = support.make_ir('s3api', 'ListBuckets')

    outcome = support.drive(
        support.ALLOWED_COMMAND,
        ir,
        index=support.FakeIndex(read_only=[('s3api', 'ListBuckets')]),
    )

    support.ran(outcome)


def test_a_listed_command_with_a_consent_client_is_asked_not_refused(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    support.write_policy({'policy': {'denyList': [], 'elicitList': [support.DENIED_COMMAND]}})

    ctx = support.Ctx()
    observed = {}

    async def approve(message, response_type=None):
        observed['asked'] = message
        from awslabs.aws_api_mcp_server.core.common.models import Consent
        from fastmcp.server.elicitation import AcceptedElicitation

        return AcceptedElicitation(data=Consent(answer=True))

    ctx.elicit = approve

    outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=support.FakeIndex(), ctx=ctx)

    assert 'asked' in observed, 'the operator was not asked about a listed command'
    support.ran(outcome)
