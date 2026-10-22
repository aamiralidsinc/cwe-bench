"""Shared fixtures for the hidden tests.

Users
  editor   a section editor: may add and change pages in their own section
           ("team" and below) on site 1, nothing else.
  manager  may add and change every page of site 1, nothing on site 2.
  root     superuser.
Pages (site 1)
  home, team, team/news   the editor's section (team is under home)
  secret                  view-restricted to the "board" group (editor is not in it)
  other                   unrestricted; only root/manager may change it
Page types (site 1, on demand)
  open type         unrestricted
  board type        view-restricted to "board"

Every expected value is computed here with plain model queries.
"""
import uuid
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.test import TestCase

from cms.api import add_plugin, create_page, create_page_content
from cms.models import GlobalPagePermission, Page, PageContent, PagePermission
from cms.models.pluginmodel import CMSPlugin
from cms.utils.urlutils import admin_reverse

TEMPLATE = "nav_playground.html"
ACCESS_PAGE = 1
ACCESS_PAGE_AND_DESCENDANTS = 5

EDITOR_PERMS = (
    "add_page", "change_page", "delete_page", "publish_page",
    "add_text", "change_text", "delete_text",
)


def marker(label):
    return f"{label}-{uuid.uuid4().hex[:12]}"


def texts_containing(mark):
    """Every text plugin whose body carries ``mark`` (plain model query)."""
    from djangocms_text_ckeditor.models import Text

    return Text.objects.filter(body__contains=mark)


def page_with_text(title, mark, site=None, parent=None, languages=("en", "de", "fr")):
    """A page with a text plugin carrying ``mark`` in each of ``languages``."""
    kwargs = {"created_by": "fixture"}
    if site is not None:
        kwargs["site"] = site
    if parent is not None:
        kwargs["parent"] = parent
    page = create_page(title, TEMPLATE, languages[0], **kwargs)
    for language in languages:
        if language != languages[0]:
            create_page_content(language, f"{title} {language}", page, template=TEMPLATE, created_by="fixture")
        content = PageContent.admin_manager.get(page=page, language=language)
        placeholder = content.get_placeholders().get(slot="body")
        add_plugin(placeholder, "TextPlugin", language, body=f"<p>{mark}</p>")
    return page


def make_page_type(page):
    Page.objects.filter(pk=page.pk).update(is_page_type=True)
    page.refresh_from_db()
    return page


def staff_user(username, perms=EDITOR_PERMS):
    user = get_user_model().objects.create_user(username, f"{username}@example.com", username, is_staff=True)
    for codename in perms:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    return user


class Scenario(TestCase):
    """Base fixture. Subclasses drive the page admin and the page wizard over HTTP."""

    def setUp(self):
        User = get_user_model()
        self.site1 = Site.objects.get(pk=1)
        self.site2, _ = Site.objects.get_or_create(pk=2, defaults={"domain": "example2.com", "name": "two"})
        self.root = User.objects.create_superuser("root", "root@example.com", "root")
        self.board = Group.objects.create(name="board")

        self.editor = staff_user("editor")
        self.manager = staff_user("manager")
        gpp = GlobalPagePermission.objects.create(
            user=self.manager, can_add=True, can_change=True, can_delete=True, can_publish=True,
            can_change_advanced_settings=False, can_change_permissions=False, can_move_page=True,
        )
        gpp.sites.set([self.site1])

        self.home = create_page("home", TEMPLATE, "en", created_by="fixture")
        self.team_mark = marker("TEAM")
        self.team = page_with_text("team", self.team_mark, parent=self.home)
        self.news = create_page("news", TEMPLATE, "en", parent=self.team, created_by="fixture")
        PagePermission.objects.create(
            user=self.editor, page=self.team, grant_on=ACCESS_PAGE_AND_DESCENDANTS,
            can_add=True, can_change=True, can_delete=True, can_publish=True, can_move_page=True,
        )
        self.secret_mark = marker("SECRET")
        self.secret = page_with_text("secret", self.secret_mark, parent=self.home)
        PagePermission.objects.create(group=self.board, page=self.secret, grant_on=ACCESS_PAGE, can_view=True)
        self.other_mark = marker("OTHER")
        self.other = page_with_text("other", self.other_mark, parent=self.home)
        self.login(self.editor)

    def login(self, user):
        # Permission answers are cached, and so are sessions: reset both together.
        cache.clear()
        self.client.force_login(user)

    # -- page types ---------------------------------------------------------
    def add_page_types(self):
        root = create_page("Page Types", TEMPLATE, "en", slug="page_types", created_by="fixture")
        make_page_type(root)
        self.open_type_mark = marker("OPENTYPE")
        self.open_type = make_page_type(page_with_text("open type", self.open_type_mark, parent=root))
        self.secret_type_mark = marker("SECRETTYPE")
        self.secret_type = make_page_type(page_with_text("board type", self.secret_type_mark, parent=root))
        PagePermission.objects.create(
            group=self.board, page=self.secret_type, grant_on=ACCESS_PAGE, can_view=True,
        )
        self.login(self.current_user())
        return root

    def foreign_page_type(self, restricted=True):
        """A page type on site 2, restricted to "board"."""
        mark = marker("FOREIGNTYPE")
        page = make_page_type(page_with_text("foreign type", mark, site=self.site2, languages=("de",)))
        if restricted:
            PagePermission.objects.create(group=self.board, page=page, grant_on=ACCESS_PAGE, can_view=True)
        self.login(self.current_user())
        return page, mark

    def foreign_page(self, title="foreign"):
        """A page on site 2 restricted to "board", with a text plugin in de."""
        mark = marker("FOREIGN")
        page = page_with_text(title, mark, site=self.site2, languages=("de",))
        PagePermission.objects.create(group=self.board, page=page, grant_on=ACCESS_PAGE, can_view=True)
        self.login(self.current_user())
        return page, mark

    def current_user(self):
        return get_user_model().objects.get(pk=self.client.session["_auth_user_id"])

    def drop_translation(self, page, language):
        """Remove one translation (and its plugins) so a request can add it again."""
        for content in PageContent.admin_manager.filter(page=page, language=language):
            for placeholder in content.get_placeholders():
                placeholder.get_plugins().delete()
                placeholder.delete()
            content.delete()
        page.urls.filter(language=language).delete()
        self.login(self.current_user())

    # -- requests -----------------------------------------------------------
    def content_id(self, page, language="en"):
        return PageContent.admin_manager.get(page=page, language=language).pk

    def add_url(self, language="en", **query):
        return admin_reverse("cms_pagecontent_add") + "?" + urlencode({"language": language, **query})

    def duplicate_url(self, page, language="en", **query):
        endpoint = admin_reverse("cms_pagecontent_duplicate", args=(self.content_id(page),))
        return endpoint + "?" + urlencode({"language": language, **query})

    def copy_url(self, page):
        return admin_reverse("cms_page_copy_page", args=(page.pk,))

    def copy_to_site_url(self, page):
        return admin_reverse("cms_page_copy_to_site", args=(page.pk,))

    def import_url(self, page, language="en"):
        return admin_reverse("cms_pagecontent_import_content", args=(self.content_id(page, language),))

    def move_url(self, page):
        return admin_reverse("cms_page_move_page", args=(page.pk,))

    def set_home_url(self, page):
        return admin_reverse("cms_page_set_home", args=(page.pk,))

    def page_form(self, slug, **extra):
        data = {"title": slug.title(), "slug": slug, "menu_title": "", "page_title": "",
                "meta_description": "", "source": "", "cms_page": "", "parent_page": ""}
        data.update({k: ("" if v is None else str(v)) for k, v in extra.items()})
        return data

    def wizard_post(self, step2, origin, language="en"):
        """Run the "New page" wizard from ``origin`` (the new page becomes its sibling)."""
        from cms.cms_wizards import cms_page_wizard

        endpoint = admin_reverse("cms_wizard_create")
        step1 = {
            "wizard_create_view-current_step": "0",
            "0-entry": cms_page_wizard.id,
            "0-language": language,
            "0-page": origin.pk,
        }
        r1 = self.client.post(endpoint, step1)
        self.assertEqual(r1.status_code, 200, "wizard step 1 was not accepted")
        self.assertNotContains(r1, "errorlist")
        data = {"wizard_create_view-current_step": "1"}
        data.update({f"1-{k}": ("" if v is None else str(v)) for k, v in step2.items()})
        return self.client.post(endpoint, data)

    # -- assertions ---------------------------------------------------------
    def snapshot(self):
        return (Page.objects.count(), PageContent.admin_manager.count(), CMSPlugin.objects.count())

    def assertRefused(self, response, before):
        """Blocked: the request did not complete (the form is shown again with an
        error, a client error is returned, or the user is redirected away) and
        nothing was written. The snapshot is what proves the refusal."""
        self.assertLess(response.status_code, 500)
        self.assertNotIn(b"cms-view-new-object", response.content, "request succeeded (modal redirect)")
        self.assertEqual(self.snapshot(), before, "the refused request changed pages, contents or plugins")

    def assertCreated(self, response):
        self.assertIn(response.status_code, (200, 302))
        if response.status_code == 200:
            self.assertNotIn(b"errornote", response.content, "the form was refused")
            self.assertNotIn(b"errorlist", response.content, "the form was refused")
