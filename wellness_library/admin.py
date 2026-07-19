from django.contrib import admin

from .models import Resource

from django import forms


class ResourceAdminForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = "__all__"


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    form = ResourceAdminForm
    list_display = ["title", "category", "mood_min", "mood_max", "is_active", "created_at"]
    list_filter = ["category", "is_active"]
    search_fields = ["title", "description"]
    list_editable = ["is_active"]
