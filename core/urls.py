from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"mood", views.MoodEntryViewSet, basename="mood")
router.register(r"journal", views.JournalEntryViewSet, basename="journal")
router.register(r"resources", views.ResourceViewSet, basename="resource")

urlpatterns = [
    # Authentication
    path("", views.home, name="home"),
    path("healthcheck/", views.healthcheck, name="healthcheck"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("verify-email/<str:token>/", views.verify_email, name="verify-email"),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="auth/password_reset_form.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"), name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-reset-complete/", auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), name="password_reset_complete"),

    # Admin Panel
    path("admin-panel/", views.AdminDashboardView.as_view(), name="admin-panel"),
    path("admin-panel/users/", views.AdminUserListView.as_view(), name="admin-panel-users"),
    path("admin-panel/resources/", views.AdminResourceListView.as_view(), name="admin-panel-resources"),
    
    # Analytics
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    
    # API
    path("api/v1/", include(router.urls)),
    
    # Journal
    path("journal/", views.JournalEntryListView.as_view(), name="journal-list"),
    path("journal/new/", views.JournalEntryCreateView.as_view(), name="journal-new"),
    path("journal/<int:pk>/edit/", views.JournalEntryUpdateView.as_view(), name="journal-edit"),
    path("journal/<int:pk>/delete/", views.JournalEntryDeleteView.as_view(), name="journal-delete"),
    
    # Mood Tracking & Dashboard
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("mood/", views.MoodEntryListView.as_view(), name="mood-list"),
    path("mood/new/", views.MoodEntryCreateView.as_view(), name="mood-new"),
    path("mood/<int:pk>/edit/", views.MoodEntryUpdateView.as_view(), name="mood-edit"),
    path("mood/<int:pk>/delete/", views.MoodEntryDeleteView.as_view(), name="mood-delete"),
    
    # Notifications
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:pk>/read/", views.MarkReadView.as_view(), name="notification-mark-read"),
    path("notifications/mark-all-read/", views.MarkAllReadView.as_view(), name="notifications-mark-all-read"),
    
    # Recommendations
    path("recommendations/", views.RecommendationsView.as_view(), name="recommendations"),
    
    # Reports
    path("reports/", views.ReportListView.as_view(), name="report-list"),
    path("reports/weekly/", views.WeeklyReportView.as_view(), name="report-weekly"),
    path("reports/monthly/", views.MonthlyReportView.as_view(), name="report-monthly"),
    path("reports/export/weekly/", views.ExportWeeklyCSVView.as_view(), name="report-export-weekly"),
    path("reports/export/monthly/", views.ExportMonthlyCSVView.as_view(), name="report-export-monthly"),
    
    # Wellness Library
    path("wellness/", views.WellnessLibraryView.as_view(), name="wellness-list"),
    path("wellness/<int:pk>/", views.ResourceDetailView.as_view(), name="wellness-detail"),
]
