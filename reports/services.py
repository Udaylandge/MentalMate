"""
reports/services.py — Phase 9: Weekly/Monthly report generation + CSV export.
No business logic in views — all aggregation happens here.
"""
from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from typing import Optional

from django.contrib.auth import get_user_model

from mood_tracking.models import MoodEntry
from .models import Report

User = get_user_model()


def _week_bounds(reference_day: date) -> tuple[date, date]:
    start = reference_day - timedelta(days=reference_day.weekday())
    end = start + timedelta(days=6)
    return start, end


def _month_bounds(reference_day: date) -> tuple[date, date]:
    start = reference_day.replace(day=1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    end = next_month - timedelta(days=1)
    return start, end


def _aggregate_mood_entries(*, user: User, start: date, end: date) -> dict:
    entries = list(
        MoodEntry.objects.filter(user=user, entry_date__gte=start, entry_date__lte=end)
        .order_by("entry_date")
    )
    scores = [e.mood_score for e in entries]
    average = round(sum(scores) / len(scores), 2) if scores else None
    return {
        "entries": entries,
        "count": len(entries),
        "average": average,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "period_start": start,
        "period_end": end,
    }


def generate_weekly_report(*, user: User, reference_day: Optional[date] = None) -> dict:
    if reference_day is None:
        reference_day = date.today()
    start, end = _week_bounds(reference_day)
    data = _aggregate_mood_entries(user=user, start=start, end=end)
    data["report_type"] = "weekly"

    # Persist record
    Report.objects.create(
        user=user,
        report_type=Report.REPORT_WEEKLY,
        period_start=start,
        period_end=end,
    )
    return data


def generate_monthly_report(*, user: User, reference_day: Optional[date] = None) -> dict:
    if reference_day is None:
        reference_day = date.today()
    start, end = _month_bounds(reference_day)
    data = _aggregate_mood_entries(user=user, start=start, end=end)
    data["report_type"] = "monthly"

    Report.objects.create(
        user=user,
        report_type=Report.REPORT_MONTHLY,
        period_start=start,
        period_end=end,
    )
    return data


def export_mood_entries_csv(*, user: User, start: date, end: date) -> str:
    """Return a CSV string of mood entries for the given period."""
    entries = MoodEntry.objects.filter(
        user=user, entry_date__gte=start, entry_date__lte=end
    ).order_by("entry_date")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Mood Score", "Energy", "Stress", "Sleep Hours", "Notes"])
    for e in entries:
        writer.writerow([
            e.entry_date,
            e.mood_score,
            e.energy if e.energy is not None else "",
            e.stress if e.stress is not None else "",
            e.sleep_hours if e.sleep_hours is not None else "",
            e.notes,
        ])
    return output.getvalue()
