from datetime import timedelta

from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.utils import timezone

from core.creatorboard_views import CreatorBoardDetailView, CreatorBoardQueueView
from core.models import CreatorBoardWorkItem


class CreatorBoardQueueViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.factory = RequestFactory()

        self.admin = user_model.objects.create_user(
            username="creatorboard-admin",
            password="x",
            is_active=True,
            is_staff=True,
        )
        self.operator_a = user_model.objects.create_user(
            username="creatorboard-operator-a",
            password="x",
            is_active=True,
        )
        self.operator_b = user_model.objects.create_user(
            username="creatorboard-operator-b",
            password="x",
            is_active=True,
        )

        self.high_item = CreatorBoardWorkItem.objects.create(
            title="High priority item",
            assigned_to=self.operator_a,
            priority=CreatorBoardWorkItem.Priority.HIGH,
            status=CreatorBoardWorkItem.Status.NEW,
            source_type=CreatorBoardWorkItem.SourceType.MANUAL_INTAKE,
            summary="High summary",
            next_action="Handle immediately",
        )
        self.medium_item = CreatorBoardWorkItem.objects.create(
            title="Medium priority item",
            assigned_to=self.operator_a,
            priority=CreatorBoardWorkItem.Priority.MEDIUM,
            status=CreatorBoardWorkItem.Status.IN_PROGRESS,
            source_type=CreatorBoardWorkItem.SourceType.CREATOR,
            summary="Medium summary",
            next_action="Check context",
        )
        self.low_item = CreatorBoardWorkItem.objects.create(
            title="Low priority item",
            assigned_to=self.operator_a,
            priority=CreatorBoardWorkItem.Priority.LOW,
            status=CreatorBoardWorkItem.Status.BLOCKED,
            source_type=CreatorBoardWorkItem.SourceType.CHANNEL,
            summary="Low summary",
            next_action="Wait for unblock",
        )
        self.other_user_item = CreatorBoardWorkItem.objects.create(
            title="Other user item",
            assigned_to=self.operator_b,
            priority=CreatorBoardWorkItem.Priority.HIGH,
            status=CreatorBoardWorkItem.Status.NEW,
        )

        now = timezone.now()
        CreatorBoardWorkItem.objects.filter(pk=self.high_item.pk).update(updated_at=now - timedelta(hours=3))
        CreatorBoardWorkItem.objects.filter(pk=self.medium_item.pk).update(updated_at=now - timedelta(hours=2))
        CreatorBoardWorkItem.objects.filter(pk=self.low_item.pk).update(updated_at=now - timedelta(hours=1))
        CreatorBoardWorkItem.objects.filter(pk=self.other_user_item.pk).update(updated_at=now - timedelta(minutes=30))

        self.high_item.refresh_from_db()
        self.medium_item.refresh_from_db()
        self.low_item.refresh_from_db()
        self.other_user_item.refresh_from_db()

    def _render_queue(self, user, path="/creatorboard/work/"):
        request = self.factory.get(path)
        request.user = user
        response = CreatorBoardQueueView.as_view()(request)
        response.render()
        return response

    def _render_detail(self, user, workitem_id):
        request = self.factory.get(f"/creatorboard/work/{workitem_id}/")
        request.user = user
        response = CreatorBoardDetailView.as_view()(request, pk=workitem_id)
        response.render()
        return response

    def test_admin_queue_sees_all_items(self):
        response = self._render_queue(self.admin)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "High priority item")
        self.assertContains(response, "Other user item")

    def test_operator_queue_sees_only_assigned_items(self):
        response = self._render_queue(self.operator_a)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "High priority item")
        self.assertNotContains(response, "Other user item")

    def test_queue_orders_by_priority_then_updated_at(self):
        response = self._render_queue(self.operator_a)
        items = list(response.context_data["workitems"])

        self.assertEqual(
            [item.title for item in items],
            [
                "High priority item",
                "Medium priority item",
                "Low priority item",
            ],
        )

    def test_detail_renders_for_allowed_user(self):
        response = self._render_detail(self.operator_a, self.high_item.pk)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "High priority item")
        self.assertContains(response, "Handle immediately")

    def test_detail_blocks_other_operator(self):
        request = self.factory.get(f"/creatorboard/work/{self.other_user_item.pk}/")
        request.user = self.operator_a

        with self.assertRaises(Http404):
            CreatorBoardDetailView.as_view()(request, pk=self.other_user_item.pk)

    def test_queue_is_paginated_to_fifty(self):
        for index in range(60):
            CreatorBoardWorkItem.objects.create(
                title=f"Paginated work item {index}",
                assigned_to=self.operator_a,
                priority=CreatorBoardWorkItem.Priority.MEDIUM,
                status=CreatorBoardWorkItem.Status.NEW,
            )

        response = self._render_queue(self.operator_a)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context_data["is_paginated"])
        self.assertEqual(response.context_data["paginator"].per_page, 50)
        self.assertEqual(len(response.context_data["workitems"]), 50)