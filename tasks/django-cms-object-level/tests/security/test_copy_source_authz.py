"""A page's content may only be copied into a new page or translation by a user
who may view that page, and a translation may only be added to an existing page
the user may change -- whichever way the page is created."""
from cms.api import create_page
from cms.models import PageContent

from cmsfix import Scenario, texts_containing


class DuplicateSourceTests(Scenario):
    def test_duplicate_own_page_with_restricted_source_in_body(self):
        """Duplicate form opened on the editor's own page, source swapped in the POST body."""
        copies, before = texts_containing(self.secret_mark).count(), self.snapshot()
        response = self.client.post(
            self.duplicate_url(self.team, parent_page=self.team.pk),
            self.page_form("copied", source=self.secret.pk, parent_page=self.team.pk),
        )
        self.assertEqual(texts_containing(self.secret_mark).count(), copies, "restricted content was copied")
        self.assertRefused(response, before)

    def test_duplicate_restricted_page_from_its_url(self):
        copies, before = texts_containing(self.secret_mark).count(), self.snapshot()
        response = self.client.post(
            self.duplicate_url(self.secret, parent_page=self.team.pk),
            self.page_form("copied", source=self.secret.pk, parent_page=self.team.pk),
        )
        self.assertEqual(texts_containing(self.secret_mark).count(), copies, "restricted content was copied")
        self.assertRefused(response, before)

    def test_duplicate_restricted_source_into_own_page_translation(self):
        """Source plus a page the editor may change: the editor's page must not
        receive the restricted page's content as a new translation."""
        self.drop_translation(self.team, "de")
        copies, before = texts_containing(self.secret_mark).count(), self.snapshot()
        response = self.client.post(
            self.duplicate_url(self.team, language="de", parent_page=self.team.pk),
            self.page_form("kopie", source=self.secret.pk, cms_page=self.team.pk, parent_page=self.team.pk),
        )
        self.assertEqual(texts_containing(self.secret_mark).count(), copies, "restricted content was copied")
        self.assertRefused(response, before)


class TranslationTargetTests(Scenario):
    def test_add_translation_to_page_user_cannot_change(self):
        self.drop_translation(self.other, "de")
        before = self.snapshot()
        response = self.client.post(
            self.add_url(language="de", cms_page=self.other.pk, parent_page=self.team.pk),
            self.page_form("andere", cms_page=self.other.pk, parent_page=self.team.pk),
        )
        self.assertFalse(PageContent.admin_manager.filter(page=self.other, language="de").exists(),
                         "a translation was added to a page the user may not change")
        self.assertRefused(response, before)

    def test_duplicate_into_page_user_cannot_change(self):
        self.drop_translation(self.other, "de")
        before = self.snapshot()
        response = self.client.post(
            self.duplicate_url(self.team, language="de", parent_page=self.team.pk),
            self.page_form("kopie", source=self.team.pk, cms_page=self.other.pk, parent_page=self.team.pk),
        )
        self.assertFalse(PageContent.admin_manager.filter(page=self.other, language="de").exists(),
                         "a translation was added to a page the user may not change")
        self.assertRefused(response, before)

    def test_duplicate_into_page_of_another_site(self):
        """A manager of site 1 only, targeting a page of site 2."""
        foreign = create_page("fremd", "nav_playground.html", "de", site=self.site2, created_by="fixture")
        self.login(self.manager)
        before = self.snapshot()
        response = self.client.post(
            self.duplicate_url(self.other, language="fr"),
            self.page_form("etranger", source=self.other.pk, cms_page=foreign.pk),
        )
        self.assertFalse(PageContent.admin_manager.filter(page=foreign, language="fr").exists(),
                         "a translation was added to another site's page")
        self.assertRefused(response, before)


class PageTypeSourceTests(Scenario):
    def test_add_page_from_restricted_page_type(self):
        self.add_page_types()
        copies, before = texts_containing(self.secret_type_mark).count(), self.snapshot()
        response = self.client.post(
            self.add_url(parent_page=self.team.pk),
            self.page_form("from-type", source=self.secret_type.pk, parent_page=self.team.pk),
        )
        self.assertEqual(texts_containing(self.secret_type_mark).count(), copies, "restricted content was copied")
        self.assertRefused(response, before)

    def test_add_translation_from_restricted_page_type(self):
        """Adding a translation of the editor's own page with a page type as source."""
        self.add_page_types()
        self.drop_translation(self.team, "de")
        copies, before = texts_containing(self.secret_type_mark).count(), self.snapshot()
        response = self.client.post(
            self.add_url(language="de", cms_page=self.team.pk, parent_page=self.team.pk),
            self.page_form("team-de", source=self.secret_type.pk, cms_page=self.team.pk, parent_page=self.team.pk),
        )
        self.assertEqual(texts_containing(self.secret_type_mark).count(), copies, "restricted content was copied")
        self.assertRefused(response, before)

    def test_wizard_page_from_restricted_page_type(self):
        self.add_page_types()
        copies, before = texts_containing(self.secret_type_mark).count(), self.snapshot()
        response = self.wizard_post({"title": "From wizard", "slug": "from-wizard",
                                     "source": self.secret_type.pk, "content": ""}, origin=self.news)
        self.assertEqual(texts_containing(self.secret_type_mark).count(), copies, "restricted content was copied")
        self.assertRefused(response, before)

