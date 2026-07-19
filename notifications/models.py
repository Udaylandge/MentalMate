from django.conf import settings
from django.db import models


class Notification(models.Model):
    NOTIF_STREAK = "streak"
    NOTIF_REMINDER = "reminder"
    NOTIF_REPORT = "report"
    NOTIF_GENERAL = "general"

    TYPE_CHOICES = [
        (NOTIF_STREAK, "Streak"),
        (NOTIF_REMINDER, "Reminder"),
        (NOTIF_REPORT, "Report Ready"),
        (NOTIF_GENERAL, "General"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=NOTIF_GENERAL)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.get_notification_type_display()}] {self.message[:60]}"
