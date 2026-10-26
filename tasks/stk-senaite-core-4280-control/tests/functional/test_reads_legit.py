# -*- coding: utf-8 -*-
"""Information the product already returns keeps being returned."""

import unittest

import world

world.install()

import fixtures


class LegitReadsTest(unittest.TestCase):

    def setUp(self):
        self.portal = fixtures.build_portal()

    def _read(self, **values):
        import bika.lims.jsonapi.read as read_module
        values.setdefault("catalog_name", "uid_catalog")
        request = world.Request(values, path_info="/@@API/read")
        return read_module.read(self.portal, request)

    def test_computed_values_are_returned(self):
        world.user("analyst", ["Analyst", "Member"])

        result = self._read(UID=fixtures.AR_UID,
                            include_methods="getPrintAddress,getVATAmount")

        objects = result.get("objects", [])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].get("getPrintAddress"),
                         {"city": "Johannesburg"})
        self.assertEqual(objects[0].get("getVATAmount"), 42)

    def test_anonymous_can_still_read(self):
        world.logout()

        result = self._read(UID=fixtures.AR_UID, include_fields="Title")

        objects = result.get("objects", [])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].get("Title"), "Request 1")

    def test_analyst_can_read_fields(self):
        world.user("analyst", ["Analyst", "Member"])

        result = self._read(UID=fixtures.AR_UID, include_fields="Title")

        self.assertEqual(result.get("objects")[0].get("Title"), "Request 1")


if __name__ == "__main__":
    unittest.main()
