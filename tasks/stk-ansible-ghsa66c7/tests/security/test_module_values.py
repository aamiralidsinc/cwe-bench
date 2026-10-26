# -*- coding: utf-8 -*-
"""A mapping supplied as text to a module must not be executed on the host."""

import os
import unittest

import runner


class ModuleValueTest(unittest.TestCase):

    def test_module_mapping_text_is_not_executed(self):
        benign = runner.run_playbook(
            runner.module_mapping_play_json("path=/tmp,size=2"))
        self.assertTrue(benign.ok, benign.report())
        self.assertIn("/tmp", benign.output)

        marker = runner.marker("module")
        attack = runner.run_playbook(
            runner.module_mapping_play_json(
                "{__import__('os').system('touch %s'): 1}" % marker))
        self.assertFalse(
            os.path.exists(marker),
            "a mapping supplied as text was executed on the managed host\n%s"
            % attack.report())


if __name__ == "__main__":
    unittest.main()
