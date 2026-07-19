from django.urls import path

from . import views

urlpatterns = [
    path("journal/", views.JournalEntryListView.as_view(), name="journal-list"),
    path("journal/new/", views.JournalEntryCreateView.as_view(), name="journal-new"),
    path("journal/<int:pk>/edit/", views.JournalEntryUpdateView.as_view(), name="journal-edit"),
    path("journal/<int:pk>/delete/", views.JournalEntryDeleteView.as_view(), name="journal-delete"),
]

