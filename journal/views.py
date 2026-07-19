from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .models import JournalEntry
from .services import create_journal_entry, delete_journal_entry, search_journal_entries, update_journal_entry


class JournalEntryForm(forms.Form):
    text = forms.CharField(
        required=True,
        max_length=5000,
        widget=forms.Textarea(attrs={"rows": 10, "class": "form-control"}),
    )


@method_decorator(login_required, name="dispatch")
class JournalEntryListView(View):
    template_name = "journal/journal_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        keyword = request.GET.get("q", "")
        entries = search_journal_entries(user=request.user, keyword=keyword)
        return render(request, self.template_name, {"entries": entries, "keyword": keyword})


@method_decorator(login_required, name="dispatch")
class JournalEntryCreateView(View):
    template_name = "journal/journal_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        form = JournalEntryForm()
        return render(request, self.template_name, {"form": form, "mode": "create"})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = JournalEntryForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "create"})

        try:
            create_journal_entry(user=request.user, text=form.cleaned_data["text"])
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "mode": "create"})

        messages.success(request, "Journal entry saved.")
        return redirect("journal-list")


@method_decorator(login_required, name="dispatch")
class JournalEntryUpdateView(View):
    template_name = "journal/journal_form.html"

    def get_object(self, request: HttpRequest, pk: int) -> JournalEntry:
        return get_object_or_404(JournalEntry, pk=pk, user=request.user)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        form = JournalEntryForm(initial={"text": entry.text})
        return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        form = JournalEntryForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

        try:
            update_journal_entry(user=request.user, entry_id=entry.pk, text=form.cleaned_data["text"])
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form, "mode": "edit", "entry": entry})

        messages.success(request, "Journal entry updated.")
        return redirect("journal-list")


@method_decorator(login_required, name="dispatch")
class JournalEntryDeleteView(View):
    template_name = "journal/journal_confirm_delete.html"

    def get_object(self, request: HttpRequest, pk: int) -> JournalEntry:
        return get_object_or_404(JournalEntry, pk=pk, user=request.user)

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        entry = self.get_object(request, pk)
        return render(request, self.template_name, {"entry": entry})

    def post(self, request: HttpRequest, pk: int) -> HttpResponseRedirect:
        entry = self.get_object(request, pk)
        delete_journal_entry(user=request.user, entry_id=entry.pk)
        messages.info(request, "Journal entry deleted.")
        return redirect("journal-list")
