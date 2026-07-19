from django.urls import path
from . import views

urlpatterns = [
    path("wellness/", views.WellnessLibraryView.as_view(), name="wellness-list"),
    path("wellness/<int:pk>/", views.ResourceDetailView.as_view(), name="wellness-detail"),
]
