from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from mongoengine import (
    Document,
    IntField,
    StringField,
    DateTimeField,
    FloatField,
    BooleanField,
    URLField,
)
import datetime

# --- AUTHENTICATION MODELS (SQLite) ---

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password is not None:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email=email, password=password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email=email, password=password, **extra_fields)


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = CustomUserManager()

    class Meta:
        db_table = "authentication_customuser"

    def __str__(self) -> str:
        return self.email


class EmailVerification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_verifications")
    token = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        db_table = "authentication_emailverification"

    def __str__(self) -> str:
        return f"EmailVerification(user={self.user_id}, used={self.used})"


# --- MONGOENGINE BUSINESS MODELS ---

class JournalEntry(Document):
    user_id = IntField(required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)
    text = StringField(required=True, max_length=5000)

    meta = {
        'collection': 'journal_entry',
        'ordering': ['-created_at'],
        'indexes': [
            {'fields': ['user_id', 'created_at']}
        ]
    }

    def clean(self):
        super().clean()
        if not self.text:
            raise ValidationError({"text": "Journal text is required."})
        if len(self.text) > 5000:
            raise ValidationError({"text": "Journal entry is too long."})

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.utcnow()
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"JournalEntry(user_id={self.user_id}, created_at={self.created_at})"


class MoodEntry(Document):
    user_id = IntField(required=True)
    entry_date = DateTimeField(required=True)
    mood_score = IntField(required=True)
    energy = IntField()
    stress = IntField()
    sleep_hours = FloatField()
    notes = StringField(default="")

    meta = {
        'collection': 'mood_entry',
        'ordering': ['-entry_date'],
        'indexes': [
            {'fields': ['user_id', 'entry_date'], 'unique': True}
        ]
    }

    def __str__(self) -> str:
        return f"{self.user_id} - {self.entry_date}: mood={self.mood_score}"


class Notification(Document):
    NOTIF_STREAK = "streak"
    NOTIF_REMINDER = "reminder"
    NOTIF_REPORT = "report"
    NOTIF_GENERAL = "general"

    TYPE_CHOICES = (
        (NOTIF_STREAK, "Streak"),
        (NOTIF_REMINDER, "Reminder"),
        (NOTIF_REPORT, "Report Ready"),
        (NOTIF_GENERAL, "General"),
    )

    user_id = IntField(required=True)
    notification_type = StringField(max_length=20, choices=TYPE_CHOICES, default=NOTIF_GENERAL)
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    read = BooleanField(default=False)

    meta = {
        'collection': 'notification',
        'ordering': ['-created_at']
    }

    def get_notification_type_display(self):
        return dict(self.TYPE_CHOICES).get(self.notification_type, self.notification_type)

    def __str__(self) -> str:
        return f"[{self.get_notification_type_display()}] {self.message[:60]}"


class Report(Document):
    REPORT_WEEKLY = "weekly"
    REPORT_MONTHLY = "monthly"
    REPORT_TYPE_CHOICES = (
        (REPORT_WEEKLY, "Weekly"),
        (REPORT_MONTHLY, "Monthly"),
    )

    user_id = IntField(required=True)
    report_type = StringField(max_length=10, choices=REPORT_TYPE_CHOICES, required=True)
    period_start = DateTimeField(required=True)
    period_end = DateTimeField(required=True)
    generated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'collection': 'report',
        'ordering': ['-generated_at']
    }

    def get_report_type_display(self):
        return dict(self.REPORT_TYPE_CHOICES).get(self.report_type, self.report_type)

    def __str__(self) -> str:
        return f"{self.get_report_type_display()} report for {self.user_id} ({self.period_start}-{self.period_end})"


CATEGORY_CHOICES = (
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
)

class Resource(Document):
    title = StringField(max_length=200, required=True)
    category = StringField(max_length=50, choices=CATEGORY_CHOICES, default="general")
    description = StringField(default="")
    link = URLField()
    image_url = URLField()
    mood_min = IntField()
    mood_max = IntField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'collection': 'resource',
        'ordering': ['category', 'title']
    }

    def __str__(self) -> str:
        return f"{self.title} ({self.category})"
