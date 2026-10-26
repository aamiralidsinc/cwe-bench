"""Legitimate authentication handshakes keep working, including realistic sizes.

Salt sizes of 16 and 64 bytes and iteration counts of 4096/16384 are what real brokers use.
The key derivation runs for real here.
"""

import base64

import pytest

from kafka.sasl import get_sasl_mechanism


def _mechanism(mechanism_name):
    return get_sasl_mechanism(mechanism_name)(
        sasl_plain_username='benchmark-user',
        sasl_plain_password='benchmark-password',
        sasl_mechanism=mechanism_name,
        security_protocol='SASL_PLAINTEXT')


def _complete_first_step(mechanism_name, salt, iterations):
    mechanism = _mechanism(mechanism_name)
    first = mechanism.auth_bytes()
    params = dict(part.split(b'=', 1) for part in first[3:].split(b','))
    server_first = (b'r=' + params[b'r'] + b'-server'
                    + b',s=' + base64.b64encode(salt)
                    + b',i=' + str(iterations).encode('utf-8'))
    mechanism.receive(server_first)
    return mechanism


@pytest.mark.parametrize('mechanism_name,salt,iterations', [
    ('SCRAM-SHA-256', b'0123456789abcdef', 4096),
    ('SCRAM-SHA-512', b'0123456789abcdef' * 4, 16384),
])
def test_standard_handshake_completes(mechanism_name, salt, iterations):
    mechanism = _complete_first_step(mechanism_name, salt, iterations)
    client_final = mechanism.auth_bytes()
    assert client_final.startswith(b'c=biws,r='), client_final[:32]
    assert b',p=' in client_final
    proof = client_final.split(b',p=', 1)[1]
    assert len(proof) >= 40
