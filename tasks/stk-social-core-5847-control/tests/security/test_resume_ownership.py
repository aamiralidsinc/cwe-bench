"""Security cases for the advisory's own route: another session's flow token is not resumed.

All four cases drive the completion action or the public resume utility with a token
for a flow that another session started.
"""
import unittest

from support import harness
from social_core.actions import do_complete
from social_core.utils import PARTIAL_TOKEN_SESSION_NAME, partial_pipeline_data


class ResumeOwnershipTest(unittest.TestCase):
    def setUp(self) -> None:
        harness.reset()

    def _started_flow(self):
        session = harness.new_session()
        backend = harness.new_backend(session)
        session.authenticate(backend, response={})
        token = session.session_get(PARTIAL_TOKEN_SESSION_NAME)
        self.assertIsNotNone(token, "the halting step must store a flow and its token")
        return session, backend, token

    def test_request_token_from_another_session_does_not_continue(self):
        _attacker, _attacker_backend, token = self._started_flow()
        victim = harness.new_session()
        victim_backend = harness.new_backend(victim)
        victim.set_request_data({"partial_token": token, "password": "x"}, victim_backend)
        harness.RUNS.clear()

        harness.assert_clean_refusal(
            self, lambda: do_complete(victim_backend, login=harness.noop_login)
        )

        self.assertEqual([], harness.RUNS, "the stored flow continued in another session")
        self.assertIsNone(victim.session_get("logged_in"))

    def test_configured_token_field_from_another_session_does_not_continue(self):
        _attacker, _attacker_backend, token = self._started_flow()
        victim = harness.new_session({"SOCIAL_AUTH_PARTIAL_PIPELINE_TOKEN_NAME": "resume"})
        victim_backend = harness.new_backend(victim)
        victim.set_request_data({"resume": token, "password": "x"}, victim_backend)
        harness.RUNS.clear()

        harness.assert_clean_refusal(
            self, lambda: do_complete(victim_backend, login=harness.noop_login)
        )

        self.assertEqual([], harness.RUNS)
        self.assertIsNone(victim.session_get("logged_in"))

    def test_explicit_token_argument_from_another_session_does_not_resume(self):
        _attacker, _attacker_backend, token = self._started_flow()
        victim = harness.new_session()
        victim_backend = harness.new_backend(victim)
        victim.set_request_data({"password": "x"}, victim_backend)

        def resume_with_argument():
            partial = partial_pipeline_data(victim_backend, None, token)
            if partial is not None:
                victim_backend.continue_pipeline(partial)

        harness.RUNS.clear()
        harness.assert_clean_refusal(self, resume_with_argument)

        self.assertEqual([], harness.RUNS)
        self.assertIsNone(victim.session_get("logged_in"))

    def test_request_token_does_not_replace_the_sessions_own_flow(self):
        _attacker, _attacker_backend, attacker_token = self._started_flow()
        victim = harness.new_session()
        victim_backend = harness.new_backend(victim)
        victim.authenticate(victim_backend, response={})
        self.assertIsNotNone(victim.session_get(PARTIAL_TOKEN_SESSION_NAME))
        victim.set_request_data(
            {"partial_token": attacker_token, "password": "x"}, victim_backend
        )
        harness.RUNS.clear()

        harness.assert_clean_refusal(
            self, lambda: do_complete(victim_backend, login=harness.noop_login)
        )

        self.assertEqual([], harness.RUNS, "a request token replaced the session's own flow")
        self.assertIsNone(victim.session_get("logged_in"))
