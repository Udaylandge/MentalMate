from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password is not None:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email=email, password=password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email=email, password=password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Phase 2: Use email as the login identifier.
    """

    # unused but kept for AbstractUser compatibility
    username = models.CharField(max_length=150, blank=True)

    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = CustomUserManager()

    def __str__(self) -> str:
        return self.email


class EmailVerification(models.Model):
    user = models.ForeignKey("authentication.CustomUser", on_delete=models.CASCADE, related_name="email_verifications")
    token = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"EmailVerification(user={self.user_id}, used={self.used})"
