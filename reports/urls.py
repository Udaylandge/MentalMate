from django.urls import path
from . import views

urlpatterns = [
    path("reports/", views.ReportListView.as_view(), name="report-list"),
    path("reports/weekly/", views.WeeklyReportView.as_view(), name="report-weekly"),
    path("reports/monthly/", views.MonthlyReportView.as_view(), name="report-monthly"),
    path("reports/export/weekly/", views.ExportWeeklyCSVView.as_view(), name="report-export-weekly"),
    path("reports/export/monthly/", views.ExportMonthlyCSVView.as_view(), name="report-export-monthly"),
]
