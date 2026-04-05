from dataclasses import dataclass

from core.models import ConversationThread


@dataclass(frozen=True)
class WorkflowProfile:
    name: str
    workflow_only: bool
    hosts_user_media: bool
    customer_facing_ai: bool
    human_approval_required: bool
    stores_personal_context: bool
    stores_special_category_context: bool


MARA_WORKFLOW_PROFILE = WorkflowProfile(
    name="Mara",
    workflow_only=True,
    hosts_user_media=False,
    customer_facing_ai=False,
    human_approval_required=True,
    stores_personal_context=True,
    stores_special_category_context=False,
)


def get_mara_workflow_profile() -> WorkflowProfile:
    return MARA_WORKFLOW_PROFILE


def resolve_workflow_profile(source_system: str) -> WorkflowProfile:
    if source_system == ConversationThread.SourceSystem.MARA_CHAT:
        return get_mara_workflow_profile()

    raise ValueError(
        f"Unsupported conversation workflow profile source_system: {source_system}"
    )