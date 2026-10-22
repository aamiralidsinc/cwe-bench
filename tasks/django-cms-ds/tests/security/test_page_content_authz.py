"""Page content may only be obtained from pages the requesting user may view
(on the site the page lives on), translations may only be added to pages the
user may change, and pages may only be placed where the user may add them --
whichever request of the page administration is used."""
from cms.models import Page, PageContent

from cmsfix import ACCESS_PAGE, PagePermission, Scenario, page_with_text, marker, texts_containing


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
        """The duplicate URL names the restricted page itself."""
        copies, before = texts_containing(self.secret_mark).count(), self.snapshot()
        response = self.client.post(
            self.duplicate_url(self.secret, parent_page=self.team.pk),
            self.page_form("copied", source=self.secret.pk, parent_page=self.team.pk),
        )
        self.assertEqual(texts_containing(self.secret_mark).count(), copies, "restricted content was copied")
        self.assertRefused(response, before)

    def test_duplicate_restricted_source_into_own_page_translation(self):
        """Source plus a page the editor may change: no translation may receive the content."""
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
        """A manager of site 1 only, targeting a page of site 2 in a missing language."""
        foreign, _ = self.foreign_page()
        self.login(self.manager)
        before = self.snapshot()
        response = self.client.post(
            self.duplicate_url(self.other, language="fr"),
            self.page_form("etranger", source=self.other.pk, cms_page=foreign.pk),
        )
        self.assertFalse(PageContent.admin_manager.filter(page=foreign, language="fr").exists(),
                         "a translation was added to another site's page")
        self.assertRefused(response, before)


class CrossSiteSourceTests(Scenario):
    def test_duplicate_restricted_source_from_another_site(self):
        """A site-1 manager copies a board-restricted page of site 2."""
        foreign, foreign_mark = self.foreign_page()
        self.login(self.manager)
        copies, before = texts_containing(foreign_mark).count(), self.snapshot()
        response = self.client.post(
            self.duplicate_url(self.other, language="de", parent_page=self.team.pk),
            self.page_form("fremd", source=foreign.pk, parent_page=self.team.pk),
        )
        self.assertEqual(texts_containing(foreign_mark).count(), copies, "another site's restricted content was copied")
        self.assertRefused(response, before)

    def test_add_page_from_restricted_page_type_of_another_site(self):
        foreign_type, foreign_mark = self.foreign_page_type()
        self.login(self.manager)
        copies, before = texts_containing(foreign_mark).count(), self.snapshot()
        response = self.client.post(
            self.add_url(language="de", parent_page=self.team.pk),
            self.page_form("fremd", source=foreign_type.pk, parent_page=self.team.pk),
        )
        self.assertEqual(texts_containing(foreign_mark).count(), copies, "another site's restricted content was copied")
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
        """Adding a translation of the editor's own page with a restricted page type as source."""
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
        response = self.wizard_post(
            {"title": "From wizard", "slug": "from-wizard", "source": self.secret_type.pk, "content": ""},
            origin=self.news,
        )
        self.assertEqual(texts_containing(self.secret_type_mark).count(), copies, "restricted content was copied")
        self.assertRefused(response, before)


class PlacementTests(Scenario):
    def test_parent_page_posted_without_add_permission(self):
        """The announced parent is permitted; the posted parent is not."""
        before = self.snapshot()
        response = self.client.post(
            self.add_url(parent_page=self.team.pk),
            self.page_form("sneaky", parent_page=self.other.pk),
        )
        self.assertFalse(Page.objects.filter(parent=self.other).exists(),
                         "a page was created where the user may not add one")
        self.assertRefused(response, before)

    def test_root_page_when_only_the_announced_parent_is_permitted(self):
        """The request announces a permitted parent but asks for a page at the root."""
        before = self.snapshot()
        response = self.client.post(
            self.add_url(parent_page=self.team.pk),
            self.page_form("rooted", parent_page=""),
        )
        roots = Page.objects.filter(parent=None, site=self.site1, is_page_type=False)
        self.assertEqual(list(roots.values_list("pk", flat=True)), [self.home.pk],
                         "a root page was created where the user may not add one")
        self.assertRefused(response, before)


class TreeCopyTests(Scenario):
    def test_copy_tree_with_restricted_descendant(self):
        """A viewable page with a board-restricted child below it is copied."""
        child_mark = marker("CHILDREN")
        child = page_with_text("members", child_mark, parent=self.other)
        PagePermission.objects.create(group=self.board, page=child, grant_on=ACCESS_PAGE, can_view=True)
        self.login(self.editor)
        copies = texts_containing(child_mark).count()
        response = self.client.post(
            self.copy_url(self.other),
            {"source_site": self.site1.pk, "position": 0, "target": self.team.pk, "copy_permissions": ""},
        )
        self.assertLess(response.status_code, 500)
        self.assertEqual(texts_containing(child_mark).count(), copies, "restricted descendant content was copied")

    def test_copy_page_from_another_site(self):
        """A site-1 manager copies a restricted site-2 page, announcing site 1 as its site."""
        foreign, foreign_mark = self.foreign_page()
        self.login(self.manager)
        copies = texts_containing(foreign_mark).count()
        response = self.client.post(
            self.copy_url(foreign),
            {"source_site": self.site1.pk, "position": 0, "target": self.other.pk, "copy_permissions": ""},
        )
        self.assertLess(response.status_code, 500)
        self.assertEqual(texts_containing(foreign_mark).count(), copies, "another site's restricted content was copied")


class WizardContentPageTests(Scenario):
    def test_wizard_page_from_restricted_content_page(self):
        """The start-from selector lists only viewable pages; its value is posted anyway."""
        copies, before = texts_containing(self.secret_mark).count(), self.snapshot()
        response = self.wizard_post(
            {"title": "From wizard", "slug": "from-wizard", "content_page": self.secret.pk, "content": ""},
            origin=self.news,
        )
        self.assertLess(response.status_code, 500)
        self.assertEqual(texts_containing(self.secret_mark).count(), copies, "restricted content was copied")


class ImportContentTests(Scenario):
    def test_import_content_from_restricted_page(self):
        copies, before = texts_containing(self.secret_mark).count(), self.snapshot()
        response = self.client.post(
            self.import_url(self.team),
            {"source_page": self.secret.pk},
        )
        self.assertEqual(texts_containing(self.secret_mark).count(), copies, "restricted content was imported")
        self.assertRefused(response, before)


class CopyToSiteTests(Scenario):
    def test_copy_page_to_site_without_add_permission(self):
        before = Page.objects.filter(site=self.site2).count()
        response = self.client.post(
            self.copy_to_site_url(self.team),
            {"target_site": self.site2.pk},
        )
        self.assertLess(response.status_code, 500)
        self.assertEqual(Page.objects.filter(site=self.site2).count(), before,
                         "a page was created on a site the user does not administer")


class MovePlacementTests(Scenario):
    def test_move_own_page_to_site_root_without_add_permission(self):
        """A page the editor may move is placed at the site root, where only a
        site-wide add right (which the editor does not have) permits pages."""
        roots = list(Page.objects.filter(parent=None, site=self.site1, is_page_type=False)
                     .values_list("pk", flat=True))
        response = self.client.post(self.move_url(self.team), {"position": 1})
        self.assertLess(response.status_code, 500)
        self.team.refresh_from_db()
        self.assertEqual(self.team.parent_id, self.home.pk,
                         "the page was placed at the site root")
        self.assertEqual(
            list(Page.objects.filter(parent=None, site=self.site1, is_page_type=False)
                 .values_list("pk", flat=True)),
            roots,
            "the site's root pages were changed",
        )


class SetHomeTests(Scenario):
    def test_set_home_changes_the_current_home_page_without_change_right(self):
        """The editor may change the candidate page, but setting it as home
        demotes the current home page and re-paths its tree."""
        self.home.set_as_homepage()
        lobby = page_with_text("lobby", marker("LOBBY"))
        PagePermission.objects.create(
            user=self.editor, page=lobby, grant_on=ACCESS_PAGE,
            can_add=False, can_change=True, can_delete=True, can_publish=True, can_move_page=True,
        )
        self.login(self.editor)
        home_path = self.home.get_path("en")
        response = self.client.post(self.set_home_url(lobby), {})
        self.assertLess(response.status_code, 500)
        self.home.refresh_from_db()
        lobby.refresh_from_db()
        self.assertTrue(self.home.is_home, "the current home page was changed")
        self.assertFalse(lobby.is_home, "the page became the home page")
        self.assertEqual(self.home.get_path("en"), home_path, "the current home page was re-pathed")
