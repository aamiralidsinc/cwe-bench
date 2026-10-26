"""A small compressed payload must not expand without bound inside the client.

The probe runs in a child with a hard memory ceiling.  A client that applies a bound refuses
the batch with an explicit error long before the ceiling; one that does not reaches the ceiling
and dies of a memory error.
"""

import pytest

from helpers import refusal_failure, run_bounded_child

LARGE_EXPANSION_MB = 512


def test_compressed_record_batch_expansion_is_refused():
    proc = run_bounded_child('v2', LARGE_EXPANSION_MB)
    problem = refusal_failure(proc)
    assert problem is None, problem


def test_compressed_legacy_message_set_expansion_is_refused():
    proc = run_bounded_child('legacy_bomb', LARGE_EXPANSION_MB)
    problem = refusal_failure(proc)
    assert problem is None, problem
