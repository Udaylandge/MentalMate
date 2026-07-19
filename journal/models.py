from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class JournalEntry(models.Model):
    """
    Phase 4: Journal entries (self-tracking).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Simple model: store created timestamp; list page can show newest-first.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Keep length validation aligned with acceptance test checklist.
    text = models.TextField(max_length=5000)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def clean(self) -> None:
        super().clean()
        if self.text is None:
            raise ValidationError({"text": "Journal text is required."})
        if len(self.text) > 5000:
            raise ValidationError({"text": "Journal entry is too long."})

    def save(self, *args, **kwargs):
        # Ensure model-level validation runs even when tests create objects directly.
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"JournalEntry(user_id={self.user_id}, created_at={self.created_at})"
