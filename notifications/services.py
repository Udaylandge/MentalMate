"""notifications/services.py — Phase 10 notification helpers."""
from __future__ import annotations

from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def create_streak_notification(*, user: User, streak: int) -> Notification:
    msg = f"🔥 You're on a {streak}-day streak! Keep it up!"
    return Notification.objects.create(
        user=user,
        notification_type=Notification.NOTIF_STREAK,
        message=msg,
    )


def create_reminder_notification(*, user: User) -> Notification:
    msg = "👋 Don't forget to log your mood for today!"
    return Notification.objects.create(
        user=user,
        notification_type=Notification.NOTIF_REMINDER,
        message=msg,
    )


def create_report_notification(*, user: User, report_type: str) -> Notification:
    msg = f"📊 Your {report_type} report is ready. Check it out!"
    return Notification.objects.create(
        user=user,
        notification_type=Notification.NOTIF_REPORT,
        message=msg,
    )


def mark_notification_read(*, user: User, notification_id: int) -> None:
    Notification.objects.filter(pk=notification_id, user=user).update(read=True)


def mark_all_read(*, user: User) -> None:
    Notification.objects.filter(user=user, read=False).update(read=True)


def get_unread_count(*, user: User) -> int:
    return Notification.objects.filter(user=user, read=False).count()


def list_notifications(*, user: User):
    return Notification.objects.filter(user=user).order_by("-created_at")
