# -*- coding: utf-8 -*-
"""A value read back from a managed host must not be executed as a program."""

import os
import unittest

import runner

ORDINARY_VARS = ("  vars:\n"
                 "    profile:\n"
                 "      name: bob\n"
                 "    tags: [red, blue]\n")


class HostValueTest(unittest.TestCase):

    def test_host_value_is_not_executed(self):
        benign = runner.run_playbook(
            runner.host_plain_play("ordinary", ORDINARY_VARS))
        self.assertTrue(benign.ok, benign.report())
        self.assertIn("bob / red-blue", benign.output)

        marker = runner.marker("host")
        attack = runner.run_playbook(
            runner.host_value_play("expression", marker))
        self.assertFalse(
            os.path.exists(marker),
            "a value read from the host was executed as a program\n%s"
            % attack.report())


if __name__ == "__main__":
    unittest.main()
