"""What legitimate use of the gate looks like, and must keep looking like.

These cover the behaviour next to every part of the gate: an authorised act proceeds and spends its
marker once; the framework's own consequences of an authorised act do not need markers of their own;
undoing is still possible; and a credential that is not consent-gated is untouched. A fix that
hardens the gate by refusing more than the flaw requires fails here.
"""
import unittest

import floor
from floor import Doc, SITE, _save, insert, Refusal

SI = "Sales Invoice"
ADS = "Asset Depreciation Schedule"
PR = "Payment Reconciliation"
JE = "Journal Entry"
PLE = "Payment Ledger Entry"


def submitted(doc):
    floor.submit(doc)
    doc.docstatus = 1
    return doc


def cancelled(site, doc):
    floor.cancel(doc)
    doc.docstatus = 2
    site.reversed.append((doc.doctype, doc.name))
    return doc


class TestAnAuthorisedActProceeds(unittest.TestCase):
    def setUp(self):
        self.site = SITE.reset()

    def test_a_document_with_its_own_marker_is_posted_and_the_marker_spent(self):
        self.site.present("token-for-si-0001")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        doc = submitted(Doc(SI, "SI-0001"))
        self.assertEqual(doc.docstatus, 1)
        self.assertEqual(self.site.burn_state(SI, "SI-0001"), 1)

    def test_a_marker_is_spent_once_and_a_replay_is_refused(self):
        self.site.present("token-for-si-0001")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        submitted(Doc(SI, "SI-0001"))
        with self.assertRaises(Refusal):
            submitted(Doc(SI, "SI-0001"))

    def test_a_document_with_no_marker_is_refused(self):
        self.site.present("")
        with self.assertRaises(Refusal):
            submitted(Doc(SI, "SI-0001"))

    def test_a_background_context_with_no_request_is_refused(self):
        # No request means no header: a gated principal that cannot present consent is refused.
        def no_request(key, default=None):
            raise RuntimeError("no request in this context")

        floor.FRAPPE.get_request_header = no_request
        try:
            with self.assertRaises(Refusal):
                submitted(Doc(SI, "SI-0001"))
        finally:
            floor.FRAPPE.get_request_header = (
                lambda key, default=None: SITE.headers.get(key, default))

    def test_erasing_with_its_own_marker_is_allowed(self):
        self.site.present("token-to-erase-si-0001")
        self.site.mint(SI, "SI-0001", "delete", "token-to-erase-si-0001")
        floor.erase(Doc(SI, "SI-0001", in_insert=False, docstatus=1))
        self.assertEqual(self.site.burn_state(SI, "SI-0001"), 1)

    def test_a_document_that_amends_another_is_posted_with_its_own_marker(self):
        self.site.present("token-for-si-0002")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        self.site.mint(SI, "SI-0002", "submit", "token-for-si-0002")
        self.site.amends(SI, "SI-0002", "SI-0001")
        doc = submitted(Doc(SI, "SI-0002"))
        self.assertEqual(doc.docstatus, 1)
        self.assertEqual(self.site.burn_state(SI, "SI-0002"), 1)
        self.assertEqual(self.site.burn_state(SI, "SI-0001"), 0)


class TestTheFrameworksConsequencesRideTheConsentedAct(unittest.TestCase):
    def setUp(self):
        self.site = SITE.reset()

    def test_a_ledger_document_the_act_creates_while_posting_rides_it(self):
        # A document that does not exist until the post runs cannot have a marker of its own.
        self.site.present("token-for-si-0001")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        si = Doc(SI, "SI-0001")

        def cascade():
            submitted(Doc(PLE, "PLE-0001", in_insert=True))

        _save(si, lambda: (submitted(si), cascade()))
        self.assertEqual(self.site.burn_state(SI, "SI-0001"), 1)
        self.assertEqual(len(self.site.burned), 1)

    def test_an_undo_cascades_into_further_undos(self):
        # Cancelling an invoice makes the framework cancel the documents it generated. Those have
        # names a human COULD have been asked about, but an undo cascading into undos is how the
        # product's undo works and the gate must keep allowing it.
        self.site.present("token-for-si-0001")
        self.site.mint(SI, "SI-0001", "cancel", "token-for-si-0001")
        si = Doc(SI, "SI-0001", in_insert=False, docstatus=1)

        def cascade():
            cancelled(self.site, Doc(JE, "JE-CREDIT-NOTE", in_insert=False, docstatus=1))
            cancelled(self.site, Doc(JE, "JE-GAIN-LOSS", in_insert=False, docstatus=1))

        _save(si, lambda: (cancelled(self.site, si), cascade()))
        self.assertEqual(len(self.site.reversed), 3)
        self.assertEqual(len(self.site.burned), 1)

    def test_a_correction_the_undo_creates_and_posts_rides_the_undo(self):
        # The undo creates a correction document and posts it in the same write. It did not exist
        # when the marker was minted, so it rides the undo it is a consequence of.
        self.site.present("token-for-si-0001")
        self.site.mint(SI, "SI-0001", "cancel", "token-for-si-0001")
        si = Doc(SI, "SI-0001", in_insert=False, docstatus=1)

        def cascade():
            submitted(Doc(JE, "JE-CORRECTION", in_insert=True))

        _save(si, lambda: (cancelled(self.site, si), cascade()))
        self.assertEqual(si.docstatus, 2)


class TestACredentialThatIsNotConsentGatedIsUntouched(unittest.TestCase):
    def test_no_grant_at_all(self):
        site = SITE.reset(grant=False)
        doc = Doc(SI, "SI-0001")

        def cascade():
            cancelled(site, Doc(ADS, "ADS-0001", in_insert=False, docstatus=1))

        _save(doc, lambda: (submitted(doc), cascade()))
        self.assertEqual(doc.docstatus, 1)

    def test_a_grant_with_consent_turned_off(self):
        site = SITE.reset(require_consent=0)
        doc = Doc(SI, "SI-0001")

        def cascade():
            cancelled(site, Doc(ADS, "ADS-0001", in_insert=False, docstatus=1))

        _save(doc, lambda: (submitted(doc), cascade()))
        self.assertEqual(doc.docstatus, 1)
        floor.erase(Doc(SI, "SI-0009", in_insert=False, docstatus=1))
