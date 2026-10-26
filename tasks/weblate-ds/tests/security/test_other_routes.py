"""Other ways a request can name content the caller cannot reach."""

from __future__ import annotations

from django.urls import reverse

from weblate.checks.models import Check
from weblate.trans.models import Suggestion
from wlbase import MISSING, AccessTestBase


class MachineryTest(AccessTestBase):
    def _compare(self, name, payload, extra=None):
        extra = extra or {}
        hidden = self.client.post(
            reverse(name, kwargs={**extra, "unit_id": self.hidden_unit.pk}), payload
        )
        missing = self.client.post(
            reverse(name, kwargs={**extra, "unit_id": MISSING}), payload
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)

    def test_translate_hidden_unit(self):
        _project, _component, translation = self.create_private()
        self.hidden_unit = self.unit_of(translation)
        self._compare("js-translate", {"service": "weblate"}, {"service": "weblate"})

    def test_memory_hidden_unit(self):
        _project, _component, translation = self.create_private()
        self.hidden_unit = self.unit_of(translation)
        self._compare("js-memory", {"q": "hello"})

    def test_translate_hidden_unit_for_blocked_broad_user(self):
        project, _component, translation = self.create_private()
        self.hidden_unit = self.unit_of(translation)
        self.grant_broad_access_and_block(project)
        self._compare("js-translate", {"service": "weblate"}, {"service": "weblate"})


class InjectedRouteTest(AccessTestBase):
    def test_check_summary_hidden_restricted_component(self):
        self.component.restricted = True
        self.component.save(update_fields=["restricted"])
        unit = self.unit_of(translation=self.translation)
        check = Check.objects.create(unit=unit, name="same")
        hidden = self.client.get(
            reverse("check-summary", kwargs={"check_id": check.pk})
        )
        missing = self.client.get(
            reverse("check-summary", kwargs={"check_id": MISSING})
        )
        self.assert_hidden_is_indistinguishable(hidden, missing)

    def test_bulk_delete_with_one_hidden_suggestion(self):
        _project, _component, private_translation = self.create_private()
        hidden = Suggestion.objects.create(
            unit=self.unit_of(private_translation),
            target="hidden",
            user=self.anotheruser,
        )
        second = self.create_po(project=self.project, name="second")
        visible_unit = self.unit_of(
            second.translation_set.get(language__code="cs")
        )
        visible = Suggestion.objects.create(
            unit=visible_unit, target="visible", user=self.anotheruser
        )
        hidden_response = self.client.post(
            reverse("delete-suggestions"),
            {"suggestions": f"{visible.pk},{hidden.pk}"},
        )
        missing_response = self.client.post(
            reverse("delete-suggestions"),
            {"suggestions": f"{visible.pk},{MISSING}"},
        )
        self.assert_same_outcome(hidden_response, missing_response)
        self.assertTrue(Suggestion.objects.filter(pk=hidden.pk).exists())

    def test_accept_suggestion_from_another_translation(self):
        _project, _component, private_translation = self.create_private()
        hidden = Suggestion.objects.create(
            unit=self.unit_of(private_translation),
            target="hidden",
            user=self.anotheruser,
        )
        hidden_response = self.client.post(
            reverse("accept-suggestion"),
            {"translation": self.translation.pk, "suggestion": hidden.pk},
        )
        missing_response = self.client.post(
            reverse("accept-suggestion"),
            {"translation": self.translation.pk, "suggestion": MISSING},
        )
        self.assert_same_outcome(hidden_response, missing_response)
        self.assertTrue(Suggestion.objects.filter(pk=hidden.pk).exists())
