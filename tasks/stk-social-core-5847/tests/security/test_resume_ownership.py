"""Security cases: a stored sign-in flow must not be continued by another session.

Every case drives the product's own entry points (the framework actions, the public
partial-pipeline utility and the backend resume hook) with a flow that another
session started, and asserts the flow did not continue.
"""
import unittest

from support import harness
from social_core.actions import do_complete, do_disconnect
from social_core.utils import PARTIAL_TOKEN_SESSION_NAME, partial_pipeline_data

EMAIL_PIPELINE = (
    f"{harness.__name__}.set_details",
    "social_core.pipeline.mail.mail_validation",
    f"{harness.__name__}.record_run",
    f"{harness.__name__}.login_user",
)

EMAIL_SETTINGS = {
    "SOCIAL_AUTH_PIPELINE": EMAIL_PIPELINE,
    "SOCIAL_AUTH_EMAIL_VALIDATION_URL": "/validate",
}


class ResumeOwnershipTest(unittest.TestCase):
    def setUp(self) -> None:
        harness.reset()

    def _started_flow(self, name="probe"):
        session = harness.new_session()
        backend = harness.new_backend(session, name)
        session.authenticate(backend, response={})
        token = session.session_get(PARTIAL_TOKEN_SESSION_NAME)
        self.assertIsNotNone(token, "the halting step must store a flow and its token")
        return session, backend, token

    def test_request_supplied_token_from_another_session_does_not_continue(self):
        _attacker, _attacker_backend, token = self._started_flow()
        victim = harness.new_session()
        victim_backend = harness.new_backend(victim)
        victim.set_request_data(
            {"partial_token": token, "password": "chosen-by-the-flow-owner"},
            victim_backend,
        )
        harness.RUNS.clear()

        harness.assert_clean_refusal(
            self, lambda: do_complete(victim_backend, login=harness.noop_login)
        )

        self.assertEqual([], harness.RUNS, "the stored flow continued in another session")
        self.assertIsNone(victim.session_get("logged_in"))
        self.assertIsNone(victim.session_get("username"))

    def test_disconnect_with_another_sessions_token_does_not_continue(self):
        attacker = harness.new_session()
        attacker_backend = harness.new_backend(attacker)
        attacker.set_settings({"SOCIAL_AUTH_DISCONNECT_PIPELINE": (f"{harness.__name__}.record_disconnect",)})
        attacker.authenticate(attacker_backend, response={}, flow_owner="another-session")
        token = attacker.session_get(PARTIAL_TOKEN_SESSION_NAME)
        self.assertIsNotNone(token)

        victim = harness.new_session()
        victim_backend = harness.new_backend(victim)
        victim_user = harness.User("victim")
        victim.set_request_data({"partial_token": token}, victim_backend)
        harness.DISCONNECTS.clear()

        harness.assert_clean_refusal(
            self, lambda: do_disconnect(victim_backend, victim_user)
        )

        self.assertNotIn(
            "another-session",
            [entry.get("marker") for entry in harness.DISCONNECTS],
            "another session's stored disconnect flow continued",
        )

    def test_configured_token_field_from_another_session_does_not_continue(self):
        _attacker, _attacker_backend, token = self._started_flow()
        victim = harness.new_session(
            {"SOCIAL_AUTH_PARTIAL_PIPELINE_TOKEN_NAME": "resume"}
        )
        victim_backend = harness.new_backend(victim)
        victim.set_request_data({"resume": token, "password": "x"}, victim_backend)
        harness.RUNS.clear()

        harness.assert_clean_refusal(
            self, lambda: do_complete(victim_backend, login=harness.noop_login)
        )

        self.assertEqual([], harness.RUNS, "a configured token field resumed another session's flow")
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

        self.assertEqual([], harness.RUNS, "an explicit token argument resumed another session's flow")
        self.assertIsNone(victim.session_get("logged_in"))

    def test_request_proof_alone_does_not_authorise_a_foreign_flow(self):
        _attacker, _attacker_backend, token = self._started_flow()
        victim = harness.new_session()
        victim_backend = harness.new_backend(victim)
        victim.set_request_data(
            {
                "partial_token": token,
                "password": "x",
                "verification_code": "supplied-by-the-request",
            },
            victim_backend,
        )
        harness.RUNS.clear()

        harness.assert_clean_refusal(
            self, lambda: do_complete(victim_backend, login=harness.noop_login)
        )

        self.assertEqual([], harness.RUNS, "request-supplied proof resumed a flow that never recorded it")
        self.assertIsNone(victim.session_get("logged_in"))

    def test_low_level_resume_hook_refuses_another_sessions_flow(self):
        _attacker, _attacker_backend, token = self._started_flow()
        victim = harness.new_session()
        victim_backend = harness.new_backend(victim)
        victim.set_request_data({"password": "x"}, victim_backend)
        partial = victim.partial_load(token)
        if partial is None:
            return  # a correct fix may refuse already at the loader

        harness.RUNS.clear()
        harness.assert_clean_refusal(self, lambda: victim_backend.continue_pipeline(partial))

        self.assertEqual([], harness.RUNS, "the low-level resume hook continued another session's flow")
        self.assertIsNone(victim.session_get("logged_in"))
