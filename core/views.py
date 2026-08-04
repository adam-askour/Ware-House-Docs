from django.contrib.auth.decorators import login_required
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@login_required
@require_GET
def home(request):
    """Authenticated landing page until the Phase 2 document list replaces it."""
    return render(request, "core/home.html")


@require_GET
@never_cache
def health(request):
    """Non-sensitive liveness endpoint; never returns infrastructure details."""
    return JsonResponse({"status": "ok"})


@require_GET
@never_cache
def readiness(request):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})
