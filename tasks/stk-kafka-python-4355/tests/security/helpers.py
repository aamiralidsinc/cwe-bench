"""Helpers shared by the security probes: build a broker-style SCRAM challenge and run a
resource probe in a memory-limited child process."""

import base64
import os
import subprocess
import sys

# How much memory the resource probes are allowed.  A refusal must happen well below this; a
# process that reaches it allocated without bound instead of refusing.
CHILD_MEMORY_LIMIT_MB = 384


def scram_mechanism(mechanism_name):
    """The library's SASL factory, i.e. exactly what a connection builds at login time."""
    from kafka.sasl import get_sasl_mechanism

    return get_sasl_mechanism(mechanism_name)(
        sasl_plain_username='benchmark-user',
        sasl_plain_password='benchmark-password',
        sasl_mechanism=mechanism_name,
        security_protocol='SASL_PLAINTEXT')


def server_first_message(mechanism, salt, iterations):
    """A broker's first SCRAM answer, echoing the client nonce the mechanism just produced."""
    first = mechanism.auth_bytes()
    params = dict(part.split(b'=', 1) for part in first[3:].split(b','))
    nonce = params[b'r'] + b'-server'
    return (b'r=' + nonce
            + b',s=' + base64.b64encode(salt)
            + b',i=' + str(iterations).encode('utf-8'))


def run_bounded_child(mode, expansion_mb, timeout=180):
    """Run the resource probe in a child capped at CHILD_MEMORY_LIMIT_MB.

    The child exits 0 when the product raised an explicit error, 2 when the product returned a
    result, and 3 when it ran out of memory.  Any other status is also a failure.
    """
    child = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bomb_child.py')
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(p for p in sys.path if p)
    return subprocess.run(
        [sys.executable, child, mode, str(expansion_mb), str(CHILD_MEMORY_LIMIT_MB)],
        capture_output=True, text=True, timeout=timeout, env=env)


def refusal_failure(proc):
    if proc.returncode == 0:
        return None
    if proc.returncode == 3:
        return ('the client allocated until it ran out of memory instead of refusing the '
                'response: %s' % (proc.stdout.strip() or proc.stderr.strip())[-300:])
    if proc.returncode == 2:
        return 'the client accepted the response without applying any bound'
    return ('the resource probe did not end in a clean refusal (exit %d): %s'
            % (proc.returncode, (proc.stdout.strip() or proc.stderr.strip())[-300:]))
