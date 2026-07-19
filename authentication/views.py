from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import View
from django import forms

from .services import create_email_verification, is_user_verified, register_user, validate_password_strength, verify_email_token

User = get_user_model()


class RegisterForm(forms.Form):
    email = forms.EmailField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password_strength(password)
        return password


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)


class VerifyEmailForm(forms.Form):
    token = forms.CharField(max_length=128)


def home(request):
    return render(request, "home.html")


def healthcheck(request):
    """
    Basic health endpoint for Phase 1 verification.
    """
    return JsonResponse({"status": "ok"})


class RegisterView(View):
    template_name = "auth/register.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        try:
            user = register_user(email=form.cleaned_data["email"], password=form.cleaned_data["password"])
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, self.template_name, {"form": form})

        from django.utils.safestring import mark_safe
        from .models import EmailVerification
        ev = EmailVerification.objects.filter(user=user, used=False).latest('created_at')
        verify_url = request.build_absolute_uri(reverse('verify-email', args=[ev.token]))
        
        print(f"\n[{user.email}] VERIFICATION LINK (Dev Mode): {verify_url}\n")
        
        # Dev behavior: we don't send real email body in Phase 2 skeleton; verification token exists in DB.
        # A full email template/sending will be added in later phases.
        msg = mark_safe(f"Registration successful. For local testing, <a href='{verify_url}' class='alert-link'>click here to verify your email</a>.")
        messages.success(request, msg)
        return redirect("login")


class LoginView(View):
    template_name = "auth/login.html"

    def get(self, request):
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]

        user = authenticate(request, username=email, password=password)
        if user is None:
            form.add_error(None, "Invalid email or password.")
            return render(request, self.template_name, {"form": form})

        if not is_user_verified(user):
            form.add_error(None, "Please verify your email before logging in.")
            return render(request, self.template_name, {"form": form})

        login(request, user)
        return redirect("profile")


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect("home")


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    template_name = "auth/profile.html"

    def get(self, request):
        return render(request, self.template_name, {"user": request.user})


@require_http_methods(["GET"])
def verify_email(request, token: str):
    try:
        verify_email_token(token=token)
    except Exception:
        # Tests expect two different substrings:
        # - invalid token: "Invalid or expired verification token"
        # - expired token: "expired verification token"
        #
        # Our service raises "Invalid or expired verification token." for invalid tokens,
        # and "This verification token has expired." for expired ones.
        messages.error(request, "Invalid or expired verification token")
        return redirect("login")

    return redirect("login")
