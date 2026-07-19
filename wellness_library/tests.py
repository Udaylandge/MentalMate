"""Phase 8 — Wellness Library Tests"""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Resource
from .services import get_resources_for_mood, list_resources

User = get_user_model()


class WellnessLibraryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="wellness1@example.com", password="Password1")
        self.client = Client()
        self.client.force_login(self.user)

        # Create resources with different categories and mood ranges
        Resource.objects.create(title="Meditation Guide", category="meditation", mood_min=1, mood_max=5, is_active=True)
        Resource.objects.create(title="Running Tips", category="exercise", mood_min=7, mood_max=10, is_active=True)
        Resource.objects.create(title="Sleep Hygiene", category="sleep", is_active=True)
        Resource.objects.create(title="Inactive Resource", category="general", is_active=False)

    def test_list_all_active_resources(self):
        resources = list_resources()
        # Should exclude inactive
        self.assertEqual(len(resources), 3)

    def test_filter_by_category(self):
        resources = list_resources(category="meditation")
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].title, "Meditation Guide")

    def test_search_by_keyword(self):
        resources = list_resources(keyword="sleep")
        self.assertTrue(any(r.title == "Sleep Hygiene" for r in resources))

    def test_filter_by_mood_score_low(self):
        resources = get_resources_for_mood(mood_score=3)
        titles = [r.title for r in resources]
        # Meditation Guide (1-5) and Sleep Hygiene (no range) should appear
        self.assertIn("Meditation Guide", titles)
        self.assertNotIn("Running Tips", titles)  # mood 7-10 only

    def test_filter_by_mood_score_high(self):
        resources = get_resources_for_mood(mood_score=9)
        titles = [r.title for r in resources]
        self.assertIn("Running Tips", titles)
        self.assertNotIn("Meditation Guide", titles)  # mood 1-5 only

    def test_wellness_list_view_accessible(self):
        resp = self.client.get(reverse("wellness-list"))
        self.assertEqual(resp.status_code, 200)

    def test_wellness_list_filters_work(self):
        resp = self.client.get(reverse("wellness-list") + "?category=exercise")
        self.assertEqual(resp.status_code, 200)

    def test_wellness_list_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("wellness-list"))
        self.assertEqual(resp.status_code, 302)
