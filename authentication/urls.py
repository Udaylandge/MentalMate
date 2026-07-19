from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("healthcheck/", views.healthcheck, name="healthcheck"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("verify-email/<str:token>/", views.verify_email, name="verify-email"),
    
    # Password Reset
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="auth/password_reset_form.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"), name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), name="password_reset_complete"),
]
