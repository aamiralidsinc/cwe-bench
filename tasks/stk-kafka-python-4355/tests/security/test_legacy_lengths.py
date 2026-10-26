"""A declared message length must not make a legacy message-set parse run forever.

A compressed legacy message set is a sequence of messages, each with its own declared length.
A length that does not advance the cursor makes the parse revisit the same bytes and collect
unbounded state.  The probe runs under the same hard memory ceiling as the expansion probes.
"""

from helpers import refusal_failure, run_bounded_child


def test_declared_message_length_must_make_the_parse_advance():
    proc = run_bounded_child('legacy_loop', 0)
    problem = refusal_failure(proc)
    assert problem is None, problem
