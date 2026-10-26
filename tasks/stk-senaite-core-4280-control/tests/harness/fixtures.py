# -*- coding: utf-8 -*-
"""World fixtures for the hidden suites.

Content objects use the product's *real* field classes, so the JSON API's own
type dispatch and the record fields' own setters run unchanged.
"""

import world

world.install()

from AccessControl.Permissions import ModifyPortalContent  # noqa: E402
from Products.Archetypes.Field import StringField  # noqa: E402
from bika.lims.browser.fields.addressfield import AddressField  # noqa: E402
from senaite.core.browser.fields.record import RecordField  # noqa: E402
from senaite.core.browser.fields.records import RecordsField  # noqa: E402

from world import Content  # noqa: E402
from world import Portal  # noqa: E402

PERM_ACCESS_JSONAPI = "senaite.core: Access JSON API"
PERM_EDIT_REMARKS = "senaite.core: Field: Edit Remarks"

ROLES_ALL = ["Analyst", "Client", "LabClerk", "LabManager", "Manager",
             "Publisher", "Sampler", "SamplingCoordinator", "Verifier"]

PERMISSIONS = {
    "Access contents information": ROLES_ALL + ["Anonymous"],
    "zope2.View": ROLES_ALL + ["Anonymous"],
    "View": ROLES_ALL + ["Anonymous"],
    "Modify portal content": ["LabManager", "Manager"],
    "Delete objects": ["LabManager", "Manager"],
    PERM_ACCESS_JSONAPI: ["LabManager", "Manager"],
    PERM_EDIT_REMARKS: ROLES_ALL,
}

AR_UID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaar"
SERVICE_UID = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbcs"
ORG_UID = "cccccccccccccccccccccccccccccco"
REPORT_UID = "dddddddddddddddddddddddddddddddf"
RESTRICTED_UID = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeer"


def _string(name, write_permission=ModifyPortalContent):
    return StringField(name, write_permission=write_permission)


class RequestRecord(Content):
    """A request-like record with the computed values the product exposes."""

    def getPrintAddress(self):
        return {"city": "Johannesburg"}

    def getVATAmount(self):
        return 42

    def refreshTotals(self):
        self._values["Priority"] = "high"
        return "refreshed"


def build_portal():
    portal = Portal("portal-uid", "/", title="SENAITE", permissions=PERMISSIONS)

    ar_fields = {
        "Title": _string("Title"),
        "Priority": _string("Priority"),
        "Remarks": _string("Remarks", write_permission=PERM_EDIT_REMARKS),
    }
    ar = RequestRecord(
        AR_UID, "/ar-1", title="Request 1",
        fields=ar_fields, permissions=PERMISSIONS, parent=portal)
    portal.register(ar)

    service = Content(
        SERVICE_UID, "/service-1", title="Calcium",
        fields={"Title": _string("Title"),
                "Conditions": RecordsField("Conditions")},
        permissions=PERMISSIONS, parent=portal)
    portal.register(service)

    organisation = Content(
        ORG_UID, "/org-1", title="Client 1",
        fields={"Title": _string("Title"),
                "PostalAddress": AddressField("PostalAddress")},
        permissions=PERMISSIONS, parent=portal)
    portal.register(organisation)

    report = Content(
        REPORT_UID, "/report-1", title="Report",
        fields={"Title": _string("Title"),
                "Template": RecordField("Template")},
        permissions=PERMISSIONS, parent=portal)
    portal.register(report)

    # The workflow of this record removed edit rights on it even for local
    # managers; the containing folder still grants them.
    restricted_perms = dict(PERMISSIONS)
    restricted_perms["Modify portal content"] = []
    restricted = Content(
        RESTRICTED_UID, "/ar-2", title="Archived request",
        fields={"Title": _string("Title")},
        permissions=restricted_perms, parent=portal)
    portal.register(restricted)

    world._PORTAL = portal
    import bika
    bika._harness_portal = portal
    return portal


def uid(portal, path):
    for obj in portal._objects.values():
        if obj._path == path:
            return obj.UID()
    raise KeyError(path)


def obj(portal, path):
    for o in portal._objects.values():
        if o._path == path:
            return o
    raise KeyError(path)
