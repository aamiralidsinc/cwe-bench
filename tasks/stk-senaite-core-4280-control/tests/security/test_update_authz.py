# -*- coding: utf-8 -*-
"""A caller must not change data they are not allowed to change through update."""

import unittest

import world

world.install()

import fixtures


def _call(route, portal, uid, **fields):
    values = {"obj_uid": uid}
    values.update(fields)
    request = world.Request(values, path_info="/@@API/update")
    try:
        return route.update(portal, request)
    except Exception as exc:  # a refusal may be raised or reported
        return exc


def _refused(result):
    if isinstance(result, Exception):
        return True
    return isinstance(result, dict) and result.get("success") is False


class UpdateAuthzTest(unittest.TestCase):

    def setUp(self):
        self.portal = fixtures.build_portal()
        from bika.lims.jsonapi.update import Update
        self.route = Update()

    def test_analyst_cannot_change_field_without_field_permission(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        obj._values["Title"] = "Original"
        world.user("analyst", ["Analyst", "Member"])

        result = _call(self.route, self.portal, fixtures.AR_UID, Title="Changed")

        self.assertEqual(obj._values.get("Title"), "Original")
        self.assertTrue(_refused(result))

    def test_analyst_cannot_change_priority_field(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        obj._values["Priority"] = "normal"
        world.user("analyst", ["Analyst", "Member"])

        result = _call(self.route, self.portal, fixtures.AR_UID,
                       Priority="urgent")

        self.assertEqual(obj._values.get("Priority"), "normal")
        self.assertTrue(_refused(result))

    def test_anonymous_cannot_change_any_field(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        obj._values["Title"] = "Original"
        obj._values["Remarks"] = ""
        world.logout()

        result = _call(self.route, self.portal, fixtures.AR_UID,
                       Title="Changed")

        self.assertEqual(obj._values.get("Title"), "Original")
        self.assertTrue(_refused(result))

    def test_object_level_denial_is_respected(self):
        """The permission that matters is the one on the object being written."""
        obj = fixtures.obj(self.portal, "/ar-2")
        obj._values["Title"] = "Archived"
        world.user("labmanager", ["LabManager", "Manager", "Member"])

        result = _call(self.route, self.portal, fixtures.RESTRICTED_UID,
                       Title="Changed")

        self.assertEqual(obj._values.get("Title"), "Archived")
        self.assertTrue(_refused(result))


if __name__ == "__main__":
    unittest.main()
