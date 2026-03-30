from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View

from core.forms import ChannelOperationalStateForm
from core.services.operational_state import get_or_create_channel_operational_state
from core.services.scope import get_channel_queryset_for_user


class ChannelOperationalStateUpdateView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk, *args, **kwargs):
        channel = get_object_or_404(
            get_channel_queryset_for_user(request.user).select_related(
                "creator",
                "creator__primary_operator",
                "creator__primary_operator__user",
            ),
            pk=pk,
        )
        state = get_or_create_channel_operational_state(channel)
        form = ChannelOperationalStateForm(request.POST, instance=state)

        if form.is_valid():
            operational_state = form.save(commit=False)
            operational_state.updated_by = request.user
            operational_state.save()
            messages.success(request, "Handoff opgeslagen.")
        else:
            messages.error(request, "Handoff kon niet worden opgeslagen. Controleer de velden.")

        next_url = (request.POST.get("next") or "").strip()
        if not next_url:
            next_url = reverse("channel-detail", kwargs={"pk": channel.pk}) + "#operational-handoff"

        return HttpResponseRedirect(next_url)