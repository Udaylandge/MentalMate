"""api/views.py — Phase 12: DRF ViewSets for mood, journal, and resources."""
from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from mood_tracking.models import MoodEntry
from journal.models import JournalEntry
from journal.services import create_journal_entry, update_journal_entry
from wellness_library.models import Resource
from mood_tracking.services import create_mood_entry, update_mood_entry

from .serializers import JournalEntrySerializer, MoodEntrySerializer, ResourceSerializer


class MoodEntryViewSet(viewsets.ModelViewSet):
    """
    CRUD for the current user's mood entries.
    GET /api/mood/        — list
    POST /api/mood/       — create
    GET /api/mood/{id}/   — retrieve
    PUT/PATCH /api/mood/{id}/ — update
    DELETE /api/mood/{id}/ — delete
    """
    serializer_class = MoodEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MoodEntry.objects.filter(user=self.request.user).order_by("-entry_date")

    def perform_create(self, serializer):
        data = serializer.validated_data
        try:
            entry = create_mood_entry(
                user=self.request.user,
                entry_date=data["entry_date"],
                mood_score=data["mood_score"],
                energy=data.get("energy"),
                stress=data.get("stress"),
                sleep_hours=data.get("sleep_hours"),
                notes=data.get("notes", ""),
            )
            serializer.instance = entry
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))

    def perform_update(self, serializer):
        data = serializer.validated_data
        try:
            entry = update_mood_entry(
                user=self.request.user,
                mood_entry_id=self.get_object().pk,
                entry_date=data["entry_date"],
                mood_score=data["mood_score"],
                energy=data.get("energy"),
                stress=data.get("stress"),
                sleep_hours=data.get("sleep_hours"),
                notes=data.get("notes", ""),
            )
            serializer.instance = entry
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))


class JournalEntryViewSet(viewsets.ModelViewSet):
    """CRUD for current user's journal entries."""
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        try:
            entry = create_journal_entry(user=self.request.user, text=serializer.validated_data["text"])
            serializer.instance = entry
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))

    def perform_update(self, serializer):
        try:
            entry = update_journal_entry(
                user=self.request.user,
                entry_id=self.get_object().pk,
                text=serializer.validated_data["text"],
            )
            serializer.instance = entry
        except Exception as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))


class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to active wellness resources. Write via Django admin."""
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Resource.objects.filter(is_active=True).order_by("category", "title")

    def get_queryset(self):
        qs = Resource.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        keyword = self.request.query_params.get("q")
        if category:
            qs = qs.filter(category=category)
        if keyword:
            qs = qs.filter(title__icontains=keyword) | Resource.objects.filter(
                is_active=True, description__icontains=keyword
            )
            if category:
                qs = qs.filter(category=category)
        return qs.distinct().order_by("category", "title")
