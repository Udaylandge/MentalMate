from django.conf import settings
from django.db import models


class Report(models.Model):
    REPORT_WEEKLY = "weekly"
    REPORT_MONTHLY = "monthly"
    REPORT_TYPE_CHOICES = [
        (REPORT_WEEKLY, "Weekly"),
        (REPORT_MONTHLY, "Monthly"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"{self.get_report_type_display()} report for {self.user_id} ({self.period_start}–{self.period_end})"
