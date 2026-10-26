# -*- coding: utf-8 -*-
"""Record values sent as text are data and must never be executed."""

import os
import tempfile
import unittest

import world

world.install()

import fixtures

MARKER_PREFIX = "senaite_record_probe_"


def _marker_path():
    fd, path = tempfile.mkstemp(prefix=MARKER_PREFIX)
    os.close(fd)
    os.unlink(path)
    return path


def _payload(path):
    return "__import__('os').system('touch %s')" % path


def _call(route, portal, uid, fieldname, value):
    request = world.Request({"obj_uid": uid, fieldname: value},
                            path_info="/@@API/update")
    try:
        return route.update(portal, request)
    except Exception as exc:
        return exc


class RecordParsingTest(unittest.TestCase):

    def setUp(self):
        self.portal = fixtures.build_portal()
        from bika.lims.jsonapi.update import Update
        self.route = Update()
        self.markers = []
        world.user("labmanager", ["LabManager", "Manager", "Member"])

    def tearDown(self):
        for path in self.markers:
            if os.path.exists(path):
                os.unlink(path)

    def _attack(self, uid, path, fieldname, sentinel):
        obj = fixtures.obj(self.portal, path)
        obj._values[fieldname] = sentinel
        marker = _marker_path()
        self.markers.append(marker)

        _call(self.route, self.portal, uid, fieldname, _payload(marker))

        self.assertFalse(
            os.path.exists(marker),
            "the submitted record text was executed as code")
        # 2026-10-24 audit fix: the instruction treats record text as data and does not require
        # non-literal text to be refused, so only non-execution is asserted (no stored-value check).

    def test_records_field_text_is_not_executed(self):
        self._attack(fixtures.SERVICE_UID, "/service-1", "Conditions", [])

    def test_record_field_text_is_not_executed(self):
        self._attack(fixtures.REPORT_UID, "/report-1", "Template", {})

    def test_record_subfield_text_is_not_executed(self):
        self._attack(fixtures.ORG_UID, "/org-1", "PostalAddress", {})


if __name__ == "__main__":
    unittest.main()
