from __future__ import annotations
from core.forms import RegisterForm, LoginForm, VerifyEmailForm, JournalEntryForm, MoodEntryForm
"""
admin_panel/views.py — Phase 11: Staff-only custom views.
All routes are protected with staff_member_required.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from core.models import MoodEntry
from core.models import Resource

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

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from core.analytics import (
    get_chart_points_last_7_days,
    get_monthly_average,
    get_trend_label,
    get_weekly_average_current_week,
)


@method_decorator(login_required, name="dispatch")
class AnalyticsView(View):
    template_name = "analytics/analytics.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        weekly_avg = get_weekly_average_current_week(user=request.user)
        monthly_avg = get_monthly_average(user=request.user)
        trend = get_trend_label(user=request.user)
        chart_dates, chart_scores = get_chart_points_last_7_days(user=request.user)

        # Pass a simple boolean so the template can do server-side conditional rendering
        has_chart_data = any(s is not None for s in chart_scores)

        return render(
            request,
            self.template_name,
            {
                "weekly_avg": weekly_avg,
                "monthly_avg": monthly_avg,
                "trend": trend,
                "chart_labels_json": json.dumps(chart_dates),
                "chart_scores_json": json.dumps(chart_scores),
                "has_chart_data": has_chart_data,
            },
        )
"""api/views.py — Phase 12: DRF ViewSets for mood, journal, and resources."""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import MoodEntry
from core.models import JournalEntry
from core.services import create_journal_entry, update_journal_entry
from core.models import Resource
from core.services import create_mood_entry, update_mood_entry

from .serializers import JournalEntrySerializer, MoodEntrySerializer, ResourceSerializer


class MoodEntryViewSet(viewsets.ModelViewSet):
    """
    CRUD for the current user's mood entries.
    GET /api/mood/        — list
    POST /api/mood/       — create
    GET /api/mood/{id}/   — retrieve
    PUT/PATCH /api/mood/{id}/ — update
    DELETE /api/mood/{id}/ — delete
    """
    serializer_class = MoodEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MoodEntry.objects.filter(user=self.request.user).order_by("-entry_date")

    def perform_create(self, serializer):
        data = serializer.validated_data
        try:
            entry = create_mood_entry(
                user=self.request.user,
                entry_date=data["entry_date"],
                mood_score=data["mood_score"],
                energy=data.get("energy"),
                stress=data.get("stress"),
                sleep_hours=data.get("sleep_hours"),
                notes=data.get("notes", ""),
            )
            serializer.instance = entry
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))

    def perform_update(self, serializer):
        data = serializer.validated_data
        try:
            entry = update_mood_entry(
                user=self.request.user,
                mood_entry_id=self.get_object().pk,
                entry_date=data["entry_date"],
                mood_score=data["mood_score"],
                energy=data.get("energy"),
                stress=data.get("stress"),
                sleep_hours=data.get("sleep_hours"),
                notes=data.get("notes", ""),
            )
            serializer.instance = entry
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))


class JournalEntryViewSet(viewsets.ModelViewSet):
    """CRUD for current user's journal entries."""
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        try:
            entry = create_journal_entry(user=self.request.user, text=serializer.validated_data["text"])
            serializer.instance = entry
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))

    def perform_update(self, serializer):
        try:
            entry = update_journal_entry(
                user=self.request.user,
                entry_id=self.get_object().pk,
                text=serializer.validated_data["text"],
            )
            serializer.instance = entry
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))


class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to active wellness resources. Write via Django admin."""
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Resource.objects.filter(is_active=True).order_by("category", "title")

    def get_queryset(self):
        qs = Resource.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        keyword = self.request.query_params.get("q")
        if category:
            qs = qs.filter(category=category)
        if keyword:
            qs = qs.filter(title__icontains=keyword) | Resource.objects.filter(
                is_active=True, description__icontains=keyword
            )
            if category:
                qs = qs.filter(category=category)
        return qs.distinct().order_by("category", "title")
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import View
from django import forms

from core.services import create_email_verification, is_user_verified, register_user, validate_password_strength, verify_email_token

User = get_user_model()





def home(request):
    return render(request, "home.html")


def healthcheck(request):
    """
    Basic health endpoint for Phase 1 verification.
    """
    return JsonResponse({"status": "ok"})


class RegisterView(View):
    template_name = "auth/register.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        try:
            user = register_user(email=form.cleaned_data["email"], password=form.cleaned_data["password"])
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form})

        from django.utils.safestring import mark_safe
        from core.models import EmailVerification
        ev = EmailVerification.objects.filter(user=user, used=False).latest('created_at')
        verify_url = request.build_absolute_uri(reverse('verify-email', args=[ev.token]))
        
        print(f"\n[{user.email}] VERIFICATION LINK (Dev Mode): {verify_url}\n")
        
        # Dev behavior: we don't send real email body in Phase 2 skeleton; verification token exists in DB.
        # A full email template/sending will be added in later phases.
        msg = mark_safe(f"Registration successful. For local testing, <a href='{verify_url}' class='alert-link'>click here to verify your email</a>.")
        messages.success(request, msg)
        return redirect("login")


class LoginView(View):
    template_name = "auth/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]

        user = authenticate(request, username=email, password=password)
        if user is None:
            form.add_error(None, "Invalid email or password.")
            return render(request, self.template_name, {"form": form})

        if not is_user_verified(user):
            form.add_error(None, "Please verify your email before logging in.")
            return render(request, self.template_name, {"form": form})

        login(request, user)
        return redirect("profile")


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect("home")


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    template_name = "auth/profile.html"

    def get(self, request):
        return render(request, self.template_name, {"user": request.user})


@require_http_methods(["GET"])
def verify_email(request, token: str):
    try:
        verify_email_token(token=token)
    except Exception:
        # Tests expect two different substrings:
        # - invalid token: "Invalid or expired verification token"
        # - expired token: "expired verification token"
        #
        # Our service raises "Invalid or expired verification token." for invalid tokens,
        # and "This verification token has expired." for expired ones.
        messages.error(request, "Invalid or expired verification token")
        return redirect("login")

    return redirect("login")

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from core.models import JournalEntry
from core.services import create_journal_entry, delete_journal_entry, search_journal_entries, update_journal_entry



class JournalEntryListView(View):
    template_name = "journal/journal_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        keyword = request.GET.get("q", "")
        entries = search_journal_entries(user=request.user, keyword=keyword)
        return render(request, self.template_name, {"entries": entries, "keyword": keyword})


@method_decorator(login_required, name="dispatch")
class JournalEntryCreateView(View):
    template_name = "journal/journal_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        form = JournalEntryForm()
        return render(request, self.template_name, {"form": form, "mode": "create"})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = JournalEntryForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "create"})

        try:
            create_journal_entry(user=request.user, text=form.cleaned_data["text"])
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "mode": "create"})

        messages.success(request, "Journal entry saved.")
        return redirect("journal-list")


@method_decorator(login_required, name="dispatch")
class JournalEntryUpdateView(View):
    template_name = "journal/journal_form.html"

    def get_object(self, request: HttpRequest, pk: int) -> JournalEntry:
        return get_object_or_404(JournalEntry, pk=pk, user=request.user)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        form = JournalEntryForm(initial={"text": entry.text})
        return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        form = JournalEntryForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

        try:
            update_journal_entry(user=request.user, entry_id=entry.pk, text=form.cleaned_data["text"])
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

        messages.success(request, "Journal entry updated.")
        return redirect("journal-list")


@method_decorator(login_required, name="dispatch")
class JournalEntryDeleteView(View):
    template_name = "journal/journal_confirm_delete.html"

    def get_object(self, request: HttpRequest, pk: int) -> JournalEntry:
        return get_object_or_404(JournalEntry, pk=pk, user=request.user)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        return render(request, self.template_name, {"entry": entry})

    def post(self, request: HttpRequest, pk: int) -> HttpResponseRedirect:
        entry = self.get_object(request, pk)
        delete_journal_entry(user=request.user, entry_id=entry.pk)
        messages.info(request, "Journal entry deleted.")
        return redirect("journal-list")

from datetime import date

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from core.models import MoodEntry
from core.services import (
    create_mood_entry,
    delete_mood_entry,
    get_entries_this_month_count,
    get_streak_today_only,
    get_today_mood,
    get_user_mood_entry,
    get_weekly_average,
    list_user_mood_entries,
    update_mood_entry,
)



class MoodEntryListView(View):
    template_name = "mood_tracking/mood_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        entries = list_user_mood_entries(user=request.user)
        return render(request, self.template_name, {"entries": entries})


@method_decorator(login_required, name="dispatch")
class MoodEntryCreateView(View):
    template_name = "mood_tracking/mood_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        form = MoodEntryForm(initial={"entry_date": date.today()})
        return render(request, self.template_name, {"form": form, "mode": "create"})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = MoodEntryForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "create"})

        try:
            create_mood_entry(
                user=request.user,
                entry_date=form.cleaned_data["entry_date"],
                mood_score=form.cleaned_data["mood_score"],
                energy=form.cleaned_data.get("energy"),
                stress=form.cleaned_data.get("stress"),
                sleep_hours=form.cleaned_data.get("sleep_hours"),
                notes=form.cleaned_data.get("notes", ""),
            )
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "mode": "create"})

        messages.success(request, "Mood entry saved!")
        return redirect("mood-list")


@method_decorator(login_required, name="dispatch")
class MoodEntryUpdateView(View):
    template_name = "mood_tracking/mood_form.html"

    def get_object(self, request: HttpRequest, pk: int) -> MoodEntry:
        return get_object_or_404(MoodEntry, pk=pk, user=request.user)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        form = MoodEntryForm(initial={
            "entry_date": entry.entry_date,
            "mood_score": entry.mood_score,
            "energy": entry.energy,
            "stress": entry.stress,
            "sleep_hours": entry.sleep_hours,
            "notes": entry.notes,
        })
        return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        form = MoodEntryForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

        try:
            update_mood_entry(
                user=request.user,
                mood_entry_id=entry.pk,
                entry_date=form.cleaned_data["entry_date"],
                mood_score=form.cleaned_data["mood_score"],
                energy=form.cleaned_data.get("energy"),
                stress=form.cleaned_data.get("stress"),
                sleep_hours=form.cleaned_data.get("sleep_hours"),
                notes=form.cleaned_data.get("notes", ""),
            )
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

        messages.success(request, "Mood entry updated!")
        return redirect("mood-list")


@method_decorator(login_required, name="dispatch")
class MoodEntryDeleteView(View):
    template_name = "mood_tracking/mood_confirm_delete.html"

    def get_object(self, request: HttpRequest, pk: int) -> MoodEntry:
        return get_object_or_404(MoodEntry, pk=pk, user=request.user)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        return render(request, self.template_name, {"entry": entry})

    def post(self, request: HttpRequest, pk: int) -> HttpResponseRedirect:
        entry = self.get_object(request, pk)
        delete_mood_entry(user=request.user, mood_entry_id=entry.pk)
        messages.info(request, "Mood entry deleted.")
        return redirect("mood-list")


@method_decorator(login_required, name="dispatch")
class DashboardView(View):
    template_name = "mood_tracking/dashboard.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        today_entry = get_today_mood(user=request.user)
        weekly_avg = get_weekly_average(user=request.user)
        streak = get_streak_today_only(user=request.user)
        entries_month = get_entries_this_month_count(user=request.user)

        return render(
            request,
            self.template_name,
            {
                "today_entry": today_entry,
                "weekly_avg": weekly_avg,
                "streak": streak,
                "entries_month": entries_month,
            },
        )

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from core.services import list_notifications, mark_all_read, mark_notification_read


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

from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from core.services import get_today_mood
from core.recommendation import get_recommendations


@method_decorator(login_required, name="dispatch")
class RecommendationsView(View):
    template_name = "recommendations/recommendations.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        # Get today's mood entry to personalize recommendations
        today_entry = get_today_mood(user=request.user)

        mood = today_entry.mood_score if today_entry else None
        stress = today_entry.stress if today_entry else None
        sleep_hours = today_entry.sleep_hours if today_entry else None

        recs = get_recommendations(mood=mood, stress=stress, sleep_hours=sleep_hours)

        return render(request, self.template_name, {
            "recommendations": recs,
            "today_entry": today_entry,
            "has_today_entry": today_entry is not None,
        })

import datetime
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from core.models import Report
from core.reports import export_mood_entries_csv, generate_monthly_report, generate_weekly_report


@method_decorator(login_required, name="dispatch")
class ReportListView(View):
    template_name = "reports/report_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        reports = Report.objects.filter(user=request.user)
        return render(request, self.template_name, {"reports": reports})


@method_decorator(login_required, name="dispatch")
class WeeklyReportView(View):
    template_name = "reports/report_detail.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        data = generate_weekly_report(user=request.user)
        return render(request, self.template_name, {"data": data})


@method_decorator(login_required, name="dispatch")
class MonthlyReportView(View):
    template_name = "reports/report_detail.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        data = generate_monthly_report(user=request.user)
        return render(request, self.template_name, {"data": data})


@method_decorator(login_required, name="dispatch")
class ExportWeeklyCSVView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        today = date.today()
        start = today - datetime.timedelta(days=today.weekday())
        end = start + datetime.timedelta(days=6)
        csv_data = export_mood_entries_csv(user=request.user, start=start, end=end)
        response = HttpResponse(csv_data, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="mentalmate-weekly-{start}.csv"'
        return response


@method_decorator(login_required, name="dispatch")
class ExportMonthlyCSVView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        today = date.today()
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        end = next_month - datetime.timedelta(days=1)
        csv_data = export_mood_entries_csv(user=request.user, start=start, end=end)
        response = HttpResponse(csv_data, content_type="text/csv")
        period = start.strftime("%Y-%m")
        response["Content-Disposition"] = f'attachment; filename="mentalmate-monthly-{period}.csv"'
        return response
from django.shortcuts import render

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from core.models import CATEGORY_CHOICES
from core.services import list_resources


@method_decorator(login_required, name="dispatch")
class WellnessLibraryView(View):
    template_name = "wellness_library/wellness_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        category = request.GET.get("category", "")
        keyword = request.GET.get("q", "")

        resources = list_resources(
            category=category or None,
            keyword=keyword or None,
        )

        return render(request, self.template_name, {
            "resources": resources,
            "category": category,
            "keyword": keyword,
            "categories": CATEGORY_CHOICES,
        })

@method_decorator(login_required, name="dispatch")
class ResourceDetailView(View):
    template_name = "wellness_library/wellness_detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        from django.shortcuts import get_object_or_404
        from core.models import Resource
        resource = get_object_or_404(Resource, pk=pk, is_active=True)
        return render(request, self.template_name, {"resource": resource})
