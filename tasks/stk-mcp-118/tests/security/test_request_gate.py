"""No command may run when the data needed for its policy decision is unavailable."""

import support


def test_denied_command_is_not_executed_when_enforcement_data_is_unavailable():
    outcome = support.drive(support.DENIED_COMMAND, support.make_ir(), index=None)
    support.refused(outcome)
    outcome.executor.assert_not_called()


def test_read_only_command_is_not_executed_when_enforcement_data_is_unavailable():
    ir = support.make_ir('s3api', 'ListBuckets')
    outcome = support.drive(support.ALLOWED_COMMAND, ir, index=None)
    support.refused(outcome)
    outcome.executor.assert_not_called()


def test_every_command_of_a_batch_is_refused_when_enforcement_data_is_unavailable():
    outcome = support.drive(
        [support.DENIED_COMMAND, support.ALLOWED_COMMAND], support.make_ir(), index=None
    )
    assert len(outcome.result) == 2
    support.refused(outcome)
    outcome.executor.assert_not_called()


def test_help_operation_is_not_served_when_enforcement_data_is_unavailable():
    ir = support.make_ir('s3api', 'ListBuckets', help_operation=True)
    outcome = support.drive('aws s3api help', ir, index=None)
    support.refused(outcome)
    outcome.help_document.assert_not_called()


def test_customization_is_not_dispatched_when_enforcement_data_is_unavailable():
    ir = support.make_ir('s3', 'Ls', customization=True, cli_service='s3', cli_operation='ls')
    outcome = support.drive('aws s3 ls', ir, index=None)
    support.refused(outcome)
    outcome.customization.assert_not_called()
