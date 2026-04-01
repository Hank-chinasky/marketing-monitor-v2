from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import CreatorBoardWorkItem


class CreatorBoardWorkItemModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="creatorboard-model-user",
            password="x",
            is_active=True,
        )

    def test_string_representation_returns_title(self):
        workitem = CreatorBoardWorkItem.objects.create(
            title="Review creator handoff",
            assigned_to=self.user,
        )
        self.assertEqual(str(workitem), "Review creator handoff")

    def test_defaults_are_small_and_predictable(self):
        workitem = CreatorBoardWorkItem.objects.create(
            title="Seeded work item",
        )

        self.assertEqual(workitem.status, CreatorBoardWorkItem.Status.NEW)
        self.assertEqual(workitem.priority, CreatorBoardWorkItem.Priority.MEDIUM)
        self.assertEqual(workitem.source_type, CreatorBoardWorkItem.SourceType.MANUAL_INTAKE)
        self.assertEqual(workitem.summary, "")
        self.assertEqual(workitem.next_action, "")