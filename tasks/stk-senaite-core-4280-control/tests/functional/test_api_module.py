# -*- coding: utf-8 -*-
"""Helpers defined on the product's own API module stay reachable."""

import ast
import types
import unittest

import world

world.install()


class ApiModuleReachTest(unittest.TestCase):

    def test_source_defined_helpers_are_reachable(self):
        """A helper the fix adds to the product API module must resolve here.

        The harness provides a small stand-in for ``bika.lims.api``; a fix may
        add its own helper to the real module.  Every function the product
        source defines and the stand-in does not must still be reachable.
        """
        from bika.lims import api

        handle = open(world.API_SOURCE)
        try:
            tree = ast.parse(handle.read(), world.API_SOURCE)
        finally:
            handle.close()
        defined = [node.name for node in tree.body
                   if isinstance(node, ast.FunctionDef)]
        stubbed = set(dir(type(api))) | set(api.__dict__)
        candidates = [name for name in defined if name not in stubbed]

        self.assertTrue(candidates, "no source-defined helper to resolve")
        helper = None
        for name in candidates:
            value = getattr(api, name)
            if isinstance(value, types.FunctionType):
                helper = value
                break
        self.assertIsNotNone(helper, "source-defined helpers are unreachable")
        self.assertEqual(helper.func_code.co_filename, world.API_SOURCE)


if __name__ == "__main__":
    unittest.main()
