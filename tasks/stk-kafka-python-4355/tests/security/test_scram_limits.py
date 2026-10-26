"""The broker-chosen authentication parameters must not buy unbounded client work.

A SCRAM challenge carries a salt and an iteration count.  Both multiply the key-derivation
cost, and both are picked by the peer.  A challenge that asks for an absurd amount of either
must be refused before any of that work is performed.
"""

import hashlib

import pytest

from helpers import scram_mechanism, server_first_message

# Sanity ceilings used only to tell "refused" apart from "performed": real brokers stay far
# below both.
MAX_WORKED_ITERATIONS = 10 ** 6
MAX_WORKED_SALT = 64 * 1024


@pytest.fixture
def key_derivation_calls(monkeypatch):
    """Record every key-derivation attempt instead of paying for it.

    The recording stand-in returns a correctly sized digest, so the handshake would otherwise
    continue normally on a build that applies no bound at all.
    """
    calls = []

    def recording_pbkdf2(hash_name, password, salt, iterations, dklen=None):
        calls.append((len(salt), iterations))
        digest = hashlib.new(hash_name, password + salt).digest()
        return digest[:dklen] if dklen else digest

    monkeypatch.setattr(hashlib, 'pbkdf2_hmac', recording_pbkdf2, raising=False)
    return calls


def _submit_first_challenge(mechanism_name, salt, iterations):
    mechanism = scram_mechanism(mechanism_name)
    mechanism.receive(server_first_message(mechanism, salt, iterations))


@pytest.mark.parametrize('mechanism_name,iterations', [
    ('SCRAM-SHA-256', 10 ** 9),
    ('SCRAM-SHA-512', 2 ** 31 - 1),
])
def test_extreme_iteration_count_is_refused(key_derivation_calls, mechanism_name, iterations):
    try:
        _submit_first_challenge(mechanism_name, b'0123456789abcdef', iterations)
    except MemoryError:
        pytest.fail('the client tried to satisfy the requested work instead of refusing it')
    except Exception:  # noqa: BLE001 - any explicit client error is an acceptable refusal
        pass
    else:
        pytest.fail('the client accepted a challenge asking for %d key-derivation rounds'
                    % iterations)
    attempted = [count for _, count in key_derivation_calls]
    assert all(count <= MAX_WORKED_ITERATIONS for count in attempted), (
        'key derivation was attempted with a count chosen by the peer: %r' % (attempted,))


def test_oversized_salt_is_refused(key_derivation_calls):
    salt = b's' * (256 * 1024)
    try:
        _submit_first_challenge('SCRAM-SHA-256', salt, 4096)
    except MemoryError:
        pytest.fail('the client allocated the peer-declared salt instead of refusing it')
    except Exception:  # noqa: BLE001 - any explicit client error is an acceptable refusal
        pass
    else:
        pytest.fail('the client accepted a %d-byte salt in its challenge' % len(salt))
    attempted = [size for size, _ in key_derivation_calls]
    assert all(size <= MAX_WORKED_SALT for size in attempted), (
        'key derivation was attempted with a peer-declared salt size: %r' % (attempted,))
