from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


TRIGGER_QUEUE_PREVIEW_ITEMS = [
    {
        "name": "Jessica Demo",
        "platform": "Eurotikken",
        "status": "Urgent",
        "status_class": "urgent",
        "priority": "Hoog",
        "reason": "Laag tegoed + recente activiteit",
        "last_action": "Nog geen actie vandaag",
        "next_step": "Gesprek openen en timing checken",
        "cooldown": "",
    },
    {
        "name": "Warm profiel",
        "platform": "Mara chat",
        "status": "Warm",
        "status_class": "warm",
        "priority": "Middel",
        "reason": "Open loop en recente respons",
        "last_action": "Gisteren kort gereageerd",
        "next_step": "Voorbereiden en later vandaag opvolgen",
        "cooldown": "",
    },
    {
        "name": "Kansrijke terugkeerder",
        "platform": "CreatorWorkboard",
        "status": "Kansrijk",
        "status_class": "ready",
        "priority": "Normaal",
        "reason": "Eerdere koper met nieuw signaal",
        "last_action": "Laatste contact drie dagen geleden",
        "next_step": "Gesprek openen en context controleren",
        "cooldown": "",
    },
    {
        "name": "Datakwaliteit voorbeeld",
        "platform": "Legacy bron",
        "status": "Controleren",
        "status_class": "info",
        "priority": "Review",
        "reason": "Bronstatus of profieldata is onzeker",
        "last_action": "Geen veilige triggeractie beschikbaar",
        "next_step": "Data controleren voordat operator actie neemt",
        "cooldown": "",
    },
    {
        "name": "Cooldown voorbeeld",
        "platform": "Eurotikken",
        "status": "Cooldown",
        "status_class": "cooldown",
        "priority": "Niet nu",
        "reason": "Recent al benaderd",
        "last_action": "Vandaag al gezien",
        "next_step": "Parkeren en later opnieuw beoordelen",
        "cooldown": "Cooldown actief tot morgen 10:00",
    },
    {
        "name": "VIP koper",
        "platform": "Mara chat",
        "status": "VIP",
        "status_class": "vip",
        "priority": "Zeer hoog",
        "reason": "Hoge waarde + warme intentie",
        "last_action": "Laatste bestelling recent afgerond",
        "next_step": "Gesprek openen en persoonlijk opvolgen",
        "cooldown": "",
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
