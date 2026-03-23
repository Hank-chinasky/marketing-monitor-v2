from django.urls import path

from core.views import (
    AssignmentListView,
    ChannelDetailView,
    ChannelListView,
    CreatorChannelCreateView,
    CreatorChannelUpdateView,
    CreatorCreateView,
    CreatorDetailView,
    CreatorListView,
    CreatorNetworkView,
    CreatorUpdateView,
    HealthzView,
    OperationsDashboardView,
    OperatorAssignmentCreateView,
    OperatorAssignmentUpdateView,
    OperatorCreateView,
    OperatorListView,
)

urlpatterns = [
    path("healthz/", HealthzView.as_view(), name="healthz"),
    path("", OperationsDashboardView.as_view(), name="operations-dashboard"),
    path("creators/", CreatorListView.as_view(), name="creator-list"),
    path("creators/create/", CreatorCreateView.as_view(), name="creator-create"),
    path("creators/<int:pk>/", CreatorDetailView.as_view(), name="creator-detail"),
    path("creators/<int:pk>/edit/", CreatorUpdateView.as_view(), name="creator-update"),
    path("creators/<int:pk>/network/", CreatorNetworkView.as_view(), name="creator-network"),
    path("channels/", ChannelListView.as_view(), name="channel-list"),
    path("channels/create/", CreatorChannelCreateView.as_view(), name="channel-create"),
    path("channels/<int:pk>/", ChannelDetailView.as_view(), name="channel-detail"),
    path("channels/<int:pk>/edit/", CreatorChannelUpdateView.as_view(), name="channel-update"),
    path("assignments/", AssignmentListView.as_view(), name="assignment-list"),
    path("assignments/create/", OperatorAssignmentCreateView.as_view(), name="assignment-create"),
    path("assignments/<int:pk>/edit/", OperatorAssignmentUpdateView.as_view(), name="assignment-update"),
    path("operators/", OperatorListView.as_view(), name="operator-list"),
    path("operators/create/", OperatorCreateView.as_view(), name="operator-create"),
]