from django.test import SimpleTestCase

from core.models import ConversationThread
from core.services.conversation_profile import (
    WorkflowProfile,
    get_mara_workflow_profile,
    resolve_workflow_profile,
)


class WorkflowProfileTests(SimpleTestCase):
    def test_mara_workflow_profile_exists_with_required_defaults(self):
        profile = get_mara_workflow_profile()

        self.assertIsInstance(profile, WorkflowProfile)
        self.assertEqual(profile.name, "Mara")
        self.assertTrue(profile.workflow_only)
        self.assertFalse(profile.hosts_user_media)
        self.assertFalse(profile.customer_facing_ai)
        self.assertTrue(profile.human_approval_required)
        self.assertTrue(profile.stores_personal_context)
        self.assertFalse(profile.stores_special_category_context)

    def test_resolve_workflow_profile_supports_mara_chat(self):
        profile = resolve_workflow_profile(
            ConversationThread.SourceSystem.MARA_CHAT
        )

        self.assertEqual(profile, get_mara_workflow_profile())

    def test_unknown_source_system_fails_closed(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported conversation workflow profile source_system: unknown_chat",
        ):
            resolve_workflow_profile("unknown_chat")