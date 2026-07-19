from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", include("core.urls")),
    
    # PWA Routes
    path("manifest.json", TemplateView.as_view(template_name="manifest.json", content_type="application/json"), name="manifest"),
    path("sw.js", TemplateView.as_view(template_name="sw.js", content_type="application/javascript"), name="sw"),
    path("offline/", TemplateView.as_view(template_name="offline.html"), name="offline"),

    path("admin/", admin.site.urls),
]
