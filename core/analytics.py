from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, Tuple

from django.contrib.auth import get_user_model

from core.models import MoodEntry

User = get_user_model()


def _week_start(d: date) -> date:
    # Monday as week start
    return d - timedelta(days=d.weekday())


def get_weekly_average_current_week(*, user: User, reference_day: date | None = None) -> Optional[float]:
    if reference_day is None:
        reference_day = date.today()
    start = _week_start(reference_day)
    days = [start + timedelta(days=i) for i in range(7)]
    scores = list(MoodEntry.objects.filter(user=user, entry_date__in=days).values_list("mood_score", flat=True))
    if not scores:
        return None
    return sum(scores) / len(scores)


def get_weekly_average_prior_week(*, user: User, reference_day: date | None = None) -> Optional[float]:
    if reference_day is None:
        reference_day = date.today()
    this_start = _week_start(reference_day)
    prior_start = this_start - timedelta(days=7)
    days = [prior_start + timedelta(days=i) for i in range(7)]
    scores = list(MoodEntry.objects.filter(user=user, entry_date__in=days).values_list("mood_score", flat=True))
    if not scores:
        return None
    return sum(scores) / len(scores)


def get_monthly_average(*, user: User, reference_day: date | None = None) -> Optional[float]:
    if reference_day is None:
        reference_day = date.today()

    month_start = reference_day.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)

    qs = MoodEntry.objects.filter(user=user, entry_date__gte=month_start, entry_date__lt=next_month)
    scores = list(qs.values_list("mood_score", flat=True))
    if not scores:
        return None
    return sum(scores) / len(scores)


def get_chart_points_last_7_days(
    *, user: User, reference_day: date | None = None
) -> Tuple[List[str], List[Optional[int]]]:
    """
    Returns X labels and Y points for the last 7 days (including reference_day).
    Missing days become None so Chart.js can show breaks.
    """
    if reference_day is None:
        reference_day = date.today()

    start = reference_day - timedelta(days=6)
    days = [start + timedelta(days=i) for i in range(7)]

    score_by_day = dict(
        MoodEntry.objects.filter(user=user, entry_date__in=days).values_list("entry_date", "mood_score")
    )

    labels = [d.isoformat() for d in days]
    points: List[Optional[int]] = [score_by_day.get(d) for d in days]
    return labels, points


def get_trend_label(*, user: User, reference_day: date | None = None) -> str:
    """
    Trend label based on prior week vs current week average:
    - improving: current > prior by at least 0.5
    - stable: within [-0.5, +0.5]
    - declining: current < prior by at least 0.5
    If prior or current is missing, return 'stable'.
    """
    current = get_weekly_average_current_week(user=user, reference_day=reference_day)
    prior = get_weekly_average_prior_week(user=user, reference_day=reference_day)

    if current is None or prior is None:
        return "stable"

    delta = current - prior
    if delta >= 0.5:
        return "improving"
    if delta <= -0.5:
        return "declining"
    return "stable"
