from __future__ import annotations

from typing import List, Optional

from .models import Resource


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
