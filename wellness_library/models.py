from django.db import models


CATEGORY_CHOICES = [
    ("meditation", "Meditation"),
    ("breathing", "Breathing"),
    ("sleep", "Sleep"),
    ("exercise", "Exercise"),
    ("nutrition", "Nutrition"),
    ("journaling", "Journaling"),
    ("music", "Music"),
    ("social", "Social"),
    ("growth", "Growth"),
    ("general", "General"),
]


class Resource(models.Model):
    """
    Phase 8: Wellness Library resource — admin-managed, user-visible.
    mood_min/mood_max allow the recommendation engine to suggest relevant resources.
    """
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="general")
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    image_url = models.URLField(blank=True)

    # Mood range this resource is appropriate for (1-10 scale). null = no filter.
    mood_min = models.IntegerField(null=True, blank=True)
    mood_max = models.IntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self) -> str:
        return f"{self.title} ({self.category})"
