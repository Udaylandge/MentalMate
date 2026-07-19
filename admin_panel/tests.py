"""Phase 11 — Admin Panel Tests"""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AdminPanelAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(email="user@example.com", password="Password1")
        self.staff_user = User.objects.create_user(
            email="staff@example.com", password="Password1", is_staff=True
        )

    def test_non_staff_blocked_from_admin_dashboard(self):
        self.client.force_login(self.regular_user)
        resp = self.client.get(reverse("admin-panel"))
        # Should redirect (staff_member_required redirects non-staff)
        self.assertIn(resp.status_code, [302, 403])

    def test_staff_can_access_admin_dashboard(self):
        self.client.force_login(self.staff_user)
        resp = self.client.get(reverse("admin-panel"))
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated_blocked_from_admin(self):
        resp = self.client.get(reverse("admin-panel"))
        self.assertEqual(resp.status_code, 302)
