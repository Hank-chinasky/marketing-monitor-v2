from core.models import ChannelOperationalState


def get_or_create_channel_operational_state(channel):
    legacy_update = (channel.last_operator_update or "").strip()

    default_owner = None
    if channel.creator.primary_operator_id and hasattr(channel.creator.primary_operator, "user"):
        default_owner = channel.creator.primary_operator.user

    state, _ = ChannelOperationalState.objects.get_or_create(
        channel=channel,
        defaults={
            "owner": default_owner,
            "status": (
                ChannelOperationalState.Status.ACTIVE
                if legacy_update
                else ChannelOperationalState.Status.NEW
            ),
            "priority": ChannelOperationalState.Priority.NORMAL,
            "last_update": legacy_update,
        },
    )
    return state