from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("mood", views.MoodEntryViewSet, basename="api-mood")
router.register("journal", views.JournalEntryViewSet, basename="api-journal")
router.register("resources", views.ResourceViewSet, basename="api-resources")

urlpatterns = [
    path("api/", include(router.urls)),
]
