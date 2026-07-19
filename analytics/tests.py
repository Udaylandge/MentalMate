from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from mood_tracking.models import MoodEntry

from .services import (
    get_chart_points_last_7_days,
    get_monthly_average,
    get_trend_label,
    get_weekly_average_current_week,
)

User = get_user_model()


class AnalyticsPhase6Tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="analytics1@example.com",
            password="Password1",
            is_active=True,
        )
        self.client.force_login(self.user)

    def _monday_of_week(self, reference_day: date) -> date:
        return reference_day - timedelta(days=reference_day.weekday())

    def test_weekly_average_current_week(self):
        ref = date(2026, 1, 14)  # Wednesday
        mon = self._monday_of_week(ref)

        # Create entries Mon..Sun with scores 1..7
        for i in range(7):
            MoodEntry.objects.create(user=self.user, entry_date=mon + timedelta(days=i), mood_score=i + 1)

        avg = get_weekly_average_current_week(user=self.user, reference_day=ref)
        self.assertAlmostEqual(avg, sum(range(1, 8)) / 7)

    def test_monthly_average(self):
        ref = date(2026, 1, 20)

        # January entries: scores 4 and 7 => avg 5.5
        MoodEntry.objects.create(user=self.user, entry_date=date(2026, 1, 1), mood_score=4)
        MoodEntry.objects.create(user=self.user, entry_date=date(2026, 1, 31), mood_score=7)

        # December entry should not affect January average
        MoodEntry.objects.create(user=self.user, entry_date=date(2025, 12, 31), mood_score=3)

        avg = get_monthly_average(user=self.user, reference_day=ref)
        self.assertAlmostEqual(avg, 5.5)

    def test_chart_points_last_7_days_includes_missing_days(self):
        # Put entries on the first and last day of the last-7-days window
        ref = date(2026, 1, 10)
        start = ref - timedelta(days=6)
        MoodEntry.objects.create(user=self.user, entry_date=start, mood_score=2)
        MoodEntry.objects.create(user=self.user, entry_date=ref, mood_score=8)

        labels, scores = get_chart_points_last_7_days(user=self.user, reference_day=ref)
        self.assertEqual(len(labels), 7)
        self.assertEqual(len(scores), 7)

        # First day present, middle missing
        self.assertEqual(scores[0], 2)
        self.assertIsNone(scores[1])

        # Last day present
        self.assertEqual(scores[-1], 8)

    def test_trend_label_improving(self):
        # Prior week (Mon..Sun): avg 3
        # Current week (Mon..Sun): avg 5 => improving
        ref = date(2026, 1, 14)  # Wednesday => same week
        current_mon = self._monday_of_week(ref)
        prior_mon = current_mon - timedelta(days=7)

        for i in range(7):
            MoodEntry.objects.create(user=self.user, entry_date=prior_mon + timedelta(days=i), mood_score=3)
            MoodEntry.objects.create(user=self.user, entry_date=current_mon + timedelta(days=i), mood_score=5)

        trend = get_trend_label(user=self.user, reference_day=ref)
        self.assertEqual(trend, "improving")

    def test_analytics_view_renders_and_empty_state(self):
        # No entries -> weekly/monthly should be empty, chart should show empty prompt
        resp = self.client.get("/analytics/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Add mood entries to see your trend chart.")

    def test_analytics_view_updates_after_new_entry(self):
        today = date.today()

        # Make a request with no data first
        resp1 = self.client.get("/analytics/")
        self.assertEqual(resp1.status_code, 200)
        self.assertContains(resp1, "Add mood entries to see your trend chart.")

        # Add entries so the last-7-days window definitely contains data.
        # (Chart.js empty-state logic depends on any non-null point in the last 7 days.)
        for i in range(7):
            MoodEntry.objects.create(
                user=self.user,
                entry_date=today - timedelta(days=6 - i),
                mood_score=5 + (i % 2),
            )

        resp2 = self.client.get("/analytics/")
        self.assertEqual(resp2.status_code, 200)
        self.assertNotContains(resp2, "Add mood entries to see your trend chart.")
