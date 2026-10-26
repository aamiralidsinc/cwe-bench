"""Requests that name content in a project the caller cannot reach."""

from __future__ import annotations

from django.urls import reverse

from weblate.checks.models import Check
from weblate.screenshots.models import Screenshot
from weblate.trans.actions import ActionEvents
from weblate.trans.models import Announcement, Change, Comment
from wlbase import MISSING, AccessTestBase


class ShowChangeTest(AccessTestBase):
    def hidden_change(self):
        project, component, _translation = self.create_private()
        return Change.objects.create(
            action=ActionEvents.LOCK,
            project=project,
            component=component,
            user=self.anotheruser,
        )

    def test_hidden_change_is_not_found(self):
        change = self.hidden_change()
        hidden = self.client.get(reverse("show_change", kwargs={"pk": change.pk}))
        missing = self.client.get(reverse("show_change", kwargs={"pk": MISSING}))
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertTrue(Change.objects.filter(pk=change.pk).exists())

    def test_hidden_change_for_blocked_broad_user(self):
        change = self.hidden_change()
        self.grant_broad_access_and_block(change.project)
        hidden = self.client.get(reverse("show_change", kwargs={"pk": change.pk}))
        missing = self.client.get(reverse("show_change", kwargs={"pk": MISSING}))
        self.assert_hidden_is_indistinguishable(hidden, missing)

    def test_hidden_other_entry_is_ignored(self):
        visible = Change.objects.create(
            action=ActionEvents.CREATE_PROJECT, project=self.project, user=self.user
        )
        hidden = self.hidden_change()
        hidden_response = self.client.get(
            reverse("show_change", kwargs={"pk": visible.pk}), {"other": hidden.pk}
        )
        missing_response = self.client.get(
            reverse("show_change", kwargs={"pk": visible.pk}), {"other": MISSING}
        )
        self.assert_same_outcome(hidden_response, missing_response)

    def test_hidden_other_entry_for_blocked_broad_user(self):
        visible = Change.objects.create(
            action=ActionEvents.CREATE_PROJECT, project=self.project, user=self.user
        )
        hidden = self.hidden_change()
        self.grant_broad_access_and_block(hidden.project)
        hidden_response = self.client.get(
            reverse("show_change", kwargs={"pk": visible.pk}), {"other": hidden.pk}
        )
        missing_response = self.client.get(
            reverse("show_change", kwargs={"pk": visible.pk}), {"other": MISSING}
        )
        self.assert_same_outcome(hidden_response, missing_response)


class CommentTest(AccessTestBase):
    def test_comment_on_hidden_unit(self):
        _project, _component, translation = self.create_private()
        unit = self.unit_of(translation)
        hidden = self.client.post(
            reverse("comment", kwargs={"pk": unit.pk}),
            {"comment": "Probe comment", "scope": "translation"},
        )
        missing = self.client.post(
            reverse("comment", kwargs={"pk": MISSING}),
            {"comment": "Probe comment", "scope": "translation"},
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertFalse(Comment.objects.filter(comment="Probe comment").exists())

    def test_comment_on_hidden_unit_for_blocked_broad_user(self):
        project, _component, translation = self.create_private()
        unit = self.unit_of(translation)
        self.grant_broad_access_and_block(project)
        hidden = self.client.post(
            reverse("comment", kwargs={"pk": unit.pk}),
            {"comment": "Probe comment", "scope": "translation"},
        )
        missing = self.client.post(
            reverse("comment", kwargs={"pk": MISSING}),
            {"comment": "Probe comment", "scope": "translation"},
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertFalse(Comment.objects.filter(comment="Probe comment").exists())

    def test_delete_hidden_comment(self):
        _project, _component, translation = self.create_private()
        comment = Comment.objects.create(
            unit=self.unit_of(translation), user=self.anotheruser, comment="Hidden"
        )
        hidden = self.client.post(
            reverse("delete-comment", kwargs={"pk": comment.pk})
        )
        missing = self.client.post(
            reverse("delete-comment", kwargs={"pk": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_resolve_hidden_comment(self):
        _project, _component, translation = self.create_private()
        comment = Comment.objects.create(
            unit=self.unit_of(translation), user=self.anotheruser, comment="Hidden"
        )
        hidden = self.client.post(
            reverse("resolve-comment", kwargs={"pk": comment.pk})
        )
        missing = self.client.post(
            reverse("resolve-comment", kwargs={"pk": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertFalse(Comment.objects.get(pk=comment.pk).resolved)


class UnitActionTest(AccessTestBase):
    def test_delete_hidden_unit(self):
        _project, _component, translation = self.create_private()
        unit = self.unit_of(translation)
        hidden = self.client.post(
            reverse("delete-unit", kwargs={"unit_id": unit.pk})
        )
        missing = self.client.post(
            reverse("delete-unit", kwargs={"unit_id": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertTrue(type(unit).objects.filter(pk=unit.pk).exists())

    def test_delete_hidden_unit_for_blocked_broad_user(self):
        project, _component, translation = self.create_private()
        unit = self.unit_of(translation)
        self.grant_broad_access_and_block(project)
        hidden = self.client.post(
            reverse("delete-unit", kwargs={"unit_id": unit.pk})
        )
        missing = self.client.post(
            reverse("delete-unit", kwargs={"unit_id": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertTrue(type(unit).objects.filter(pk=unit.pk).exists())

    def test_ignore_hidden_check(self):
        _project, _component, translation = self.create_private()
        check = Check.objects.create(unit=self.unit_of(translation), name="same")
        hidden = self.client.post(
            reverse("js-ignore-check", kwargs={"check_id": check.pk})
        )
        missing = self.client.post(
            reverse("js-ignore-check", kwargs={"check_id": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertFalse(Check.objects.get(pk=check.pk).dismissed)

    def test_ignore_hidden_check_for_blocked_broad_user(self):
        project, _component, translation = self.create_private()
        check = Check.objects.create(unit=self.unit_of(translation), name="same")
        self.grant_broad_access_and_block(project)
        hidden = self.client.post(
            reverse("js-ignore-check", kwargs={"check_id": check.pk})
        )
        missing = self.client.post(
            reverse("js-ignore-check", kwargs={"check_id": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertFalse(Check.objects.get(pk=check.pk).dismissed)

    def test_ignore_hidden_check_source(self):
        _project, _component, translation = self.create_private()
        unit = self.unit_of(translation)
        source = unit.source_unit
        before = source.extra_flags
        check = Check.objects.create(unit=unit, name="same")
        hidden = self.client.post(
            reverse("js-ignore-check-source", kwargs={"check_id": check.pk})
        )
        missing = self.client.post(
            reverse("js-ignore-check-source", kwargs={"check_id": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        source.refresh_from_db()
        self.assertEqual(source.extra_flags, before)

    def test_dismiss_hidden_automatic_translation(self):
        _project, _component, translation = self.create_private()
        unit = self.unit_of(translation)
        hidden = self.client.post(
            reverse("js-dismiss-automatically-translated", kwargs={"unit_id": unit.pk})
        )
        missing = self.client.post(
            reverse("js-dismiss-automatically-translated", kwargs={"unit_id": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        unit.refresh_from_db()
        self.assertFalse(unit.automatically_translated)


class AnnouncementTest(AccessTestBase):
    def hidden_announcement(self):
        project, component, _translation = self.create_private()
        return Announcement.objects.create(
            project=project, component=component, message="Hidden announcement"
        )

    def test_delete_hidden_announcement(self):
        announcement = self.hidden_announcement()
        hidden = self.client.post(
            reverse("announcement-delete", kwargs={"pk": announcement.pk})
        )
        missing = self.client.post(
            reverse("announcement-delete", kwargs={"pk": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertTrue(Announcement.objects.filter(pk=announcement.pk).exists())

    def test_delete_hidden_announcement_for_blocked_broad_user(self):
        announcement = self.hidden_announcement()
        self.grant_broad_access_and_block(announcement.project)
        hidden = self.client.post(
            reverse("announcement-delete", kwargs={"pk": announcement.pk})
        )
        missing = self.client.post(
            reverse("announcement-delete", kwargs={"pk": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertTrue(Announcement.objects.filter(pk=announcement.pk).exists())


class EditContextTest(AccessTestBase):
    def test_edit_hidden_context(self):
        _project, _component, translation = self.create_private()
        unit = self.unit_of(translation).source_unit
        before_context = unit.context
        before_explanation = unit.explanation
        hidden = self.client.post(
            reverse("edit_context", kwargs={"pk": unit.pk}),
            {"explanation": "Extra context"},
        )
        missing = self.client.post(
            reverse("edit_context", kwargs={"pk": MISSING}),
            {"explanation": "Extra context"},
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        unit.refresh_from_db()
        self.assertEqual(unit.context, before_context)
        self.assertEqual(unit.explanation, before_explanation)


class ScreenshotTest(AccessTestBase):
    def test_delete_hidden_screenshot_for_blocked_broad_user(self):
        project, _component, translation = self.create_private()
        screenshot = Screenshot.objects.create(translation=translation, name="shot")
        self.grant_broad_access_and_block(project)
        hidden = self.client.post(
            reverse("screenshot-delete", kwargs={"pk": screenshot.pk})
        )
        missing = self.client.post(
            reverse("screenshot-delete", kwargs={"pk": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertTrue(Screenshot.objects.filter(pk=screenshot.pk).exists())

    def test_remove_hidden_screenshot_source_for_blocked_broad_user(self):
        project, _component, translation = self.create_private()
        screenshot = Screenshot.objects.create(translation=translation, name="shot")
        unit = self.unit_of(translation)
        self.grant_broad_access_and_block(project)
        hidden = self.client.post(
            reverse("screenshot-remove-source", kwargs={"pk": screenshot.pk}),
            {"source": unit.pk},
        )
        missing = self.client.post(
            reverse("screenshot-remove-source", kwargs={"pk": MISSING}),
            {"source": unit.pk},
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)
        self.assertTrue(Screenshot.objects.filter(pk=screenshot.pk).exists())
