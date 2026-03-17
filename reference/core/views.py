from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from core.mixins import AdminOnlyMixin
from core.models import Creator
from core.forms import CreatorForm


class CreatorUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Creator
    form_class = CreatorForm
    template_name = "creators/creator_form.html"

    def get_success_url(self):
        return reverse_lazy("creator-detail", kwargs={"pk": self.object.pk})
