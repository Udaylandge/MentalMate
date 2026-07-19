from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string

from core.models import EmailVerification

User = get_user_model()


def validate_password_strength(password: str) -> None:
    """
    Server-side password strength validation (Phase 2 requirement).
    Rules are intentionally simple for capstone baseline.
    """
    if not isinstance(password, str):
        raise ValidationError("Invalid password type.")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    # Require at least 1 letter and 1 number.
    has_alpha = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_alpha and has_digit):
        raise ValidationError("Password must include both letters and numbers.")


def create_email_verification(*, user: User, ttl_minutes: int = 60 * 24) -> EmailVerification:
    token = get_random_string(length=48)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ttl_minutes)

    ev = EmailVerification.objects.create(
        user=user,
        token=token,
        created_at=now,
        expires_at=expires_at,
        used=False,
    )
    return ev


def register_user(*, email: str, password: str) -> User:
    """
    Create a new user and issue an email verification token.
    Login will be blocked until email is verified (per requirement).
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required.")

    normalized_email = email.strip().lower()
    if len(normalized_email) > 254 or "@" not in normalized_email:
        raise ValidationError("Enter a valid email address.")

    validate_password_strength(password)

    # Django User model already enforces unique constraints; handle friendly error.
    if User.objects.filter(email__iexact=normalized_email).exists():
        raise ValidationError("A user with this email already exists.")

    user = User.objects.create_user(email=normalized_email, password=password, is_active=True)
    create_email_verification(user=user)
    return user


def verify_email_token(*, token: str) -> User:
    if not token or not isinstance(token, str):
        raise ValidationError("Invalid token.")

    try:
        ev = EmailVerification.objects.select_related("user").get(token=token)
    except EmailVerification.DoesNotExist as exc:
        raise ValidationError("Invalid or expired verification token.") from exc

    now = datetime.now(timezone.utc)
    if ev.used:
        raise ValidationError("This verification token has already been used.")
    if ev.expires_at <= now:
        raise ValidationError("This verification token has expired.")

    ev.used = True
    ev.save(update_fields=["used"])

    user = ev.user
    user.is_active = True
    # store verification state via user flag on profile/auth model later.
    # For now use a boolean on EmailVerification only; for gating login use ev.used status via helper.
    return user


def is_user_verified(user: User) -> bool:
    # A user is considered verified if any unused token was never used;
    # For Phase 2, we treat verified if there exists a used token and no active unused token.
    # Simpler: there is an EmailVerification record marked used for this user.
    return EmailVerification.objects.filter(user=user, used=True).exists()

import re
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from core.models import JournalEntry

User = get_user_model()


_SCRIPT_BLOCK_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
_SCRIPT_TAG_RE = re.compile(r"<script\b[^>]*>", re.IGNORECASE)
_TEMPLATE_EXPR_REPLACEMENTS = {
    "{{": "&#123;&#123;",
    "}}": "&#125;&#125;",
}


def sanitize_journal_text(text: str) -> str:
    """
    Phase 4 journal sanitization (server-side).
    - Strip <script> blocks/tags
    - Neutralize template-injection patterns like {{ }}
    """
    if text is None:
        return ""

    # Remove full script blocks.
    cleaned = _SCRIPT_BLOCK_RE.sub("", text)
    # Remove standalone script opening tags (rare after block removal).
    cleaned = _SCRIPT_TAG_RE.sub("", cleaned)

    # Neutralize template-injection sequences.
    for k, v in _TEMPLATE_EXPR_REPLACEMENTS.items():
        cleaned = cleaned.replace(k, v)

    return cleaned


def validate_journal_text(text: str) -> None:
    if text is None:
        raise ValidationError("Journal text is required.")
    if not isinstance(text, str):
        raise ValidationError("Journal text must be a string.")
    if len(text) == 0:
        raise ValidationError("Journal text cannot be empty.")


@transaction.atomic
def create_journal_entry(*, user: User, text: str) -> JournalEntry:
    validate_journal_text(text)
    cleaned = sanitize_journal_text(text)

    if len(cleaned) > 5000:
        raise ValidationError("Journal entry is too long.")

    return JournalEntry.objects.create(user=user, text=cleaned)


@transaction.atomic
def update_journal_entry(*, user: User, entry_id: int, text: str) -> JournalEntry:
    if entry_id is None:
        raise ValidationError("Journal entry id is required.")
    validate_journal_text(text)

    cleaned = sanitize_journal_text(text)
    if len(cleaned) > 5000:
        raise ValidationError("Journal entry is too long.")

    entry = JournalEntry.objects.select_for_update().get(pk=entry_id, user=user)
    entry.text = cleaned
    entry.save(update_fields=["text"])
    return entry


def delete_journal_entry(*, user: User, entry_id: int) -> None:
    JournalEntry.objects.filter(pk=entry_id, user=user).delete()


def search_journal_entries(*, user: User, keyword: str) -> List[JournalEntry]:
    if keyword is None:
        keyword = ""
    if not isinstance(keyword, str):
        raise ValidationError("Keyword must be a string.")

    # Simple case-insensitive substring match on stored (sanitized) text.
    qs = JournalEntry.objects.filter(user=user)
    if keyword.strip():
        qs = qs.filter(text__icontains=keyword.strip())
    return list(qs.order_by("-created_at"))
"""
mood_tracking/services.py

Business-logic layer for Mood Logging (Phase 3) and Dashboard stats (Phase 5).
dashboard_services.py has been merged here to eliminate duplication.
"""

from datetime import date, timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from core.models import MoodEntry

User = get_user_model()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_mood_score(score: int) -> None:
    """Server-side validation: mood score must be between 1 and 10 inclusive."""
    if not isinstance(score, int):
        raise ValidationError("Mood score must be an integer.")
    if score < 1 or score > 10:
        raise ValidationError("Mood score must be between 1 and 10.")


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

@transaction.atomic
def create_mood_entry(
    *,
    user: User,
    entry_date: date,
    mood_score: int,
    energy: Optional[int] = None,
    stress: Optional[int] = None,
    sleep_hours: Optional[float] = None,
    notes: str = "",
) -> MoodEntry:
    if entry_date is None or not isinstance(entry_date, date):
        raise ValidationError("Entry date is required.")

    validate_mood_score(mood_score)
    if energy is not None:
        if not isinstance(energy, int) or not (1 <= energy <= 10):
            raise ValidationError("Energy must be an integer between 1 and 10.")
    if stress is not None:
        if not isinstance(stress, int) or not (1 <= stress <= 10):
            raise ValidationError("Stress must be an integer between 1 and 10.")
    if sleep_hours is not None:
        if not isinstance(sleep_hours, (int, float)) or not (0 <= sleep_hours <= 24):
            raise ValidationError("Sleep hours must be between 0 and 24.")

    try:
        return MoodEntry.objects.create(
            user=user,
            entry_date=entry_date,
            mood_score=mood_score,
            energy=energy,
            stress=stress,
            sleep_hours=sleep_hours,
            notes=notes,
        )
    except IntegrityError as exc:
        raise ValidationError("You can only log one mood entry per day.") from exc


@transaction.atomic
def update_mood_entry(
    *,
    user: User,
    mood_entry_id: int,
    entry_date: date,
    mood_score: int,
    energy: Optional[int] = None,
    stress: Optional[int] = None,
    sleep_hours: Optional[float] = None,
    notes: str = "",
) -> MoodEntry:
    if mood_entry_id is None:
        raise ValidationError("Mood entry id is required.")
    if entry_date is None or not isinstance(entry_date, date):
        raise ValidationError("Entry date is required.")

    validate_mood_score(mood_score)

    entry = MoodEntry.objects.select_for_update().get(pk=mood_entry_id, user=user)
    try:
        entry.entry_date = entry_date
        entry.mood_score = mood_score
        entry.energy = energy
        entry.stress = stress
        entry.sleep_hours = sleep_hours
        entry.notes = notes
        entry.save(update_fields=["entry_date", "mood_score", "energy", "stress", "sleep_hours", "notes"])
    except IntegrityError as exc:
        raise ValidationError("You can only log one mood entry per day.") from exc

    return entry


def delete_mood_entry(*, user: User, mood_entry_id: int) -> None:
    MoodEntry.objects.filter(pk=mood_entry_id, user=user).delete()


def list_user_mood_entries(*, user: User):
    return MoodEntry.objects.filter(user=user).order_by("-entry_date")


def get_user_mood_entry(*, user: User, mood_entry_id: int) -> MoodEntry:
    return MoodEntry.objects.get(pk=mood_entry_id, user=user)


# ---------------------------------------------------------------------------
# Dashboard / aggregate helpers  (formerly dashboard_services.py)
# ---------------------------------------------------------------------------

def _week_start(d: date) -> date:
    """Return the Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def get_today_mood(*, user: User, today: date | None = None) -> Optional[MoodEntry]:
    if today is None:
        today = date.today()
    try:
        return MoodEntry.objects.get(user=user, entry_date=today)
    except MoodEntry.DoesNotExist:
        return None


def get_weekly_average(*, user: User, reference_day: date | None = None) -> Optional[float]:
    if reference_day is None:
        reference_day = date.today()
    start = _week_start(reference_day)
    days = [start + timedelta(days=i) for i in range(7)]
    scores = list(
        MoodEntry.objects.filter(user=user, entry_date__in=days).values_list("mood_score", flat=True)
    )
    if not scores:
        return None
    return sum(scores) / len(scores)


def get_streak_today_only(*, user: User, today: date | None = None) -> int:
    """
    Streak counts consecutive days with entries ending on TODAY.
    If there's no entry today, streak is 0.
    """
    if today is None:
        today = date.today()

    current_day = today
    streak = 0
    while True:
        exists = MoodEntry.objects.filter(user=user, entry_date=current_day).exists()
        if not exists:
            break
        streak += 1
        current_day = current_day - timedelta(days=1)

    return streak


def get_entries_this_month_count(*, user: User, reference_day: date | None = None) -> int:
    if reference_day is None:
        reference_day = date.today()
    month_start = reference_day.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return MoodEntry.objects.filter(
        user=user, entry_date__gte=month_start, entry_date__lt=next_month
    ).count()

from typing import List, Optional

from core.models import Resource


def list_resources(
    *,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    mood_score: Optional[int] = None,
) -> List[Resource]:
    """
    Return active resources filtered by category / keyword / mood score.
    """
    qs = Resource.objects.filter(is_active=True)

    if category:
        qs = qs.filter(category=category)

    if keyword and keyword.strip():
        from django.db.models import Q
        kw = keyword.strip()
        qs = qs.filter(Q(title__icontains=kw) | Q(description__icontains=kw))

    if mood_score is not None:
        # Include resources whose range covers mood_score (or have no range set).
        from django.db.models import Q
        qs = qs.filter(
            Q(mood_min__isnull=True) | Q(mood_min__lte=mood_score),
        ).filter(
            Q(mood_max__isnull=True) | Q(mood_max__gte=mood_score),
        )

    return list(qs.distinct().order_by("category", "title"))


def get_resources_for_mood(*, mood_score: int) -> List[Resource]:
    """Return resources whose mood_min/max range includes mood_score."""
    return list_resources(mood_score=mood_score)
"""notifications/services.py — Phase 10 notification helpers."""

from django.contrib.auth import get_user_model

from core.models import Notification

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
