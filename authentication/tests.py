from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerification
from .models import CustomUser


class AuthenticationPhase2Tests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_valid_creates_user_and_rejects_login_until_verified(self):
        resp = self.client.post(
            reverse("register"),
            data={"email": "test@example.com", "password": "Password1"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)

        user = CustomUser.objects.get(email="test@example.com")
        self.assertTrue(CustomUser.objects.filter(email="test@example.com").exists())

        token_obj = EmailVerification.objects.get(user=user)
        self.assertFalse(token_obj.used)

        login_resp = self.client.post(
            reverse("login"),
            data={"email": "test@example.com", "password": "Password1"},
            follow=True,
        )
        self.assertEqual(login_resp.status_code, 200)
        # verify that login is blocked (still on login page)
        self.assertContains(login_resp, "Please verify your email")

        # now verify
        verify_resp = self.client.get(reverse("verify-email", kwargs={"token": token_obj.token}), follow=True)
        self.assertEqual(verify_resp.status_code, 200)

        login_resp2 = self.client.post(
            reverse("login"),
            data={"email": "test@example.com", "password": "Password1"},
            follow=True,
        )
        self.assertEqual(login_resp2.status_code, 200)
        # profile page should load
        self.assertContains(login_resp2, "Your Profile")

    def test_register_rejects_duplicate_email(self):
        CustomUser.objects.create_user(email="dup@example.com", password="Password1")
        EmailVerification.objects.create(
            user=CustomUser.objects.get(email="dup@example.com"),
            token="tok1" * 16,
            created_at=timezone.now(),
            expires_at=timezone.now(),
            used=False,
        )

        resp = self.client.post(
            reverse("register"),
            data={"email": "dup@example.com", "password": "Password1"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "already exists")

    def test_register_rejects_weak_password(self):
        resp = self.client.post(
            reverse("register"),
            data={"email": "weak@example.com", "password": "short"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "at least 8")

    def test_login_rejects_bad_credentials(self):
        user = CustomUser.objects.create_user(email="bad@example.com", password="Password1")
        EmailVerification.objects.create(
            user=user,
            token="tok2" * 16,
            created_at=timezone.now(),
            expires_at=timezone.now(),
            used=True,  # mark verified
        )

        resp = self.client.post(
            reverse("login"),
            data={"email": "bad@example.com", "password": "WrongPassword1"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Invalid email or password")

    def test_logout_clears_session(self):
        user = CustomUser.objects.create_user(email="logout@example.com", password="Password1")
        EmailVerification.objects.create(
            user=user,
            token="tok3" * 16,
            created_at=timezone.now(),
            expires_at=timezone.now(),
            used=True,
        )

        self.client.login(email="logout@example.com", password="Password1")
        logout_resp = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(logout_resp.status_code, 200)
        self.assertFalse(logout_resp.wsgi_request.user.is_authenticated)

    def test_verify_email_rejects_invalid_token(self):
        resp = self.client.get(reverse("verify-email", kwargs={"token": "invalid-token"}), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Invalid or expired verification token")

    def test_verify_email_rejects_expired_token(self):
        user = CustomUser.objects.create_user(email="expired@example.com", password="Password1")
        ev = EmailVerification.objects.create(
            user=user,
            token="tok4" * 16,
            created_at=timezone.now(),
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
            used=False,
        )

        resp = self.client.get(reverse("verify-email", kwargs={"token": ev.token}), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "expired verification token")
