"""Legitimate page creation keeps working: duplicating, building from page types
(admin and wizard), and adding translations, for users entitled to do so."""
from django.contrib.auth.models import Group

from cms.models import Page, PageContent

from cmsfix import Scenario, texts_containing


class DuplicateTests(Scenario):
    def test_editor_duplicates_own_section_page(self):
        copies = texts_containing(self.team_mark).count()
        pages = Page.objects.count()
        response = self.client.post(
            self.duplicate_url(self.team, parent_page=self.team.pk),
            self.page_form("team-copy", source=self.team.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(Page.objects.count(), pages + 1)
        self.assertEqual(texts_containing(self.team_mark).count(), copies + 1)

    def test_editor_opens_duplicate_form_for_own_page(self):
        response = self.client.get(self.duplicate_url(self.team, parent_page=self.team.pk))
        self.assertEqual(response.status_code, 200)

    def test_superuser_duplicates_restricted_page(self):
        self.login(self.root)
        copies = texts_containing(self.secret_mark).count()
        response = self.client.post(
            self.duplicate_url(self.secret),
            self.page_form("secret-copy", source=self.secret.pk),
        )
        self.assertCreated(response)
        self.assertEqual(texts_containing(self.secret_mark).count(), copies + 1)

    def test_manager_duplicates_page_of_their_site(self):
        self.login(self.manager)
        copies = texts_containing(self.other_mark).count()
        response = self.client.post(
            self.duplicate_url(self.other),
            self.page_form("other-copy", source=self.other.pk),
        )
        self.assertCreated(response)
        self.assertEqual(texts_containing(self.other_mark).count(), copies + 1)


class PageTypeTests(Scenario):
    def test_add_form_offers_page_types_of_this_site(self):
        self.add_page_types()
        response = self.client.get(self.add_url(parent_page=self.team.pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "open type")

    def test_editor_creates_page_from_open_page_type(self):
        self.add_page_types()
        copies = texts_containing(self.open_type_mark).count()
        response = self.client.post(
            self.add_url(parent_page=self.team.pk),
            self.page_form("from-open-type", source=self.open_type.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(texts_containing(self.open_type_mark).count(), copies + 1)
        new = PageContent.admin_manager.get(page__urls__slug="from-open-type", language="en")
        self.assertEqual(new.page.parent_id, self.team.pk)
        self.assertFalse(new.page.is_page_type)

    def test_board_member_creates_page_from_board_page_type(self):
        self.add_page_types()
        self.editor.groups.add(Group.objects.get(name="board"))
        self.login(self.editor)
        copies = texts_containing(self.secret_type_mark).count()
        response = self.client.post(
            self.add_url(parent_page=self.team.pk),
            self.page_form("from-board-type", source=self.secret_type.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(texts_containing(self.secret_type_mark).count(), copies + 1)

    def test_wizard_creates_page_from_open_page_type(self):
        self.add_page_types()
        copies = texts_containing(self.open_type_mark).count()
        response = self.wizard_post({"title": "Wizard page", "slug": "wizard-page",
                                     "source": self.open_type.pk, "content": ""}, origin=self.news)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cms-view-new-object")
        self.assertEqual(texts_containing(self.open_type_mark).count(), copies + 1)

    def test_wizard_creates_plain_page(self):
        pages = Page.objects.count()
        response = self.wizard_post({"title": "Plain wizard", "slug": "plain-wizard", "content": ""},
                                    origin=self.news)
        self.assertContains(response, "cms-view-new-object")
        self.assertEqual(Page.objects.count(), pages + 1)


class AddPageAndTranslationTests(Scenario):
    def test_editor_adds_plain_page_in_section(self):
        pages = Page.objects.count()
        response = self.client.post(
            self.add_url(parent_page=self.team.pk),
            self.page_form("plain", parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(Page.objects.count(), pages + 1)

    def test_editor_adds_translation_to_own_page(self):
        self.drop_translation(self.team, "de")
        pages = Page.objects.count()
        response = self.client.post(
            self.add_url(language="de", cms_page=self.team.pk, parent_page=self.team.pk),
            self.page_form("team-de", cms_page=self.team.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertTrue(PageContent.admin_manager.filter(page=self.team, language="de").exists())
        self.assertEqual(Page.objects.count(), pages)

    def test_manager_adds_translation_to_page_of_their_site(self):
        self.drop_translation(self.other, "de")
        self.login(self.manager)
        response = self.client.post(
            self.add_url(language="de", cms_page=self.other.pk),
            self.page_form("andere", cms_page=self.other.pk),
        )
        self.assertCreated(response)
        self.assertTrue(PageContent.admin_manager.filter(page=self.other, language="de").exists())

    def test_manager_opens_add_translation_form(self):
        self.drop_translation(self.other, "de")
        self.login(self.manager)
        response = self.client.get(self.add_url(language="de", cms_page=self.other.pk))
        self.assertEqual(response.status_code, 200)
