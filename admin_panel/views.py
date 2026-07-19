"""
admin_panel/views.py — Phase 11: Staff-only custom views.
All routes are protected with staff_member_required.
"""
from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from mood_tracking.models import MoodEntry
from wellness_library.models import Resource

User = get_user_model()


@method_decorator(staff_member_required, name="dispatch")
class AdminDashboardView(View):
    template_name = "admin_panel/admin_dashboard.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        total_users = User.objects.count()
        total_mood_entries = MoodEntry.objects.count()
        total_resources = Resource.objects.count()
        recent_users = User.objects.order_by("-date_joined")[:10]

        return render(request, self.template_name, {
            "total_users": total_users,
            "total_mood_entries": total_mood_entries,
            "total_resources": total_resources,
            "recent_users": recent_users,
        })


@method_decorator(staff_member_required, name="dispatch")
class AdminUserListView(View):
    template_name = "admin_panel/admin_user_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        users = User.objects.order_by("-date_joined")
        return render(request, self.template_name, {"users": users})


@method_decorator(staff_member_required, name="dispatch")
class AdminResourceListView(View):
    template_name = "admin_panel/admin_resource_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        resources = Resource.objects.all()
        return render(request, self.template_name, {"resources": resources})
