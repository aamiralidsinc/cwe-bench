# -*- coding: utf-8 -*-
"""A caller must not change data they are not allowed to change through a batch update."""

import json
import unittest

import world

world.install()

import fixtures


def _call(route, portal, path, **fields):
    values = {"input_values": json.dumps({path: fields})}
    request = world.Request(values, path_info="/@@API/update_many")
    try:
        return route.update_many(portal, request)
    except Exception as exc:
        return exc


def _refused(result):
    if isinstance(result, Exception):
        return True
    if not isinstance(result, dict):
        return True
    return result.get("success") is False or result.get("error") is True


class UpdateManyAuthzTest(unittest.TestCase):

    def setUp(self):
        self.portal = fixtures.build_portal()
        from bika.lims.jsonapi.update import Update
        self.route = Update()

    def test_analyst_cannot_change_field_without_field_permission(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        obj._values["Title"] = "Original"
        world.user("analyst", ["Analyst", "Member"])

        result = _call(self.route, self.portal, "/ar-1", Title="Changed")

        self.assertEqual(obj._values.get("Title"), "Original")
        self.assertTrue(_refused(result))

    def test_anonymous_cannot_change_any_field(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        obj._values["Title"] = "Original"
        world.logout()

        result = _call(self.route, self.portal, "/ar-1", Title="Changed")

        self.assertEqual(obj._values.get("Title"), "Original")
        self.assertTrue(_refused(result))


if __name__ == "__main__":
    unittest.main()
