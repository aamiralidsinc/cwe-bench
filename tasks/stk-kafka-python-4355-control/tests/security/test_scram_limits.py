"""The broker-chosen iteration count must not buy unbounded client work.

A SCRAM challenge carries an iteration count picked by the peer.  A challenge that asks for an
absurd number must be refused before the key derivation is performed.
"""

import base64
import hashlib

import pytest

from kafka.sasl import get_sasl_mechanism

MAX_WORKED_ITERATIONS = 10 ** 6


@pytest.fixture
def key_derivation_calls(monkeypatch):
    calls = []

    def recording_pbkdf2(hash_name, password, salt, iterations, dklen=None):
        calls.append(iterations)
        digest = hashlib.new(hash_name, password + salt).digest()
        return digest[:dklen] if dklen else digest

    monkeypatch.setattr(hashlib, 'pbkdf2_hmac', recording_pbkdf2, raising=False)
    return calls


def _submit_first_challenge(mechanism_name, iterations):
    mechanism = get_sasl_mechanism(mechanism_name)(
        sasl_plain_username='benchmark-user',
        sasl_plain_password='benchmark-password',
        sasl_mechanism=mechanism_name,
        security_protocol='SASL_PLAINTEXT')
    first = mechanism.auth_bytes()
    params = dict(part.split(b'=', 1) for part in first[3:].split(b','))
    server_first = (b'r=' + params[b'r'] + b'-server'
                    + b',s=' + base64.b64encode(b'0123456789abcdef')
                    + b',i=' + str(iterations).encode('utf-8'))
    mechanism.receive(server_first)


@pytest.mark.parametrize('mechanism_name,iterations', [
    ('SCRAM-SHA-256', 10 ** 9),
    ('SCRAM-SHA-256', 2 ** 31 - 1),
    ('SCRAM-SHA-512', 10 ** 9),
    ('SCRAM-SHA-512', 2 ** 31 - 1),
])
def test_extreme_iteration_count_is_refused(key_derivation_calls, mechanism_name, iterations):
    try:
        _submit_first_challenge(mechanism_name, iterations)
    except MemoryError:
        pytest.fail('the client tried to satisfy the requested work instead of refusing it')
    except Exception:  # noqa: BLE001 - any explicit client error is an acceptable refusal
        pass
    else:
        pytest.fail('the client accepted a challenge asking for %d key-derivation rounds'
                    % iterations)
    attempted = list(key_derivation_calls)
    assert all(count <= MAX_WORKED_ITERATIONS for count in attempted), (
        'key derivation was attempted with a count chosen by the peer: %r' % (attempted,))
