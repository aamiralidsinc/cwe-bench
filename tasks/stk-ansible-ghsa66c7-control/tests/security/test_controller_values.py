# -*- coding: utf-8 -*-
"""A value supplied as data must not be executed when it is turned into a value.

Every case drives the product's command-line tool with its own play.
"""

import os
import unittest

import runner


def _refused_or_inert(testcase, run, marker):
    """The attack must leave no side effect; the refusal form is not graded."""
    testcase.assertFalse(
        os.path.exists(marker),
        "a value supplied as data was executed as code\n%s" % run.report())


class LoopValueTest(unittest.TestCase):

    def test_loop_value_is_not_executed(self):
        benign = runner.run_playbook(
            runner.loop_play("[u'alpha', u'beta']"))
        self.assertTrue(benign.ok, benign.report())
        self.assertIn("alpha", benign.output)
        self.assertIn("beta", benign.output)

        marker = runner.marker("loop")
        attack = runner.run_playbook(
            runner.loop_play("[__import__('os').system('touch %s')]" % marker))
        _refused_or_inert(self, attack, marker)

    def test_loop_value_with_indirect_call_is_not_executed(self):
        benign = runner.run_playbook(runner.loop_play("[u'alpha']"))
        self.assertTrue(benign.ok, benign.report())

        marker = runner.marker("loop_indirect")
        attack = runner.run_playbook(
            runner.loop_play(
                "map(__import__('os').system, ['touch %s'])" % marker))
        _refused_or_inert(self, attack, marker)


class TaskValueTest(unittest.TestCase):

    def test_arguments_value_is_not_executed(self):
        benign = runner.run_playbook(
            runner.args_play("{'msg': 'from-args'}"))
        self.assertTrue(benign.ok, benign.report())
        self.assertIn("from-args", benign.output)

        marker = runner.marker("args")
        attack = runner.run_playbook(
            runner.args_play(
                "{__import__('os').system('touch %s'): 1}" % marker))
        _refused_or_inert(self, attack, marker)

    def test_environment_value_is_not_executed(self):
        benign = runner.run_playbook(
            runner.environment_play("{'GREETING': 'hello'}"))
        self.assertTrue(benign.ok, benign.report())

        marker = runner.marker("environment")
        attack = runner.run_playbook(
            runner.environment_play(
                "{__import__('os').system('touch %s'): 1}" % marker))
        _refused_or_inert(self, attack, marker)


if __name__ == "__main__":
    unittest.main()
