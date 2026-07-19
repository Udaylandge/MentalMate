from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("mood/", views.MoodEntryListView.as_view(), name="mood-list"),
    path("mood/new/", views.MoodEntryCreateView.as_view(), name="mood-new"),
    path("mood/<int:pk>/edit/", views.MoodEntryUpdateView.as_view(), name="mood-edit"),
    path("mood/<int:pk>/delete/", views.MoodEntryDeleteView.as_view(), name="mood-delete"),
]
