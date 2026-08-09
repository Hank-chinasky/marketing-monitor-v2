from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


TRIGGER_QUEUE_PREVIEW_ITEMS = [
    {
        "name": "Jessica Demo",
        "platform": "Eurotikken",
        "status": "Urgent",
        "status_class": "urgent",
        "priority": "High",
        "reason": "Low balance + recent activity",
        "last_action": "No action yet today",
        "next_step": "Open conversation and check timing",
        "cooldown": "",
        "buddy": {
            "status": "Attention now",
            "status_class": "urgent",
            "why_now": "Recent activity and a low balance make this a sensitive revenue moment.",
            "latest_context": "Do not reset the context; review the latest thread first.",
            "open_loop": "The customer may disengage if follow-up comes too late.",
            "do_not_do": "Do not send a generic trigger.",
            "next_step": "Open the conversation, check the latest context and continue the existing line carefully.",
            "reliability": "Demo context / human verification.",
        },
    },
    {
        "name": "Warm profile",
        "platform": "Mara chat",
        "status": "Warm",
        "status_class": "warm",
        "priority": "Medium",
        "reason": "Open loop and recent response",
        "last_action": "Brief response yesterday",
        "next_step": "Prepare and follow up later today",
        "cooldown": "",
        "buddy": {
            "status": "Warm active follow-up",
            "status_class": "warm",
            "why_now": "The recent response and established personal context make follow-up appropriate.",
            "latest_context": "The tone is already established; continue in the same style.",
            "open_loop": "A follow-up response is still outstanding.",
            "do_not_do": "Do not reset or reopen generically.",
            "next_step": "Continue from the latest context and guide the conversation forward calmly.",
            "reliability": "Demo context / human verification.",
        },
    },
    {
        "name": "Promising returning customer",
        "platform": "CreatorWorkboard",
        "status": "Promising",
        "status_class": "ready",
        "priority": "Normal",
        "reason": "Previous buyer with a new signal",
        "last_action": "Last contact three days ago",
        "next_step": "Open conversation and review context",
        "cooldown": "",
        "buddy": {
            "status": "Promising",
            "status_class": "ready",
            "why_now": "Purchase history and a new signal make careful follow-up worthwhile.",
            "latest_context": "Review the profile tone and latest agreement first.",
            "open_loop": "Returning interest without current follow-up.",
            "do_not_do": "Do not prioritize revenue blindly without context.",
            "next_step": "Open the conversation and confirm whether the revenue opportunity is still warm.",
            "reliability": "Demo context / human verification.",
        },
    },
    {
        "name": "Data quality example",
        "platform": "Legacy source",
        "status": "Review",
        "status_class": "info",
        "priority": "Review",
        "reason": "Source status or profile data is uncertain",
        "last_action": "No safe trigger action available",
        "next_step": "Verify data before the operator acts",
        "cooldown": "",
        "buddy": {
            "status": "Review first",
            "status_class": "info",
            "why_now": "Uncertain source data may lead to incorrect follow-up.",
            "latest_context": "The legacy signal is not fully reliable.",
            "open_loop": "Data quality must be confirmed first.",
            "do_not_do": "Do not act on uncertain source data.",
            "next_step": "Verify the profile, source and latest context before continuing.",
            "reliability": "Low confidence / human verification.",
        },
    },
    {
        "name": "Cooldown example",
        "platform": "Eurotikken",
        "status": "Cooldown",
        "status_class": "cooldown",
        "priority": "Not now",
        "reason": "Contacted recently",
        "last_action": "Already reviewed today",
        "next_step": "Park and review later",
        "cooldown": "Cooldown active until tomorrow at 10:00",
        "buddy": {
            "status": "Park",
            "status_class": "cooldown",
            "why_now": "Following up too quickly may damage the established relationship.",
            "latest_context": "Already contacted today; allow space first.",
            "open_loop": "Review again later.",
            "do_not_do": "Do not push again during cooldown.",
            "next_step": "Park and review again tomorrow.",
            "reliability": "Demo context / human verification.",
        },
    },
    {
        "name": "VIP buyer",
        "platform": "Mara chat",
        "status": "VIP",
        "status_class": "vip",
        "priority": "Very high",
        "reason": "High value + warm intent",
        "last_action": "Latest order completed recently",
        "next_step": "Open conversation and follow up personally",
        "cooldown": "",
        "buddy": {
            "status": "High value",
            "status_class": "vip",
            "why_now": "High value and warm intent require personal continuity.",
            "latest_context": "Do not treat the customer as a cold lead.",
            "open_loop": "Opportunity for a follow-up conversation or repeat value.",
            "do_not_do": "Do not use standard copy or a mass trigger.",
            "next_step": "Open the conversation and continue personally.",
            "reliability": "Demo context / human verification.",
        },
    },
]


class AdultAdSuiteCockpitView(LoginRequiredMixin, TemplateView):
    template_name = "adultadsuite/cockpit.html"


class AdultAdSuiteTriggerPreviewView(LoginRequiredMixin, TemplateView):
    template_name = "adultadsuite/triggers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trigger_queue"] = TRIGGER_QUEUE_PREVIEW_ITEMS
        return context
