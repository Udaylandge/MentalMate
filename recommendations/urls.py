from django.urls import path
from . import views

urlpatterns = [
    path("recommendations/", views.RecommendationsView.as_view(), name="recommendations"),
]
