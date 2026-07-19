from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .models import CATEGORY_CHOICES
from .services import list_resources


@method_decorator(login_required, name="dispatch")
class WellnessLibraryView(View):
    template_name = "wellness_library/wellness_list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        category = request.GET.get("category", "")
        keyword = request.GET.get("q", "")

        resources = list_resources(
            category=category or None,
            keyword=keyword or None,
        )

        return render(request, self.template_name, {
            "resources": resources,
            "category": category,
            "keyword": keyword,
            "categories": CATEGORY_CHOICES,
        })

@method_decorator(login_required, name="dispatch")
class ResourceDetailView(View):
    template_name = "wellness_library/wellness_detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        from django.shortcuts import get_object_or_404
        from .models import Resource
        resource = get_object_or_404(Resource, pk=pk, is_active=True)
        return render(request, self.template_name, {"resource": resource})
