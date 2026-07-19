from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .services import list_notifications, mark_all_read, mark_notification_read


@method_decorator(login_required, name="dispatch")
class NotificationListView(View):
    template_name = "notifications/notification_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        notifications = list_notifications(user=request.user)
        return render(request, self.template_name, {"notifications": notifications})


@method_decorator(login_required, name="dispatch")
class MarkReadView(View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        mark_notification_read(user=request.user, notification_id=pk)
        return redirect("notifications")


@method_decorator(login_required, name="dispatch")
class MarkAllReadView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        mark_all_read(user=request.user)
        return redirect("notifications")
