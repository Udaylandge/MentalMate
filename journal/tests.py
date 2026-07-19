from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import JournalEntry
from .services import sanitize_journal_text, search_journal_entries


User = get_user_model()


class JournalModelAndServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="journal1@example.com",
            password="StrongPass123!",
            username="journal1",
        )

    def test_sanitize_removes_script(self):
        raw = "Hello <script>alert('x')</script> world"
        cleaned = sanitize_journal_text(raw)
        self.assertNotIn("<script", cleaned.lower())
        self.assertIn("Hello", cleaned)

    def test_sanitize_neutralizes_template_expressions(self):
        raw = "Value: {{ user }}"
        cleaned = sanitize_journal_text(raw)
        self.assertNotIn("{{", cleaned)
        self.assertNotIn("}}", cleaned)
        self.assertIn("&#123;&#123;", cleaned)

    def test_save_valid_text(self):
        entry = JournalEntry.objects.create(user=self.user, text="My day was okay.")
        self.assertEqual(entry.user, self.user)
        self.assertTrue(JournalEntry.objects.filter(pk=entry.pk).exists())

    def test_reject_over_length_text(self):
        too_long = "a" * 5001
        with self.assertRaises(Exception):
            # Model field max_length will raise either ValidationError or DB error.
            JournalEntry.objects.create(user=self.user, text=too_long)

    def test_keyword_search_case_insensitive_substring(self):
        e1 = JournalEntry.objects.create(user=self.user, text="I felt calm and relaxed.")
        e2 = JournalEntry.objects.create(user=self.user, text="Stressful day, but I tried breathing.")
        e3 = JournalEntry.objects.create(user=self.user, text="Nothing relevant here.")

        results = search_journal_entries(user=self.user, keyword="CALM")
        self.assertIn(e1, results)
        self.assertNotIn(e2, results)
        self.assertNotIn(e3, results)

        results2 = search_journal_entries(user=self.user, keyword="breathing")
        self.assertIn(e2, results2)
        self.assertNotIn(e1, results2)
        self.assertNotIn(e3, results2)
