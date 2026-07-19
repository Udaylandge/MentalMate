from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .services import (
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
