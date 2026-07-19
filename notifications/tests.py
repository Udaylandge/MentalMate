"""Phase 10 — Notifications Tests"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from .services import (
    create_reminder_notification,
    create_streak_notification,
    get_unread_count,
    mark_all_read,
    mark_notification_read,
)
from .models import Notification

User = get_user_model()


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="notif1@example.com", password="Password1")

    def test_create_streak_notification(self):
        notif = create_streak_notification(user=self.user, streak=7)
        self.assertIn("7", notif.message)
        self.assertEqual(notif.notification_type, Notification.NOTIF_STREAK)
        self.assertFalse(notif.read)

    def test_create_reminder_notification(self):
        notif = create_reminder_notification(user=self.user)
        self.assertEqual(notif.notification_type, Notification.NOTIF_REMINDER)
        self.assertFalse(notif.read)

    def test_unread_count(self):
        create_streak_notification(user=self.user, streak=3)
        create_reminder_notification(user=self.user)
        self.assertEqual(get_unread_count(user=self.user), 2)

    def test_mark_notification_read(self):
        notif = create_streak_notification(user=self.user, streak=5)
        mark_notification_read(user=self.user, notification_id=notif.pk)
        notif.refresh_from_db()
        self.assertTrue(notif.read)
        self.assertEqual(get_unread_count(user=self.user), 0)

    def test_mark_all_read(self):
        create_streak_notification(user=self.user, streak=1)
        create_reminder_notification(user=self.user)
        mark_all_read(user=self.user)
        self.assertEqual(get_unread_count(user=self.user), 0)
