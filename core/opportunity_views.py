from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, IntegerField, Value, When
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from core.forms import OutcomeEntryForm, ProfileOpportunityForm
from core.models import ProfileOpportunity
from core.services.scope import is_admin_user


def append_query_parameter(url, key, value):
    parts = urlsplit(url)
    query_items = dict(parse_qsl(parts.query, keep_blank_values=True))
    query_items[key] = value
    new_query = urlencode(query_items)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def get_profile_opportunity_queryset_for_user(user):
    base_qs = ProfileOpportunity.objects.select_related("assigned_to")
    if is_admin_user(user):
        return base_qs
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return base_qs.none()
    return base_qs.filter(assigned_to=user)


class OpportunityScopedMixin:
    def get_queryset(self):
        return get_profile_opportunity_queryset_for_user(self.request.user)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def render_detail(self, *, opportunity, form, outcome_form, status=200):
        context = {
            "opportunity": opportunity,
            "form": form,
            "outcome_form": outcome_form,
            "saved": self.request.GET.get("saved") == "1",
            "outcome_added": self.request.GET.get("outcome_added") == "1",
            "back_url": reverse("opportunity-queue"),
        }
        return render(
            self.request,
            "core/opportunities/detail.html",
            context,
            status=status,
        )


class OpportunityQueueView(LoginRequiredMixin, ListView):
    model = ProfileOpportunity
    template_name = "core/opportunities/queue.html"
    context_object_name = "opportunities"
    paginate_by = 50

    def get_queryset(self):
        return (
            get_profile_opportunity_queryset_for_user(self.request.user)
            .annotate(
                priority_rank=Case(
                    When(
                        manual_override=True,
                        override_priority_band=ProfileOpportunity.PriorityBand.HIGH,
                        then=Value(0),
                    ),
                    When(
                        manual_override=True,
                        override_priority_band=ProfileOpportunity.PriorityBand.MEDIUM,
                        then=Value(1),
                    ),
                    When(
                        manual_override=True,
                        override_priority_band=ProfileOpportunity.PriorityBand.LOW,
                        then=Value(2),
                    ),
                    When(priority_band=ProfileOpportunity.PriorityBand.HIGH, then=Value(0)),
                    When(priority_band=ProfileOpportunity.PriorityBand.MEDIUM, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
            .order_by("priority_rank", "-updated_at", "-created_at")
        )


class OpportunityDetailView(LoginRequiredMixin, OpportunityScopedMixin, DetailView):
    model = ProfileOpportunity
    template_name = "core/opportunities/detail.html"
    context_object_name = "opportunity"

    def get_object(self, queryset=None):
        return super().get_object()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opportunity = self.object
        context["form"] = kwargs.get("form") or ProfileOpportunityForm(
            instance=opportunity,
            user=self.request.user,
        )
        context["outcome_form"] = kwargs.get("outcome_form") or OutcomeEntryForm()
        context["saved"] = self.request.GET.get("saved") == "1"
        context["outcome_added"] = self.request.GET.get("outcome_added") == "1"
        context["back_url"] = reverse("opportunity-queue")
        return context


class OpportunityUpdateView(LoginRequiredMixin, OpportunityScopedMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        opportunity = self.get_object()
        form = ProfileOpportunityForm(
            request.POST,
            instance=opportunity,
            user=request.user,
        )

        if form.is_valid():
            form.save()
            redirect_url = reverse("opportunity-detail", kwargs={"pk": opportunity.pk})
            redirect_url = append_query_parameter(redirect_url, "saved", "1")
            return HttpResponseRedirect(redirect_url)

        outcome_form = OutcomeEntryForm()
        return self.render_detail(
            opportunity=opportunity,
            form=form,
            outcome_form=outcome_form,
            status=200,
        )


class OpportunityOutcomeCreateView(LoginRequiredMixin, OpportunityScopedMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        opportunity = self.get_object()
        form = OutcomeEntryForm(request.POST)

        if form.is_valid():
            outcome = form.save(commit=False)
            outcome.opportunity = opportunity
            outcome.created_by = request.user
            outcome.save()

            redirect_url = reverse("opportunity-detail", kwargs={"pk": opportunity.pk})
            redirect_url = append_query_parameter(redirect_url, "outcome_added", "1")
            return HttpResponseRedirect(redirect_url)

        main_form = ProfileOpportunityForm(
            instance=opportunity,
            user=request.user,
        )
        return self.render_detail(
            opportunity=opportunity,
            form=main_form,
            outcome_form=form,
            status=200,
        )
