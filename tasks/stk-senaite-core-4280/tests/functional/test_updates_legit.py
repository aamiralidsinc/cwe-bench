# -*- coding: utf-8 -*-
"""Edits a caller is allowed to make keep working."""

import json
import unittest

import world

world.install()

import fixtures


class LegitUpdatesTest(unittest.TestCase):

    def setUp(self):
        self.portal = fixtures.build_portal()
        from bika.lims.jsonapi.update import Update
        self.route = Update()

    def _update(self, uid, **fields):
        values = {"obj_uid": uid}
        values.update(fields)
        return self.route.update(
            self.portal, world.Request(values, path_info="/@@API/update"))

    def test_analyst_can_save_remarks(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        world.user("analyst", ["Analyst", "Member"])

        result = self._update(fixtures.AR_UID, Remarks="checked today")

        self.assertTrue(result.get("success"))
        self.assertEqual(obj._values.get("Remarks"), "checked today")

    def test_analyst_can_save_remarks_in_batch(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        world.user("analyst", ["Analyst", "Member"])
        request = world.Request(
            {"input_values": json.dumps({"/ar-1": {"Remarks": "batch note"}})},
            path_info="/@@API/update_many")

        result = self.route.update_many(self.portal, request)

        self.assertTrue(result.get("success"))
        self.assertEqual(obj._values.get("Remarks"), "batch note")

    def test_manager_can_save_ordinary_field(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        world.user("labmanager", ["LabManager", "Manager", "Member"])

        result = self._update(fixtures.AR_UID, Title="Renamed request")

        self.assertTrue(result.get("success"))
        self.assertEqual(obj._values.get("Title"), "Renamed request")

    def test_manager_can_save_priority(self):
        obj = fixtures.obj(self.portal, "/ar-1")
        world.user("labmanager", ["LabManager", "Manager", "Member"])

        result = self._update(fixtures.AR_UID, Priority="urgent")

        self.assertTrue(result.get("success"))
        self.assertEqual(obj._values.get("Priority"), "urgent")


if __name__ == "__main__":
    unittest.main()
