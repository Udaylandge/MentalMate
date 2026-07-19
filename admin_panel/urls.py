from django.urls import path
from . import views

urlpatterns = [
    path("admin-panel/", views.AdminDashboardView.as_view(), name="admin-panel"),
    path("admin-panel/users/", views.AdminUserListView.as_view(), name="admin-panel-users"),
    path("admin-panel/resources/", views.AdminResourceListView.as_view(), name="admin-panel-resources"),
]
