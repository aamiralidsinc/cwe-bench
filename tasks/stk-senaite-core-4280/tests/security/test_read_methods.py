# -*- coding: utf-8 -*-
"""A read must not run operations that change data the caller may not change."""

import unittest

import world

world.install()

import fixtures


def _read(portal, uid, include_methods):
    import bika.lims.jsonapi.read as read_module
    request = world.Request({"UID": uid,
                             "catalog_name": "uid_catalog",
                             "include_methods": include_methods},
                            path_info="/@@API/read")
    try:
        return read_module.read(portal, request)
    except Exception as exc:
        return exc


class ReadMethodsTest(unittest.TestCase):

    def setUp(self):
        self.portal = fixtures.build_portal()
        self.obj = fixtures.obj(self.portal, "/ar-1")
        self.obj._values["Priority"] = "normal"

    def test_analyst_read_does_not_run_state_changing_method(self):
        world.user("analyst", ["Analyst", "Member"])

        _read(self.portal, fixtures.AR_UID, "refreshTotals")

        self.assertEqual(self.obj._values.get("Priority"), "normal",
                         "a read ran a caller-named state-changing method")

    def test_anonymous_read_does_not_run_state_changing_method(self):
        world.logout()

        _read(self.portal, fixtures.AR_UID, "refreshTotals")

        self.assertEqual(self.obj._values.get("Priority"), "normal",
                         "a read ran a caller-named state-changing method")


if __name__ == "__main__":
    unittest.main()
