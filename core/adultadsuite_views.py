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
        "buddy": {
            "status": "Nu aandacht",
            "status_class": "urgent",
            "why_now": "Recente activiteit en laag tegoed maken dit een kwetsbaar omzetmoment.",
            "latest_context": "Context niet resetten; eerst laatste threadlijn controleren.",
            "open_loop": "Klant kan afhaken als timing te laat komt.",
            "do_not_do": "Geen generieke trigger sturen.",
            "next_step": "Open gesprek, check laatste context en pak gecontroleerd de lijn op.",
            "reliability": "Demo-context / menselijk checken.",
        },
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
        "buddy": {
            "status": "Warme lopende follow-up",
            "status_class": "warm",
            "why_now": "Recente respons en bestaande persoonlijke lijn maken opvolging logisch.",
            "latest_context": "Toon is al opgebouwd; blijf in dezelfde lijn.",
            "open_loop": "Er ligt nog een vervolgreactie open.",
            "do_not_do": "Niet resetten en niet generiek openen.",
            "next_step": "Pak laatste context op en stuur rustig richting vervolg.",
            "reliability": "Demo-context / menselijk checken.",
        },
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
        "buddy": {
            "status": "Kansrijk",
            "status_class": "ready",
            "why_now": "Eerdere koophistorie en nieuw signaal maken gecontroleerde opvolging zinvol.",
            "latest_context": "Eerst profieltoon en laatste afspraak nalopen.",
            "open_loop": "Terugkeerinteresse zonder actuele opvolging.",
            "do_not_do": "Niet blind op geld prioriteren zonder context.",
            "next_step": "Open gesprek en bevestig of het omzetmoment nog warm is.",
            "reliability": "Demo-context / menselijk checken.",
        },
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
        "buddy": {
            "status": "Eerst controleren",
            "status_class": "info",
            "why_now": "Onzekere brondata kan leiden tot verkeerde opvolging.",
            "latest_context": "Legacy-signaal is niet volledig betrouwbaar.",
            "open_loop": "Datakwaliteit moet eerst bevestigd worden.",
            "do_not_do": "Geen actie baseren op onzekere brondata.",
            "next_step": "Controleer profiel, bron en laatste context voordat je verdergaat.",
            "reliability": "Lage zekerheid / menselijk checken.",
        },
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
        "buddy": {
            "status": "Parkeren",
            "status_class": "cooldown",
            "why_now": "Te snel opnieuw opvolgen kan de opgebouwde lijn beschadigen.",
            "latest_context": "Vandaag al benaderd; eerst rust bewaren.",
            "open_loop": "Later opnieuw beoordelen.",
            "do_not_do": "Niet opnieuw pushen binnen cooldown.",
            "next_step": "Parkeren en morgen opnieuw controleren.",
            "reliability": "Demo-context / menselijk checken.",
        },
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
        "buddy": {
            "status": "Hoge waarde",
            "status_class": "vip",
            "why_now": "Hoge waarde en warme intentie vragen persoonlijke continuïteit.",
            "latest_context": "Klant niet behandelen als koude lead.",
            "open_loop": "Kans op vervolggesprek of herhaalwaarde.",
            "do_not_do": "Geen standaardtekst of massale trigger gebruiken.",
            "next_step": "Open gesprek en vervolg op persoonlijke lijn.",
            "reliability": "Demo-context / menselijk checken.",
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
