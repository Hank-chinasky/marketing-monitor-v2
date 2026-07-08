from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class AdultAdSuiteCockpitView(LoginRequiredMixin, TemplateView):
    template_name = "adultadsuite/cockpit.html"
