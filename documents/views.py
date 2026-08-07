from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from access.policies import AccessPolicy
from audit.models import AuditEvent

from .forms import ManualUploadForm
from .models import Document
from .services import create_manual_document


def _client_ip(request):
    return request.META.get("REMOTE_ADDR") or None


def _accessible_document(request, pk):
    return get_object_or_404(
        AccessPolicy.visible_documents(request.user).prefetch_related("assignments__department"),
        pk=pk,
    )


@login_required
@require_GET
def document_list(request):
    documents = AccessPolicy.visible_documents(request.user).prefetch_related(
        "assignments__department"
    )
    department = request.GET.get("department", "")
    status = request.GET.get("status", "")
    if department:
        documents = documents.filter(assignments__department__code=department)
    if status in Document.Status.values:
        documents = documents.filter(status=status)
    return render(
        request,
        "documents/document_list.html",
        {"documents": documents.distinct(), "statuses": Document.Status.choices},
    )


@login_required
@require_http_methods(["GET", "POST"])
def manual_upload(request):
    form = ManualUploadForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        document = create_manual_document(
            user=request.user,
            title=form.cleaned_data["title"],
            department=form.cleaned_data["department"],
            upload=form.cleaned_data["file"],
            sensitivity=form.cleaned_data["sensitivity"],
            label=form.cleaned_data["confidential_label"],
            ip=_client_ip(request),
        )
        return redirect("documents:list") if document else redirect("documents:upload")
    return render(request, "documents/manual_upload.html", {"form": form})


def _serve(request, pk, *, attachment):
    document = _accessible_document(request, pk)
    version = document.versions.select_related("stored_file").first()
    if version is None:
        return get_object_or_404(document.versions, pk=None)
    action = AuditEvent.Action.DOWNLOAD if attachment else AuditEvent.Action.VIEW
    AuditEvent.objects.create(
        actor=request.user, document=document, action=action, ip_address=_client_ip(request)
    )
    stored_file = version.stored_file
    if not attachment:
        try:
            if version.ocr_job.searchable_file_id:
                stored_file = version.ocr_job.searchable_file
        except version._meta.model.ocr_job.RelatedObjectDoesNotExist:
            pass
    response = FileResponse(
        stored_file.file.open("rb"),
        content_type="application/pdf",
        as_attachment=attachment,
        filename=Path(version.original_filename).name,
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


@login_required
@require_GET
def preview(request, pk):
    return _serve(request, pk, attachment=False)


@login_required
@require_GET
def download(request, pk):
    return _serve(request, pk, attachment=True)
