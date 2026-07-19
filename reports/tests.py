"""Phase 9 — Reports Tests"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from mood_tracking.models import MoodEntry
from .services import export_mood_entries_csv, generate_monthly_report, generate_weekly_report

User = get_user_model()


class ReportsServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="rep1@example.com", password="Password1")
        # Add mood entries for current week
        today = date.today()
        self.week_start = today - timedelta(days=today.weekday())
        for i in range(5):
            MoodEntry.objects.create(
                user=self.user,
                entry_date=self.week_start + timedelta(days=i),
                mood_score=i + 5,
            )

    def test_weekly_report_correct_average(self):
        data = generate_weekly_report(user=self.user)
        self.assertEqual(data["count"], 5)
        self.assertIsNotNone(data["average"])
        expected = sum(range(5, 10)) / 5
        self.assertAlmostEqual(data["average"], expected)

    def test_weekly_report_fields(self):
        data = generate_weekly_report(user=self.user)
        self.assertIn("entries", data)
        self.assertIn("min_score", data)
        self.assertIn("max_score", data)
        self.assertIn("period_start", data)
        self.assertIn("period_end", data)

    def test_monthly_report_correct_entries(self):
        data = generate_monthly_report(user=self.user)
        self.assertGreaterEqual(data["count"], 5)

    def test_csv_export_contains_all_data(self):
        today = date.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        csv_output = export_mood_entries_csv(user=self.user, start=start, end=end)
        self.assertIn("Date", csv_output)
        self.assertIn("Mood Score", csv_output)
        # Should have 5 data rows
        lines = [l for l in csv_output.strip().split("\n") if l]
        self.assertEqual(len(lines), 6)  # header + 5 entries

    def test_report_download_restricted_to_owner(self):
        """Download endpoint must redirect non-authenticated users."""
        client = Client()
        resp = client.get(reverse("report-export-weekly"))
        self.assertEqual(resp.status_code, 302)
