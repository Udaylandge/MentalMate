"""
Phase 7 — Recommendation Engine Tests
Tests confirm: low mood → calming resources / high mood → growth resources / missing data → fallback
"""
from django.test import TestCase

from .services import get_recommendations


class RecommendationEngineTests(TestCase):
    def test_low_mood_high_stress_returns_calming(self):
        recs = get_recommendations(mood=3, stress=8, sleep_hours=7)
        titles = [r["title"] for r in recs]
        # Should include calming recommendations
        self.assertTrue(any("Meditation" in t or "Breathing" in t or "Relaxing" in t for t in titles))

    def test_high_mood_returns_growth(self):
        recs = get_recommendations(mood=9, stress=2, sleep_hours=8)
        titles = [r["title"] for r in recs]
        self.assertTrue(any("Habit" in t or "Gratitude" in t or "Connect" in t or "Physical" in t for t in titles))

    def test_low_sleep_returns_sleep_tips(self):
        recs = get_recommendations(mood=6, stress=4, sleep_hours=4)
        titles = [r["title"] for r in recs]
        self.assertTrue(any("Sleep" in t or "Wind-Down" in t or "Caffeine" in t for t in titles))

    def test_missing_data_returns_general_fallback(self):
        recs = get_recommendations(mood=None, stress=None, sleep_hours=None)
        self.assertGreater(len(recs), 0)
        categories = [r["category"] for r in recs]
        # General fallback should include "general" category items
        self.assertIn("general", categories)

    def test_partial_data_returns_recommendations(self):
        # Only mood provided, no stress/sleep
        recs = get_recommendations(mood=2, stress=None, sleep_hours=None)
        self.assertGreater(len(recs), 0)

    def test_no_duplicates_in_results(self):
        recs = get_recommendations(mood=2, stress=9, sleep_hours=3)
        titles = [r["title"] for r in recs]
        self.assertEqual(len(titles), len(set(titles)))
