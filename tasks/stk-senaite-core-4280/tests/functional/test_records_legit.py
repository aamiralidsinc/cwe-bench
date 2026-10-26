# -*- coding: utf-8 -*-
"""Record values written as ordinary text keep saving."""

import unittest

import world

world.install()

import fixtures


class LegitRecordsTest(unittest.TestCase):

    def setUp(self):
        self.portal = fixtures.build_portal()
        from bika.lims.jsonapi.update import Update
        self.route = Update()
        world.user("labmanager", ["LabManager", "Manager", "Member"])

    def _update(self, uid, **fields):
        values = {"obj_uid": uid}
        values.update(fields)
        return self.route.update(
            self.portal, world.Request(values, path_info="/@@API/update"))

    def test_address_record_text_saves(self):
        obj = fixtures.obj(self.portal, "/org-1")
        value = ("{'address': '1 Wendy Way', 'city': 'Johannesburg', "
                 "'zip': '9000', 'state': 'Gauteng', 'district': '', "
                 "'country': 'South Africa'}")

        self._update(fixtures.ORG_UID, PostalAddress=value)

        self.assertEqual(obj._values.get("PostalAddress"),
                         {"address": "1 Wendy Way", "city": "Johannesburg",
                          "zip": "9000", "state": "Gauteng", "district": "",
                          "country": "South Africa"})

    def test_records_field_text_saves(self):
        obj = fixtures.obj(self.portal, "/service-1")
        value = "{'keyword': 'Ca', 'value': '1'}"

        self._update(fixtures.SERVICE_UID, Conditions=value)

        self.assertEqual(obj._values.get("Conditions"),
                         [{"keyword": "Ca", "value": "1"}])

    def test_record_field_text_saves(self):
        obj = fixtures.obj(self.portal, "/report-1")
        value = "{'name': 'report.pt'}"

        self._update(fixtures.REPORT_UID, Template=value)

        self.assertEqual(obj._values.get("Template"),
                         {"name": "report.pt"})


if __name__ == "__main__":
    unittest.main()
