from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .services import (
    get_entries_this_month_count,
    get_streak_today_only,
    get_weekly_average,
)
from .models import MoodEntry

User = get_user_model()


class MoodLoggingPhase3Tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="mood1@example.com",
            password="Password1",
            is_active=True,
        )
        self.client.force_login(self.user)

    def test_save_score_rejects_out_of_range(self):
        entry_date = date.today()

        resp = self.client.post(
            reverse("mood-new"),
            data={"entry_date": entry_date.isoformat(), "mood_score": 0},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(MoodEntry.objects.filter(user=self.user, entry_date=entry_date).exists())

    def test_save_score_rejects_out_of_range_high(self):
        entry_date = date.today()

        resp = self.client.post(
            reverse("mood-new"),
            data={"entry_date": entry_date.isoformat(), "mood_score": 11},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(MoodEntry.objects.filter(user=self.user, entry_date=entry_date).exists())

    def test_one_entry_per_day_enforced(self):
        entry_date = date.today()

        resp1 = self.client.post(
            reverse("mood-new"),
            data={"entry_date": entry_date.isoformat(), "mood_score": 5},
            follow=True,
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertTrue(MoodEntry.objects.filter(user=self.user, entry_date=entry_date, mood_score=5).exists())

        # Second entry same day should be rejected.
        resp2 = self.client.post(
            reverse("mood-new"),
            data={"entry_date": entry_date.isoformat(), "mood_score": 7},
            follow=True,
        )
        self.assertEqual(resp2.status_code, 200)

        entries = MoodEntry.objects.filter(user=self.user, entry_date=entry_date)
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().mood_score, 5)

    def test_edit_entry_updates_values(self):
        entry_date = date.today()
        entry = MoodEntry.objects.create(user=self.user, entry_date=entry_date, mood_score=4)

        resp = self.client.post(
            reverse("mood-edit", kwargs={"pk": entry.pk}),
            data={"entry_date": entry_date.isoformat(), "mood_score": 9},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)

        entry.refresh_from_db()
        self.assertEqual(entry.mood_score, 9)

    def test_delete_entry_removes_record(self):
        entry_date = date.today()
        entry = MoodEntry.objects.create(user=self.user, entry_date=entry_date, mood_score=3)

        resp = self.client.post(
            reverse("mood-delete", kwargs={"pk": entry.pk}),
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)

        self.assertFalse(MoodEntry.objects.filter(pk=entry.pk).exists())

    def test_login_required_for_mood_pages(self):
        self.client.logout()
        entry_date = date.today()

        resp = self.client.get(reverse("mood-list"))
        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(
            reverse("mood-new"),
            data={"entry_date": entry_date.isoformat(), "mood_score": 5},
        )
        self.assertEqual(resp.status_code, 302)


class DashboardPhase5Tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="dash1@example.com",
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

        avg = get_weekly_average(user=self.user, reference_day=ref)
        self.assertIsNotNone(avg)
        self.assertAlmostEqual(avg, sum(range(1, 8)) / 7)

    def test_streak_today_only(self):
        today = date(2026, 1, 10)
        yesterday = today - timedelta(days=1)

        # No entry today -> streak should be 0 even if yesterday exists
        MoodEntry.objects.create(user=self.user, entry_date=yesterday, mood_score=5)
        streak = get_streak_today_only(user=self.user, today=today)
        self.assertEqual(streak, 0)

        # Add today's entry -> streak should count consecutive ending today
        MoodEntry.objects.create(user=self.user, entry_date=today, mood_score=6)
        streak = get_streak_today_only(user=self.user, today=today)
        self.assertEqual(streak, 2)

    def test_entries_this_month_count(self):
        ref = date(2026, 1, 20)

        # In January
        MoodEntry.objects.create(user=self.user, entry_date=date(2026, 1, 1), mood_score=4)
        MoodEntry.objects.create(user=self.user, entry_date=date(2026, 1, 31), mood_score=7)

        # In December
        MoodEntry.objects.create(user=self.user, entry_date=date(2025, 12, 31), mood_score=3)

        count = get_entries_this_month_count(user=self.user, reference_day=ref)
        self.assertEqual(count, 2)

    def test_dashboard_view_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_view_renders(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Dashboard")
