from django import forms
from core.services import validate_password_strength

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


class JournalEntryForm(forms.Form):
    text = forms.CharField(
        required=True,
        max_length=5000,
        widget=forms.Textarea(attrs={"rows": 10, "class": "form-control"}),
    )


class MoodEntryForm(forms.Form):
    entry_date = forms.DateField(required=True, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    mood_score = forms.IntegerField(required=True, min_value=1, max_value=10, widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 10}))
    energy = forms.IntegerField(required=False, min_value=1, max_value=10, widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 10, "placeholder": "1-10 (optional)"}))
    stress = forms.IntegerField(required=False, min_value=1, max_value=10, widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 10, "placeholder": "1-10 (optional)"}))
    sleep_hours = forms.FloatField(required=False, min_value=0, max_value=24, widget=forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 24, "step": "0.5", "placeholder": "Hours (optional)"}))
    notes = forms.CharField(required=False, max_length=500, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Any notes about your day... (optional)"}))
