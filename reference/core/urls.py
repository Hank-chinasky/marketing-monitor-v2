from django.urls import path
from core.views import CreatorDetailView, CreatorUpdateView

urlpatterns = [
    path("creators/<int:pk>/", CreatorDetailView.as_view(), name="creator-detail"),
    path("creators/<int:pk>/edit/", CreatorUpdateView.as_view(), name="creator-update"),
]
