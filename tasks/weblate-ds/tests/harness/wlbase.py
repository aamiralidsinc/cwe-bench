"""Shared fixtures for the hidden suites. Not product code."""

from __future__ import annotations

from weblate.auth.models import Group, UserBlock
from weblate.trans.models import Project
from weblate.trans.tests.test_views import ViewTestCase

MISSING = 99999999


class AccessTestBase(ViewTestCase):
    """Base with the data shapes the security properties talk about."""

    def create_private(self, name: str = "Private", slug: str = "private"):
        project = self.create_project(
            name=name, slug=slug, access_control=Project.ACCESS_PRIVATE
        )
        component = self.create_po(project=project, name=slug)
        translation = component.translation_set.get(language__code="cs")
        return project, component, translation

    def unit_of(self, translation, source: str = "Hello, world!\n"):
        return translation.unit_set.get(source__startswith=source)

    def grant_broad_access(self):
        self.user.groups.add(Group.objects.get(name="Managers"))
        self.user.clear_cache()

    def grant_broad_access_and_block(self, project):
        self.grant_broad_access()
        UserBlock.objects.create(user=self.user, project=project)
        self.user.clear_cache()

    def assert_hidden_is_indistinguishable(self, hidden, missing):
        """Both requests refer to something the user cannot reach."""
        self.assertGreaterEqual(hidden.status_code, 400)
        self.assertLess(
            hidden.status_code,
            500,
            "a refusal must be a client error, not a crash",
        )
        self.assertEqual(
            hidden.status_code,
            missing.status_code,
            "hidden content must answer exactly like content that does not exist",
        )

    def assert_same_outcome(self, hidden, missing):
        self.assertLess(hidden.status_code, 500, "a refusal must not be a crash")
        self.assertLess(missing.status_code, 500, "a refusal must not be a crash")
        self.assertEqual(
            hidden.status_code,
            missing.status_code,
            "hidden content must answer exactly like content that does not exist",
        )
