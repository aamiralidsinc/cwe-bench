"""Consent is bound to one act on one document.

Every test drives the handler the app registers on ``doc_events`` — the same entry point frappe's
own dispatch uses — and asserts the act is refused (the site's permission error) *and* that nothing
happened: the target document keeps its state and no marker was spent.
"""
import unittest

import floor
from floor import Doc, SITE, _save, insert, Refusal

SI = "Sales Invoice"
ADS = "Asset Depreciation Schedule"
PR = "Payment Reconciliation"
JE = "Journal Entry"
SABB = "Serial and Batch Bundle"


def submitted(site, doc):
    """Run the submit handler and, if it was allowed, the write frappe performs for it."""
    floor.submit(doc)
    doc.docstatus = 1
    return doc


def cancelled(site, doc):
    """Run the cancel handler and, if it was allowed, the write frappe performs for it."""
    floor.cancel(doc)
    doc.docstatus = 2
    site.reversed.append((doc.doctype, doc.name))
    return doc


def erased(site, doc):
    floor.erase(doc)
    site.erased.append((doc.doctype, doc.name))
    return doc


class TestOneActNeverRidesAnotherActsAuthority(unittest.TestCase):
    def setUp(self):
        self.site = SITE.reset()

    def test_a_marker_minted_to_post_a_document_does_not_reverse_another_one(self):
        # One request. A credential authorised to post SI-0001, carrying the marker for SI-0001.
        # Inside that post the framework reverses a schedule the request named, which no human
        # authorised; the request must be refused and the schedule must keep its state.
        self.site.present("token-for-si-0001")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        si = Doc(SI, "SI-0001")
        schedule = Doc(ADS, "ADS-0001", in_insert=False)

        def cascade():
            cancelled(self.site, schedule)

        with self.assertRaises(Refusal):
            _save(si, lambda: (submitted(self.site, si), cascade()))
        self.assertEqual(schedule.docstatus, 0)
        self.assertEqual(self.site.reversed, [])

    def test_a_cascade_does_not_carry_an_authority_into_a_different_act(self):
        # The undo is authorised; while it runs it creates-and-posts a correction, which rides the
        # undo it is a consequence of; that correction then reverses a pre-existing document. The
        # authority a consequence carries is the act it actually performed, so the second reversal
        # is still a different act from the one any human authorised.
        self.site.present("token-for-pr-0001")
        self.site.mint(PR, "PR-0001", "cancel", "token-for-pr-0001")
        doc = Doc(PR, "PR-0001", in_insert=False, docstatus=1)
        correction = Doc(JE, "JE-CORRECTION", in_insert=True)
        old = Doc(JE, "JE-EXISTING", in_insert=False, docstatus=1)

        def at_root():
            def at_correction():
                cancelled(self.site, old)
            _save(correction, lambda: (submitted(self.site, correction), at_correction()))

        with self.assertRaises(Refusal):
            _save(doc, lambda: (cancelled(self.site, doc), at_root()))
        self.assertEqual(old.docstatus, 1)
        self.assertEqual(self.site.reversed, [(PR, "PR-0001")])

    def test_a_marker_minted_to_post_a_document_does_not_erase_another_one(self):
        # Erasing a document is its own act; a post that erases a document the request named is
        # not a consequence of posting.
        self.site.present("token-for-si-0001")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        si = Doc(SI, "SI-0001")
        bundle = Doc(SABB, "SABB-0001", in_insert=False, docstatus=1)

        def cascade():
            erased(self.site, bundle)

        with self.assertRaises(Refusal):
            _save(si, lambda: (submitted(self.site, si), cascade()))
        self.assertEqual(self.site.erased, [])

    def test_a_marker_does_not_authorise_the_document_it_was_amended_into(self):
        # A marker is bound to the document it names. The correction is a different document with
        # values the caller supplies; authorising the original is not authorising the copy.
        self.site.present("token-for-si-0001")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        self.site.amends(SI, "SI-0002", "SI-0001")
        copy = Doc(SI, "SI-0002")

        with self.assertRaises(Refusal):
            submitted(self.site, copy)
        self.assertEqual(copy.docstatus, 0)
        self.assertEqual(self.site.burn_state(SI, "SI-0001"), 0)


class TestOneRequestMayCarrySomeonesAuthorisationForEachAct(unittest.TestCase):
    """A request that performs more than one gated act carries more than one marker. Refusing the
    crossing must not make the legitimate case impossible."""

    def setUp(self):
        self.site = SITE.reset()

    def _arrange(self, header):
        self.site.present(header)
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        self.site.mint(ADS, "ADS-0001", "cancel", "token-for-ads-0001")
        si = Doc(SI, "SI-0001")
        schedule = Doc(ADS, "ADS-0001", in_insert=False, docstatus=1)

        def cascade():
            cancelled(self.site, schedule)

        return si, schedule, (lambda: _save(si, lambda: (submitted(self.site, si), cascade())))

    def test_whitespace_separated_markers_authorise_their_own_acts(self):
        _, schedule, run = self._arrange("token-for-si-0001 token-for-ads-0001")
        run()
        self.assertEqual(schedule.docstatus, 2)
        self.assertEqual(self.site.burn_state(SI, "SI-0001"), 1)
        self.assertEqual(self.site.burn_state(ADS, "ADS-0001"), 1)

    def test_comma_separated_markers_authorise_their_own_acts(self):
        # Order is not significant: the matching marker need not come first.
        _, schedule, run = self._arrange("token-for-ads-0001,token-for-si-0001")
        run()
        self.assertEqual(schedule.docstatus, 2)

    def test_several_markers_do_not_widen_which_document_they_authorise(self):
        # The request carries a valid marker for the post and a marker for a DIFFERENT schedule.
        # It must authorise the post and nothing else.
        self.site.present("token-for-si-0001 token-for-ads-0002")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        self.site.mint(ADS, "ADS-0002", "cancel", "token-for-ads-0002")
        si = Doc(SI, "SI-0001")
        schedule = Doc(ADS, "ADS-0001", in_insert=False, docstatus=1)

        def cascade():
            cancelled(self.site, schedule)

        with self.assertRaises(Refusal):
            _save(si, lambda: (submitted(self.site, si), cascade()))
        # The post is authorised by the marker minted for it; the other marker authorises nothing
        # else in the same request.
        self.assertEqual(si.docstatus, 1)
        self.assertEqual(schedule.docstatus, 1)
        self.assertEqual(self.site.reversed, [])

    def test_an_empty_entry_is_never_a_marker(self):
        # A record whose stored hash is the hash of an empty token (a marker minted from a blank
        # entry) must not be spendable by stray separators in the header.
        from pacioli_guard.scope import consent_token_hash
        self.site.present("token-for-si-0001 , , ")
        self.site.mint(SI, "SI-0001", "submit", "token-for-si-0001")
        self.site.mint(ADS, "ADS-0001", "cancel", "", token_hash=consent_token_hash(""))
        si = Doc(SI, "SI-0001")
        schedule = Doc(ADS, "ADS-0001", in_insert=False, docstatus=1)

        def cascade():
            cancelled(self.site, schedule)

        with self.assertRaises(Refusal):
            _save(si, lambda: (submitted(self.site, si), cascade()))
        self.assertEqual(si.docstatus, 1)
        self.assertEqual(schedule.docstatus, 1)
        self.assertEqual(self.site.burn_state(ADS, "ADS-0001"), 0)
