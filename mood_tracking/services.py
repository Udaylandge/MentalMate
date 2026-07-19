"""
mood_tracking/services.py

Business-logic layer for Mood Logging (Phase 3) and Dashboard stats (Phase 5).
dashboard_services.py has been merged here to eliminate duplication.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import MoodEntry

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
