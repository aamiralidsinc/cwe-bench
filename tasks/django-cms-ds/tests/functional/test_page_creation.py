"""Legitimate page creation, translation, tree copy, content import and
cross-site copy keep working for users who have the corresponding rights."""
from cms.models import Page, PageContent

from cmsfix import (
    Scenario,
    marker,
    page_with_text,
    texts_containing,
)


class DuplicateTests(Scenario):
    def test_editor_duplicates_own_section_page(self):
        copies = texts_containing(self.team_mark).count()
        response = self.client.post(
            self.duplicate_url(self.team, parent_page=self.team.pk),
            self.page_form("copied", source=self.team.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(texts_containing(self.team_mark).count(), copies + 1, "the page was not copied")

    def test_editor_opens_duplicate_form_for_own_page(self):
        response = self.client.get(self.duplicate_url(self.team, parent_page=self.team.pk))
        self.assertEqual(response.status_code, 200)

    def test_superuser_duplicates_restricted_page(self):
        self.login(self.root)
        copies = texts_containing(self.secret_mark).count()
        response = self.client.post(
            self.duplicate_url(self.secret, parent_page=self.team.pk),
            self.page_form("copied", source=self.secret.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(texts_containing(self.secret_mark).count(), copies + 1, "the page was not copied")

    def test_manager_duplicates_page_of_their_site(self):
        self.login(self.manager)
        copies = texts_containing(self.other_mark).count()
        response = self.client.post(
            self.duplicate_url(self.other, parent_page=self.team.pk),
            self.page_form("copied", source=self.other.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(texts_containing(self.other_mark).count(), copies + 1, "the page was not copied")


class AddPageAndTranslationTests(Scenario):
    def test_editor_adds_plain_page_in_section(self):
        before = Page.objects.count()
        response = self.client.post(
            self.add_url(parent_page=self.team.pk),
            self.page_form("kid", parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(Page.objects.count(), before + 1, "the page was not created")
        self.assertTrue(Page.objects.filter(parent=self.team).exists())

    def test_editor_adds_translation_to_own_page(self):
        self.drop_translation(self.team, "de")
        response = self.client.post(
            self.add_url(language="de", cms_page=self.team.pk, parent_page=self.team.pk),
            self.page_form("team-de", cms_page=self.team.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertTrue(PageContent.admin_manager.filter(page=self.team, language="de").exists(),
                        "the translation was not added")

    def test_manager_adds_translation_to_page_of_their_site(self):
        self.login(self.manager)
        self.drop_translation(self.other, "de")
        response = self.client.post(
            self.add_url(language="de", cms_page=self.other.pk, parent_page=self.team.pk),
            self.page_form("andere", cms_page=self.other.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertTrue(PageContent.admin_manager.filter(page=self.other, language="de").exists(),
                        "the translation was not added")

    def test_manager_opens_add_translation_form(self):
        self.login(self.manager)
        response = self.client.get(self.add_url(language="de", cms_page=self.other.pk, parent_page=self.team.pk))
        self.assertEqual(response.status_code, 200)


class PageTypeTests(Scenario):
    def test_add_form_offers_page_types_of_this_site(self):
        self.add_page_types()
        response = self.client.get(self.add_url(parent_page=self.team.pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "open type")

    def test_editor_creates_page_from_open_page_type(self):
        self.add_page_types()
        before = Page.objects.count()
        response = self.client.post(
            self.add_url(parent_page=self.team.pk),
            self.page_form("from-type", source=self.open_type.pk, parent_page=self.team.pk),
        )
        self.assertCreated(response)
        self.assertEqual(Page.objects.count(), before + 1, "the page was not created")
        self.assertGreater(texts_containing(self.open_type_mark).count(), 0)

    def test_wizard_creates_page_from_open_page_type(self):
        self.add_page_types()
        before = Page.objects.count()
        response = self.wizard_post(
            {"title": "From wizard", "slug": "from-wizard", "source": self.open_type.pk, "content": ""},
            origin=self.news,
        )
        self.assertCreated(response)
        self.assertEqual(Page.objects.count(), before + 1, "the page was not created")

    def test_wizard_creates_plain_page(self):
        before = Page.objects.count()
        response = self.wizard_post(
            {"title": "Plain wizard", "slug": "plain-wizard", "content": ""},
            origin=self.news,
        )
        self.assertCreated(response)
        self.assertEqual(Page.objects.count(), before + 1, "the page was not created")

    def test_wizard_starts_from_a_viewable_page(self):
        copies = texts_containing(self.team_mark).count()
        response = self.wizard_post(
            {"title": "From page", "slug": "from-page", "content_page": self.team.pk, "content": ""},
            origin=self.news,
        )
        self.assertCreated(response)
        self.assertEqual(texts_containing(self.team_mark).count(), copies + 1,
                         "the selected page's content was not used")


class TreeCopyTests(Scenario):
    def test_editor_copies_own_tree_with_descendants(self):
        kid_mark = marker("KID")
        page_with_text("kid", kid_mark, parent=self.team)
        self.login(self.editor)
        before = Page.objects.count()
        copies = texts_containing(kid_mark).count()
        response = self.client.post(
            self.copy_url(self.team),
            {"source_site": self.site1.pk, "position": 0, "target": self.team.pk, "copy_permissions": ""},
        )
        self.assertLess(response.status_code, 500)
        self.assertGreater(Page.objects.count(), before, "the tree was not copied")
        self.assertGreater(texts_containing(kid_mark).count(), copies, "the descendant was not copied")


class ImportContentTests(Scenario):
    def test_editor_imports_content_from_a_viewable_page(self):
        copies = texts_containing(self.other_mark).count()
        response = self.client.post(self.import_url(self.team), {"source_page": self.other.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(texts_containing(self.other_mark).count(), copies + 1,
                         "the content was not imported")


class CopyToSiteTests(Scenario):
    def test_superuser_copies_page_to_another_site(self):
        self.login(self.root)
        before = Page.objects.filter(site=self.site2).count()
        response = self.client.post(self.copy_to_site_url(self.team), {"target_site": self.site2.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Page.objects.filter(site=self.site2).count(), before + 1,
                         "the page was not copied to the other site")


class MovePlacementTests(Scenario):
    def test_editor_moves_own_page_under_permitted_target(self):
        response = self.client.post(
            self.move_url(self.news),
            {"target": self.team.pk, "position": 0},
        )
        self.assertLess(response.status_code, 500)
        self.news.refresh_from_db()
        self.assertEqual(self.news.parent_id, self.team.pk, "the page was not moved")

    def test_manager_moves_page_to_site_root(self):
        """A user who may add pages across the site still moves a page to the root."""
        self.login(self.manager)
        response = self.client.post(self.move_url(self.news), {"position": 1})
        self.assertLess(response.status_code, 500)
        self.news.refresh_from_db()
        self.assertIsNone(self.news.parent_id, "the page was not placed at the site root")


class SetHomeTests(Scenario):
    def test_manager_sets_new_home_page(self):
        """A user who may change every page of the site still sets a new home."""
        self.home.set_as_homepage()
        lobby = page_with_text("lobby", marker("LOBBY"))
        self.login(self.manager)
        response = self.client.post(self.set_home_url(lobby), {})
        self.assertEqual(response.status_code, 200)
        lobby.refresh_from_db()
        self.assertTrue(lobby.is_home, "the page was not made the home page")
