from rest_framework import serializers

from core.models import MoodEntry, JournalEntry, Resource


class MoodEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodEntry
        fields = ["id", "entry_date", "mood_score", "energy", "stress", "sleep_hours", "notes"]
        read_only_fields = ["id"]

    def validate_mood_score(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError("Mood score must be between 1 and 10.")
        return value

    def validate_energy(self, value):
        if value is not None and not (1 <= value <= 10):
            raise serializers.ValidationError("Energy must be between 1 and 10.")
        return value

    def validate_stress(self, value):
        if value is not None and not (1 <= value <= 10):
            raise serializers.ValidationError("Stress must be between 1 and 10.")
        return value


class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = ["id", "text", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "title", "category", "description", "link", "image_url", "mood_min", "mood_max"]
        read_only_fields = ["id"]
