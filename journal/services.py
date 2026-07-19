from __future__ import annotations

import re
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import JournalEntry

User = get_user_model()


_SCRIPT_BLOCK_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
_SCRIPT_TAG_RE = re.compile(r"<script\b[^>]*>", re.IGNORECASE)
_TEMPLATE_EXPR_REPLACEMENTS = {
    "{{": "&#123;&#123;",
    "}}": "&#125;&#125;",
}


def sanitize_journal_text(text: str) -> str:
    """
    Phase 4 journal sanitization (server-side).
    - Strip <script> blocks/tags
    - Neutralize template-injection patterns like {{ }}
    """
    if text is None:
        return ""

    # Remove full script blocks.
    cleaned = _SCRIPT_BLOCK_RE.sub("", text)
    # Remove standalone script opening tags (rare after block removal).
    cleaned = _SCRIPT_TAG_RE.sub("", cleaned)

    # Neutralize template-injection sequences.
    for k, v in _TEMPLATE_EXPR_REPLACEMENTS.items():
        cleaned = cleaned.replace(k, v)

    return cleaned


def validate_journal_text(text: str) -> None:
    if text is None:
        raise ValidationError("Journal text is required.")
    if not isinstance(text, str):
        raise ValidationError("Journal text must be a string.")
    if len(text) == 0:
        raise ValidationError("Journal text cannot be empty.")


@transaction.atomic
def create_journal_entry(*, user: User, text: str) -> JournalEntry:
    validate_journal_text(text)
    cleaned = sanitize_journal_text(text)

    if len(cleaned) > 5000:
        raise ValidationError("Journal entry is too long.")

    return JournalEntry.objects.create(user=user, text=cleaned)


@transaction.atomic
def update_journal_entry(*, user: User, entry_id: int, text: str) -> JournalEntry:
    if entry_id is None:
        raise ValidationError("Journal entry id is required.")
    validate_journal_text(text)

    cleaned = sanitize_journal_text(text)
    if len(cleaned) > 5000:
        raise ValidationError("Journal entry is too long.")

    entry = JournalEntry.objects.select_for_update().get(pk=entry_id, user=user)
    entry.text = cleaned
    entry.save(update_fields=["text"])
    return entry


def delete_journal_entry(*, user: User, entry_id: int) -> None:
    JournalEntry.objects.filter(pk=entry_id, user=user).delete()


def search_journal_entries(*, user: User, keyword: str) -> List[JournalEntry]:
    if keyword is None:
        keyword = ""
    if not isinstance(keyword, str):
        raise ValidationError("Keyword must be a string.")

    # Simple case-insensitive substring match on stored (sanitized) text.
    qs = JournalEntry.objects.filter(user=user)
    if keyword.strip():
        qs = qs.filter(text__icontains=keyword.strip())
    return list(qs.order_by("-created_at"))
