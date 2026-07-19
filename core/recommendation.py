"""
recommendations/services.py

Phase 7: Rule-based recommendation engine.
Pure function — no DB access, easy to unit test and swap for ML later.
"""
from __future__ import annotations

from typing import Optional


def get_recommendations(
    *,
    mood: Optional[int] = None,
    stress: Optional[int] = None,
    sleep_hours: Optional[float] = None,
) -> list[dict]:
    """
    Return a list of wellness recommendation dicts based on current mood/stress/sleep.

    Each dict: {title, description, category, icon}

    Rules (Section 7.4):
    - Low mood (≤4) + High stress (≥7) → meditation, breathing, relaxing music
    - Low sleep (≤5 hours)              → sleep hygiene tips
    - High mood (≥8)                    → habit-building / growth resources
    - Missing/incomplete data           → general wellness fallback list
    """
    recommendations: list[dict] = []

    # --- Missing / incomplete data → general fallback ---
    if mood is None and stress is None and sleep_hours is None:
        return _general_wellness()

    # --- Low sleep → sleep hygiene ---
    if sleep_hours is not None and sleep_hours <= 5:
        recommendations.extend(_sleep_hygiene_tips())

    # --- Low mood + high stress → calming resources ---
    if mood is not None and mood <= 4 and stress is not None and stress >= 7:
        recommendations.extend(_calming_resources())
    elif mood is not None and mood <= 4:
        recommendations.extend(_calming_resources())
    elif stress is not None and stress >= 7:
        recommendations.extend(_calming_resources())

    # --- High mood → growth resources ---
    if mood is not None and mood >= 8:
        recommendations.extend(_growth_resources())

    # De-duplicate by title while preserving order
    seen: set[str] = set()
    unique: list[dict] = []
    for r in recommendations:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique.append(r)

    # If nothing matched, return general fallback
    if not unique:
        return _general_wellness()

    return unique


# ---------------------------------------------------------------------------
# Resource lists
# ---------------------------------------------------------------------------

def _calming_resources() -> list[dict]:
    return [
        {
            "title": "Guided Meditation",
            "description": "A 10-minute guided meditation to calm your mind.",
            "category": "meditation",
            "icon": "🧘",
        },
        {
            "title": "4-7-8 Breathing Exercise",
            "description": "A breathing technique that reduces anxiety quickly.",
            "category": "breathing",
            "icon": "🌬️",
        },
        {
            "title": "Relaxing Music Playlist",
            "description": "Lo-fi and nature sounds to ease stress.",
            "category": "music",
            "icon": "🎵",
        },
        {
            "title": "Progressive Muscle Relaxation",
            "description": "Tense and release muscle groups to relieve physical stress.",
            "category": "breathing",
            "icon": "💆",
        },
    ]


def _sleep_hygiene_tips() -> list[dict]:
    return [
        {
            "title": "Sleep Hygiene Basics",
            "description": "Consistent schedule, dark room, no screens 1 hour before bed.",
            "category": "sleep",
            "icon": "😴",
        },
        {
            "title": "Evening Wind-Down Routine",
            "description": "Light stretching and journaling to signal your body it's time to sleep.",
            "category": "sleep",
            "icon": "🌙",
        },
        {
            "title": "Limit Caffeine After Noon",
            "description": "Caffeine has a 6-hour half-life — avoid it after midday for better sleep.",
            "category": "nutrition",
            "icon": "☕",
        },
    ]


def _growth_resources() -> list[dict]:
    return [
        {
            "title": "Start a Habit Tracker",
            "description": "Leverage your high energy to build positive habits today.",
            "category": "growth",
            "icon": "🌱",
        },
        {
            "title": "Gratitude Journaling",
            "description": "Write three things you're grateful for to amplify positive feelings.",
            "category": "journaling",
            "icon": "📓",
        },
        {
            "title": "Connect With Someone",
            "description": "Reach out to a friend or family member — social bonds reinforce wellbeing.",
            "category": "social",
            "icon": "🤝",
        },
        {
            "title": "Try a New Physical Activity",
            "description": "High mood is a great time to try yoga, dancing, or a nature walk.",
            "category": "exercise",
            "icon": "🏃",
        },
    ]


def _general_wellness() -> list[dict]:
    return [
        {
            "title": "Daily Mood Check-In",
            "description": "Log your mood daily to spot patterns and improve self-awareness.",
            "category": "general",
            "icon": "📊",
        },
        {
            "title": "5-Minute Mindfulness",
            "description": "A short mindfulness exercise you can do anywhere, anytime.",
            "category": "meditation",
            "icon": "🧠",
        },
        {
            "title": "Hydration Reminder",
            "description": "Drink enough water — even mild dehydration affects mood and focus.",
            "category": "nutrition",
            "icon": "💧",
        },
        {
            "title": "Take a Short Walk",
            "description": "10 minutes of walking outdoors boosts mood and reduces stress.",
            "category": "exercise",
            "icon": "🚶",
        },
    ]
