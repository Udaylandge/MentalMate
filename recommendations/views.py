from __future__ import annotations

from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from mood_tracking.services import get_today_mood
from .services import get_recommendations


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
