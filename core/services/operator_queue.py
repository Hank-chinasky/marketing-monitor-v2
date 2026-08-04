from __future__ import annotations

from django.utils import timezone

from core.models import ConversationThread, ThreadFollowUpStatus
from core.services.source_identity import (
    canonical_source_key,
    canonical_source_label,
)


GROUP_NOW = "now"
GROUP_REVIEW = "review"
GROUP_LATER = "later"
GROUP_WAITING = "waiting"

GROUP_ORDER = {
    GROUP_NOW: 0,
    GROUP_REVIEW: 1,
    GROUP_LATER: 2,
    GROUP_WAITING: 3,
}

GROUP_LABELS = {
    GROUP_NOW: "Nu afhandelen",
    GROUP_REVIEW: "Review nodig",
    GROUP_LATER: "Later opvolgen",
    GROUP_WAITING: "Wacht op klant",
}

GROUP_BADGES = {
    GROUP_NOW: "badge-red",
    GROUP_REVIEW: "badge-yellow",
    GROUP_LATER: "badge-blue",
    GROUP_WAITING: "badge-green",
}


def _get_follow_up(thread):
    try:
        return thread.follow_up_status
    except ThreadFollowUpStatus.DoesNotExist:
        return None


def _waiting_seconds(thread, now):
    if not thread.last_message_at:
        return 0

    return max(
        0,
        int((now - thread.last_message_at).total_seconds()),
    )


def _format_waiting_time(seconds):
    if seconds < 60:
        return "minder dan 1 minuut"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours < 24:
        if remaining_minutes:
            return f"{hours}u {remaining_minutes}m"
        return f"{hours} uur"

    days = hours // 24
    remaining_hours = hours % 24

    if remaining_hours:
        return f"{days}d {remaining_hours}u"
    return f"{days} dagen"


def _missing_context(thread):
    missing = []

    if not thread.channel:
        missing.append("bronaccount")
    if not (thread.guardrails or "").strip():
        missing.append("guardrails")
    if not (thread.open_loop or "").strip():
        missing.append("volgende stap")
    if not (thread.last_handoff_note or "").strip():
        missing.append("handoff")

    return missing


def _build_revenue_signal(thread, follow_up):
    stage = thread.creator.customer_stage
    follow_up_value = follow_up.status if follow_up else ""

    if (
        stage == thread.creator.CustomerStage.INSIDE_PAYWALL
        and follow_up_value == ThreadFollowUpStatus.Status.WARM
    ):
        return "Warm omzetmoment"

    if stage == thread.creator.CustomerStage.FORMER_CUSTOMER:
        return "Heractivatiekans"

    if stage in {
        thread.creator.CustomerStage.LEAD,
        thread.creator.CustomerStage.OUTSIDE_PAYWALL,
    }:
        return "Conversiekans"

    if follow_up_value == ThreadFollowUpStatus.Status.OPEN_LOOP:
        return "Open follow-upkans"

    return "Geen expliciet revenuesignaal"


def _classify_thread(thread, follow_up, waiting_seconds):
    follow_up_value = follow_up.status if follow_up else ""
    missing = _missing_context(thread)
    has_risk = bool((thread.risk_flags or "").strip())

    if thread.status == ConversationThread.Status.WAITING_ON_CUSTOMER:
        return {
            "group": GROUP_WAITING,
            "priority_rank": 50,
            "priority_label": "Parkeren",
            "why_now": "De klant is aan zet; voorkom onnodig opnieuw benaderen.",
        }

    if follow_up_value in {
        ThreadFollowUpStatus.Status.LATER_TRIGGEREN,
        ThreadFollowUpStatus.Status.AFGEKOELD,
    }:
        return {
            "group": GROUP_LATER,
            "priority_rank": 40,
            "priority_label": "Later",
            "why_now": (
                "Deze thread is bewust geparkeerd voor een later opvolgmoment."
            ),
        }

    if (
        follow_up_value == ThreadFollowUpStatus.Status.REVIEW_NODIG
        or has_risk
        or missing
    ):
        reasons = []

        if has_risk:
            reasons.append("risicosignaal")
        if follow_up_value == ThreadFollowUpStatus.Status.REVIEW_NODIG:
            reasons.append("reviewstatus")
        if missing:
            reasons.append(f"ontbreekt: {', '.join(missing)}")

        return {
            "group": GROUP_REVIEW,
            "priority_rank": 10,
            "priority_label": "Review",
            "why_now": (
                "Eerst controleren voordat de operator veilig verdergaat "
                f"({'; '.join(reasons)})."
            ),
        }

    if thread.status == ConversationThread.Status.HANDOFF_REQUIRED:
        return {
            "group": GROUP_NOW,
            "priority_rank": 0,
            "priority_label": "P1",
            "why_now": (
                "Een handoff is vereist voordat de conversatie verder kan."
            ),
        }

    if (
        thread.status == ConversationThread.Status.WAITING_ON_OPERATOR
        and follow_up_value
        in {
            ThreadFollowUpStatus.Status.WARM,
            ThreadFollowUpStatus.Status.OPEN_LOOP,
        }
    ):
        return {
            "group": GROUP_NOW,
            "priority_rank": 1,
            "priority_label": "P1",
            "why_now": (
                "De klant wacht en de warme of open lijn vraagt continuïteit."
            ),
        }

    if thread.status == ConversationThread.Status.WAITING_ON_OPERATOR:
        if waiting_seconds >= 30 * 60:
            reason = (
                "De klant wacht langer dan 30 minuten; "
                "de reactiedrempel is overschreden."
            )
        else:
            reason = "De klant wacht op een operatorreactie."

        return {
            "group": GROUP_NOW,
            "priority_rank": 20,
            "priority_label": "P2",
            "why_now": reason,
        }

    if thread.status == ConversationThread.Status.ACTIVE:
        return {
            "group": GROUP_NOW,
            "priority_rank": 25,
            "priority_label": "P2",
            "why_now": "De conversatie is actief en vraagt operatorbewaking.",
        }

    return {
        "group": GROUP_LATER,
        "priority_rank": 45,
        "priority_label": "Later",
        "why_now": "Geen directe operatoractie nodig.",
    }


def _build_next_action(thread, group):
    open_loop = (thread.open_loop or "").strip()
    if open_loop:
        return open_loop

    if group == GROUP_REVIEW:
        return "Controleer bron, context en guardrails voordat je antwoordt."

    if group == GROUP_WAITING:
        return "Wacht op een nieuw klantsignaal."

    if group == GROUP_LATER:
        return "Plan een handmatig opvolgmoment."

    return "Open de thread en bepaal de eerstvolgende veilige actie."


def build_operator_queue(threads, *, now=None):
    now = now or timezone.now()
    items = []

    for thread in threads:
        if not thread.active:
            continue
        if thread.status == ConversationThread.Status.CLOSED:
            continue

        follow_up = _get_follow_up(thread)
        waiting_seconds = _waiting_seconds(thread, now)
        classification = _classify_thread(
            thread,
            follow_up,
            waiting_seconds,
        )
        group = classification["group"]

        source_label = (
            (thread.source_site_label or "").strip()
            or canonical_source_label(
                thread.source_system
            )
        )
        source_account = (
            thread.channel.handle
            if thread.channel
            else (thread.source_site_id or "").strip() or "Niet gekoppeld"
        )

        reliability = "Hoog"
        if group == GROUP_REVIEW:
            reliability = "Laag"
        elif not (thread.last_approved_reply_style or "").strip():
            reliability = "Middel"

        item = {
            "thread": thread,
            "follow_up": follow_up,
            "group": group,
            "group_label": GROUP_LABELS[group],
            "group_badge": GROUP_BADGES[group],
            "priority_rank": classification["priority_rank"],
            "priority_label": classification["priority_label"],
            "why_now": classification["why_now"],
            "waiting_seconds": waiting_seconds,
            "waiting_label": _format_waiting_time(waiting_seconds),
            "source_label": source_label,
            "source_account": source_account,
            "revenue_signal": _build_revenue_signal(
                thread,
                follow_up,
            ),
            "next_action": _build_next_action(thread, group),
            "reliability": reliability,
        }
        items.append(item)

    items.sort(
        key=lambda item: (
            GROUP_ORDER[item["group"]],
            item["priority_rank"],
            -item["waiting_seconds"],
            item["thread"].pk,
        )
    )

    active_items = [
        item
        for item in items
        if item["group"] in {GROUP_NOW, GROUP_REVIEW}
    ]
    parked_items = [
        item
        for item in items
        if item["group"] in {GROUP_LATER, GROUP_WAITING}
    ]

    source_count = len(
        {
            canonical_source_key(
                item["thread"].source_system
            )
            for item in items
        }
    )

    return {
        "items": items,
        "active_items": active_items,
        "parked_items": parked_items,
        "next_item": active_items[0] if active_items else None,
        "counts": {
            "now": sum(
                item["group"] == GROUP_NOW
                for item in items
            ),
            "review": sum(
                item["group"] == GROUP_REVIEW
                for item in items
            ),
            "later": sum(
                item["group"] == GROUP_LATER
                for item in items
            ),
            "waiting": sum(
                item["group"] == GROUP_WAITING
                for item in items
            ),
            "total": len(items),
            "sources": source_count,
        },
    }
