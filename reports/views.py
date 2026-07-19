from __future__ import annotations

import datetime
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .models import Report
from .services import export_mood_entries_csv, generate_monthly_report, generate_weekly_report


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
