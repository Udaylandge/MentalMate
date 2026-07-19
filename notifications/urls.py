from django.urls import path
from . import views

urlpatterns = [
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:pk>/read/", views.MarkReadView.as_view(), name="notification-mark-read"),
    path("notifications/mark-all-read/", views.MarkAllReadView.as_view(), name="notifications-mark-all-read"),
]
