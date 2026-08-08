from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from documents.models import Document

from .services import search_pages


@login_required
@require_GET
def search(request):
    query = request.GET.get("q", "").strip()
    department = request.GET.get("department", "").strip()
    status = request.GET.get("status", "")
    sensitivity = request.GET.get("sensitivity", "")
    if status not in Document.Status.values:
        status = ""
    if sensitivity not in Document.Sensitivity.values:
        sensitivity = ""

    results = []
    if query:
        seen_documents = set()
        for result in search_pages(
            user=request.user,
            query_text=query,
            department=department,
            status=status,
            sensitivity=sensitivity,
        ):
            if result.document_id not in seen_documents:
                results.append(result)
                seen_documents.add(result.document_id)

    return render(
        request,
        "search/results.html",
        {
            "query": query,
            "results": results,
            "statuses": Document.Status.choices,
            "sensitivities": Document.Sensitivity.choices,
            "selected_status": status,
            "selected_sensitivity": sensitivity,
            "department": department,
        },
    )
