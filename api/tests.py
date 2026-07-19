"""Phase 12 — REST API Tests"""
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from mood_tracking.models import MoodEntry

User = get_user_model()


class MoodEntryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="api1@example.com", password="Password1")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_mood_entry_via_api(self):
        data = {"entry_date": date.today().isoformat(), "mood_score": 7}
        resp = self.client.post("/api/mood/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MoodEntry.objects.filter(user=self.user, mood_score=7).exists())

    def test_list_mood_entries_via_api(self):
        MoodEntry.objects.create(user=self.user, entry_date=date.today(), mood_score=5)
        resp = self.client.get("/api/mood/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"] if "results" in resp.data else resp.data), 1)

    def test_reject_out_of_range_mood_via_api(self):
        data = {"entry_date": date.today().isoformat(), "mood_score": 11}
        resp = self.client.post("/api/mood/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_blocked_from_api(self):
        client = APIClient()
        resp = client.get("/api/mood/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class JournalEntryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="api2@example.com", password="Password1")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_journal_entry_via_api(self):
        data = {"text": "Today was a good day."}
        resp = self.client.post("/api/journal/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_list_journal_entries_via_api(self):
        resp = self.client.get("/api/journal/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
