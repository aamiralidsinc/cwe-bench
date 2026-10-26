# -*- coding: utf-8 -*-
"""Legitimate values keep the meaning they have today."""

import unittest

import runner

ORDINARY_VARS = ("  vars:\n"
                 "    profile:\n"
                 "      name: bob\n"
                 "    tags: [red, blue]\n")

MAPPING_VARS = ("  vars:\n"
                "    mapping:\n"
                "      k: v\n"
                "      n: 3\n")


class ControllerValueTest(unittest.TestCase):

    def test_loop_over_a_rendered_list(self):
        run = runner.run_playbook(
            runner.loop_play("[u'alpha', u'beta']"))
        self.assertTrue(run.ok, run.report())
        self.assertIn("alpha", run.output)
        self.assertIn("beta", run.output)

    def test_arguments_from_a_rendered_mapping(self):
        run = runner.run_playbook(
            runner.args_play("{'msg': 'from-args'}"))
        self.assertTrue(run.ok, run.report())
        self.assertIn("from-args", run.output)

    def test_environment_from_a_rendered_mapping(self):
        run = runner.run_playbook(
            runner.environment_echo_play("{'GREETING': 'hello-env'}"))
        self.assertTrue(run.ok, run.report())
        self.assertIn("hello-env", run.output)


class ModuleMappingTest(unittest.TestCase):

    def test_key_value_text(self):
        run = runner.run_playbook(
            runner.module_mapping_play_json("path=/tmp,size=2"))
        self.assertTrue(run.ok, run.report())
        self.assertIn("/tmp", run.output)

    def test_json_text(self):
        run = runner.run_playbook(
            runner.module_mapping_play_json('{"path": "/tmp"}'))
        self.assertTrue(run.ok, run.report())
        self.assertIn("/tmp", run.output)

    def test_python_style_text(self):
        run = runner.run_playbook(
            runner.module_mapping_play_json(
                "{'path': u'/tmp', 'name': u'probe'}"))
        self.assertTrue(run.ok, run.report())
        self.assertIn("/tmp", run.output)
        self.assertIn("probe", run.output)


class HostValueTest(unittest.TestCase):

    def test_ordinary_expression_in_a_value(self):
        run = runner.run_playbook(
            runner.host_plain_play("ordinary", ORDINARY_VARS))
        self.assertTrue(run.ok, run.report())
        self.assertIn("bob / red-blue", run.output)

    def test_mapping_value_turns_back_into_data(self):
        run = runner.run_playbook(
            runner.host_plain_play("mapping", MAPPING_VARS, "r.value.k"))
        self.assertTrue(run.ok, run.report())
        self.assertIn("value=v", run.output)


if __name__ == "__main__":
    unittest.main()
