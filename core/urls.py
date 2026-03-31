from django.urls import path

from core.admin_update_views import CreatorChannelUpdateView, CreatorUpdateView
from core.assignment_views import (
    AssignmentListView,
    OperatorAssignmentDeactivateView,
)
from core.material_views import (
    CreatorDetailView,
    CreatorMaterialBulkDeleteView,
    CreatorMaterialDownloadView,
)
from core.opportunity_views import (
    OpportunityDetailView,
    OpportunityOutcomeCreateView,
    OpportunityQueueView,
    OpportunityUpdateView,
)
from core.views import (
    ChannelDetailView,
    ChannelListView,
    CreatorChannelCreateView,
    CreatorCreateView,
    CreatorListView,
    CreatorNetworkView,
    HealthzView,
    OperationsDashboardView,
    OperatorAssignmentCreateView,
    OperatorAssignmentUpdateView,
    OperatorCreateView,
    OperatorListView,
    OperatorPasswordResetView,
    OperatorToggleActiveView,
    OperatorUpdateView,
)
from core.workspace_views import InstagramWorkspaceView

urlpatterns = [
    path("healthz/", HealthzView.as_view(), name="healthz"),
    path("", OperationsDashboardView.as_view(), name="operations-dashboard"),
    path("creators/", CreatorListView.as_view(), name="creator-list"),
    path("creators/create/", CreatorCreateView.as_view(), name="creator-create"),
    path("creators/<int:pk>/", CreatorDetailView.as_view(), name="creator-detail"),
    path(
        "creators/<int:creator_pk>/materials/<int:material_pk>/download/",
        CreatorMaterialDownloadView.as_view(),
        name="creator-material-download",
    ),
    path(
        "creators/<int:creator_pk>/materials/bulk-delete/",
        CreatorMaterialBulkDeleteView.as_view(),
        name="creator-material-bulk-delete",
    ),
    path("creators/<int:pk>/edit/", CreatorUpdateView.as_view(), name="creator-update"),
    path("creators/<int:pk>/network/", CreatorNetworkView.as_view(), name="creator-network"),
    path("channels/", ChannelListView.as_view(), name="channel-list"),
    path("channels/create/", CreatorChannelCreateView.as_view(), name="channel-create"),
    path("channels/<int:pk>/", ChannelDetailView.as_view(), name="channel-detail"),
    path(
        "channels/<int:pk>/workspace/",
        InstagramWorkspaceView.as_view(),
        name="instagram-workspace",
    ),
    path("channels/<int:pk>/edit/", CreatorChannelUpdateView.as_view(), name="channel-update"),
    path("assignments/", AssignmentListView.as_view(), name="assignment-list"),
    path("assignments/create/", OperatorAssignmentCreateView.as_view(), name="assignment-create"),
    path("assignments/<int:pk>/edit/", OperatorAssignmentUpdateView.as_view(), name="assignment-update"),
    path(
        "assignments/<int:pk>/deactivate/",
        OperatorAssignmentDeactivateView.as_view(),
        name="assignment-deactivate",
    ),
    path("operators/", OperatorListView.as_view(), name="operator-list"),
    path("operators/create/", OperatorCreateView.as_view(), name="operator-create"),
    path("operators/<int:pk>/edit/", OperatorUpdateView.as_view(), name="operator-update"),
    path(
        "operators/<int:pk>/toggle-active/",
        OperatorToggleActiveView.as_view(),
        name="operator-toggle-active",
    ),
    path(
        "operators/<int:pk>/reset-password/",
        OperatorPasswordResetView.as_view(),
        name="operator-reset-password",
    ),
    path("opportunities/", OpportunityQueueView.as_view(), name="opportunity-queue"),
    path("opportunities/<int:pk>/", OpportunityDetailView.as_view(), name="opportunity-detail"),
    path("opportunities/<int:pk>/save/", OpportunityUpdateView.as_view(), name="opportunity-save"),
    path(
        "opportunities/<int:pk>/outcomes/add/",
        OpportunityOutcomeCreateView.as_view(),
        name="opportunity-outcome-add",
    ),
]