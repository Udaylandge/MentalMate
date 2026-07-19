from django.conf import settings
from django.db import models


class MoodEntry(models.Model):
    """
    Phase 3: Mood Logging — one entry per day per user.
    Extended in Phase 3+ with energy/stress/sleep/notes fields.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entry_date = models.DateField()
    mood_score = models.IntegerField()

    # Optional extended fields (energy 1-10, stress 1-10, sleep 0-24 h)
    energy = models.IntegerField(null=True, blank=True)
    stress = models.IntegerField(null=True, blank=True)
    sleep_hours = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "entry_date"], name="unique_mood_entry_per_day")
        ]
        ordering = ["-entry_date"]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.entry_date}: mood={self.mood_score}"
