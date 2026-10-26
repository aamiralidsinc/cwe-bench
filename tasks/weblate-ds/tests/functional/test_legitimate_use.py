"""Legitimate use that must keep working, including next to hidden content."""

from __future__ import annotations

from django.urls import reverse

from weblate.checks.models import Check
from weblate.screenshots.models import Screenshot
from weblate.trans.actions import ActionEvents
from weblate.trans.models import Announcement, Change, Comment, Suggestion
from wlbase import MISSING, AccessTestBase


class AccessibleActionsTest(AccessTestBase):
    def test_comment_on_accessible_unit_is_posted(self):
        unit = self.unit_of(self.translation)
        response = self.client.post(
            reverse("comment", kwargs={"pk": unit.pk}),
            {"comment": "Legitimate comment", "scope": "translation"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Comment.objects.filter(comment="Legitimate comment", unit=unit).exists()
        )

    def test_refusals_for_accessible_content_stay_authority_refusals(self):
        unit = self.unit_of(self.translation)
        comment = Comment.objects.create(
            unit=unit, user=self.anotheruser, comment="Visible comment"
        )
        self.assertEqual(
            self.client.post(
                reverse("delete-unit", kwargs={"unit_id": unit.pk})
            ).status_code,
            403,
        )
        self.assertTrue(unit.__class__.objects.filter(pk=unit.pk).exists())
        self.assertEqual(
            self.client.post(
                reverse("delete-comment", kwargs={"pk": comment.pk})
            ).status_code,
            403,
        )
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
        source = unit.source_unit
        self.assertEqual(
            self.client.post(
                reverse("edit_context", kwargs={"pk": source.pk}),
                {"explanation": "Extra context"},
            ).status_code,
            403,
        )
        global_announcement = Announcement.objects.create(message="Global")
        self.assertEqual(
            self.client.post(
                reverse("announcement-delete", kwargs={"pk": global_announcement.pk})
            ).status_code,
            403,
        )
        self.assertTrue(
            Announcement.objects.filter(pk=global_announcement.pk).exists()
        )

    def test_show_change_with_missing_or_visible_other(self):
        visible = Change.objects.create(
            action=ActionEvents.CREATE_PROJECT, project=self.project, user=self.user
        )
        second = Change.objects.create(
            action=ActionEvents.CREATE_PROJECT, project=self.project, user=self.user
        )
        self.assertEqual(
            self.client.get(
                reverse("show_change", kwargs={"pk": visible.pk}),
                {"other": MISSING},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("show_change", kwargs={"pk": visible.pk}),
                {"other": second.pk},
            ).status_code,
            200,
        )

    def test_hidden_translations_answer_like_missing(self):
        _project, _component, translation = self.create_private()
        unit = self.unit_of(translation)
        hidden = self.client.get(
            reverse("js-unit-translations", kwargs={"unit_id": unit.pk})
        )
        missing = self.client.get(
            reverse("js-unit-translations", kwargs={"unit_id": MISSING})
        )
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(missing.status_code, 404)

    def test_machinery_on_accessible_unit(self):
        unit = self.unit_of(self.translation)
        translate = self.client.post(
            reverse("js-translate", kwargs={"service": "weblate", "unit_id": unit.pk})
        )
        memory = self.client.post(
            reverse("js-memory", kwargs={"unit_id": unit.pk}), {"q": "hello"}
        )
        self.assertEqual(translate.status_code, 200)
        self.assertEqual(memory.status_code, 200)
        self.assertIn("responseStatus", translate.json())
        self.assertIn("responseStatus", memory.json())

    def test_broad_access_without_block_still_reaches_private_project(self):
        project, _component, translation = self.create_private()
        unit = self.unit_of(translation)
        self.grant_broad_access()
        response = self.client.post(
            reverse("comment", kwargs={"pk": unit.pk}),
            {"comment": "Broad access", "scope": "translation"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Comment.objects.filter(comment="Broad access", unit=unit).exists()
        )

    def test_hidden_screenshot_for_plain_user_answers_like_missing(self):
        _project, _component, translation = self.create_private()
        screenshot = Screenshot.objects.create(translation=translation, name="shot")
        hidden = self.client.post(
            reverse("screenshot-delete", kwargs={"pk": screenshot.pk})
        )
        missing = self.client.post(
            reverse("screenshot-delete", kwargs={"pk": MISSING})
        )
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(missing.status_code, 404)


class AllowedActionsTest(AccessTestBase):
    def test_screenshot_delete_with_authority(self):
        screenshot = Screenshot.objects.create(
            translation=self.translation, name="shot"
        )
        self.make_manager()
        self.user.clear_cache()
        response = self.client.post(
            reverse("screenshot-delete", kwargs={"pk": screenshot.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Screenshot.objects.filter(pk=screenshot.pk).exists())

    def test_check_summary_for_authorised_user(self):
        unit = self.unit_of(self.translation)
        check = Check.objects.create(unit=unit, name="same")
        response = self.client.get(
            reverse("check-summary", kwargs={"check_id": check.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "same")

    def test_bulk_delete_for_authorised_user(self):
        unit = self.unit_of(self.translation)
        suggestion = Suggestion.objects.create(
            unit=unit, target="visible", user=self.anotheruser
        )
        response = self.client.post(
            reverse("delete-suggestions"), {"suggestions": str(suggestion.pk)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Suggestion.objects.filter(pk=suggestion.pk).exists())

    def test_accept_suggestion_for_authorised_user(self):
        unit = self.unit_of(self.translation)
        suggestion = Suggestion.objects.create(
            unit=unit, target="Accepted target", user=self.anotheruser
        )
        response = self.client.post(
            reverse("accept-suggestion"),
            {"translation": self.translation.pk, "suggestion": suggestion.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Suggestion.objects.filter(pk=suggestion.pk).exists())

    def test_project_announcement_deleted_with_authority(self):
        announcement = Announcement.objects.create(
            project=self.project, message="Project announcement"
        )
        self.make_manager()
        self.user.clear_cache()
        response = self.client.post(
            reverse("announcement-delete", kwargs={"pk": announcement.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Announcement.objects.filter(pk=announcement.pk).exists())
