from __future__ import annotations

from datetime import date

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .models import MoodEntry
from .services import (
    create_mood_entry,
    delete_mood_entry,
    get_entries_this_month_count,
    get_streak_today_only,
    get_today_mood,
    get_user_mood_entry,
    get_weekly_average,
    list_user_mood_entries,
    update_mood_entry,
)


class MoodEntryForm(forms.Form):
    entry_date = forms.DateField(required=True, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    mood_score = forms.IntegerField(required=True, min_value=1, max_value=10, widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 10}))
    energy = forms.IntegerField(required=False, min_value=1, max_value=10, widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 10, "placeholder": "1-10 (optional)"}))
    stress = forms.IntegerField(required=False, min_value=1, max_value=10, widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 10, "placeholder": "1-10 (optional)"}))
    sleep_hours = forms.FloatField(required=False, min_value=0, max_value=24, widget=forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 24, "step": "0.5", "placeholder": "Hours (optional)"}))
    notes = forms.CharField(required=False, max_length=500, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Any notes about your day... (optional)"}))


@method_decorator(login_required, name="dispatch")
class MoodEntryListView(View):
    template_name = "mood_tracking/mood_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        entries = list_user_mood_entries(user=request.user)
        return render(request, self.template_name, {"entries": entries})


@method_decorator(login_required, name="dispatch")
class MoodEntryCreateView(View):
    template_name = "mood_tracking/mood_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        form = MoodEntryForm(initial={"entry_date": date.today()})
        return render(request, self.template_name, {"form": form, "mode": "create"})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = MoodEntryForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "create"})

        try:
            create_mood_entry(
                user=request.user,
                entry_date=form.cleaned_data["entry_date"],
                mood_score=form.cleaned_data["mood_score"],
                energy=form.cleaned_data.get("energy"),
                stress=form.cleaned_data.get("stress"),
                sleep_hours=form.cleaned_data.get("sleep_hours"),
                notes=form.cleaned_data.get("notes", ""),
            )
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "mode": "create"})

        messages.success(request, "Mood entry saved!")
        return redirect("mood-list")


@method_decorator(login_required, name="dispatch")
class MoodEntryUpdateView(View):
    template_name = "mood_tracking/mood_form.html"

    def get_object(self, request: HttpRequest, pk: int) -> MoodEntry:
        return get_object_or_404(MoodEntry, pk=pk, user=request.user)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        form = MoodEntryForm(initial={
            "entry_date": entry.entry_date,
            "mood_score": entry.mood_score,
            "energy": entry.energy,
            "stress": entry.stress,
            "sleep_hours": entry.sleep_hours,
            "notes": entry.notes,
        })
        return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        form = MoodEntryForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

        try:
            update_mood_entry(
                user=request.user,
                mood_entry_id=entry.pk,
                entry_date=form.cleaned_data["entry_date"],
                mood_score=form.cleaned_data["mood_score"],
                energy=form.cleaned_data.get("energy"),
                stress=form.cleaned_data.get("stress"),
                sleep_hours=form.cleaned_data.get("sleep_hours"),
                notes=form.cleaned_data.get("notes", ""),
            )
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

        messages.success(request, "Mood entry updated!")
        return redirect("mood-list")


@method_decorator(login_required, name="dispatch")
class MoodEntryDeleteView(View):
    template_name = "mood_tracking/mood_confirm_delete.html"

    def get_object(self, request: HttpRequest, pk: int) -> MoodEntry:
        return get_object_or_404(MoodEntry, pk=pk, user=request.user)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        return render(request, self.template_name, {"entry": entry})

    def post(self, request: HttpRequest, pk: int) -> HttpResponseRedirect:
        entry = self.get_object(request, pk)
        delete_mood_entry(user=request.user, mood_entry_id=entry.pk)
        messages.info(request, "Mood entry deleted.")
        return redirect("mood-list")


@method_decorator(login_required, name="dispatch")
class DashboardView(View):
    template_name = "mood_tracking/dashboard.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        today_entry = get_today_mood(user=request.user)
        weekly_avg = get_weekly_average(user=request.user)
        streak = get_streak_today_only(user=request.user)
        entries_month = get_entries_this_month_count(user=request.user)

        return render(
            request,
            self.template_name,
            {
                "today_entry": today_entry,
                "weekly_avg": weekly_avg,
                "streak": streak,
                "entries_month": entries_month,
            },
        )
