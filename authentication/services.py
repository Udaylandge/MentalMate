from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string

from .models import EmailVerification

User = get_user_model()


def validate_password_strength(password: str) -> None:
    """
    Server-side password strength validation (Phase 2 requirement).
    Rules are intentionally simple for capstone baseline.
    """
    if not isinstance(password, str):
        raise ValidationError("Invalid password type.")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    # Require at least 1 letter and 1 number.
    has_alpha = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_alpha and has_digit):
        raise ValidationError("Password must include both letters and numbers.")


def create_email_verification(*, user: User, ttl_minutes: int = 60 * 24) -> EmailVerification:
    token = get_random_string(length=48)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ttl_minutes)

    ev = EmailVerification.objects.create(
        user=user,
        token=token,
        created_at=now,
        expires_at=expires_at,
        used=False,
    )
    return ev


def register_user(*, email: str, password: str) -> User:
    """
    Create a new user and issue an email verification token.
    Login will be blocked until email is verified (per requirement).
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required.")

    normalized_email = email.strip().lower()
    if len(normalized_email) > 254 or "@" not in normalized_email:
        raise ValidationError("Enter a valid email address.")

    validate_password_strength(password)

    # Django User model already enforces unique constraints; handle friendly error.
    if User.objects.filter(email__iexact=normalized_email).exists():
        raise ValidationError("A user with this email already exists.")

    user = User.objects.create_user(email=normalized_email, password=password, is_active=True)
    create_email_verification(user=user)
    return user


def verify_email_token(*, token: str) -> User:
    if not token or not isinstance(token, str):
        raise ValidationError("Invalid token.")

    try:
        ev = EmailVerification.objects.select_related("user").get(token=token)
    except EmailVerification.DoesNotExist as exc:
        raise ValidationError("Invalid or expired verification token.") from exc

    now = datetime.now(timezone.utc)
    if ev.used:
        raise ValidationError("This verification token has already been used.")
    if ev.expires_at <= now:
        raise ValidationError("This verification token has expired.")

    ev.used = True
    ev.save(update_fields=["used"])

    user = ev.user
    user.is_active = True
    # store verification state via user flag on profile/auth model later.
    # For now use a boolean on EmailVerification only; for gating login use ev.used status via helper.
    return user


def is_user_verified(user: User) -> bool:
    # A user is considered verified if any unused token was never used;
    # For Phase 2, we treat verified if there exists a used token and no active unused token.
    # Simpler: there is an EmailVerification record marked used for this user.
    return EmailVerification.objects.filter(user=user, used=True).exists()
