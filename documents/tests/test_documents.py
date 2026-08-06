import hashlib
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.urls import reverse
from pypdf import PdfWriter

from audit.models import AuditEvent
from documents.forms import ManualUploadForm
from documents.models import Document, DocumentDepartment
from documents.services import validate_pdf
from organization.models import Department, Membership

pytestmark = pytest.mark.django_db


def make_user(username):
    return get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="a-secure-password"
    )


def pdf_bytes(*, encrypted=False):
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    if encrypted:
        writer.encrypt("secret")
    writer.write(output)
    return output.getvalue()


def upload(client, department, content=None, **data):
    content = content or pdf_bytes()
    return client.post(
        reverse("documents:upload"),
        {
            "title": "Safety procedure",
            "department": department.pk,
            "sensitivity": Document.Sensitivity.NORMAL,
            "confidential_label": "",
            "file": SimpleUploadedFile("procedure.pdf", content, content_type="application/pdf"),
            **data,
        },
    )


def test_renamed_non_pdf_and_corrupt_pdf_are_rejected():
    for content in (b"this is not a PDF", b"%PDF-1.7\ncorrupt"):
        with pytest.raises(ValidationError):
            validate_pdf(SimpleUploadedFile("renamed.pdf", content))


def test_encrypted_pdf_is_rejected():
    with pytest.raises(ValidationError, match="Encrypted"):
        validate_pdf(SimpleUploadedFile("protected.pdf", pdf_bytes(encrypted=True)))


def test_published_document_requires_primary_department():
    user = make_user("author")
    document = Document.objects.create(title="Draft", created_by=user)
    document.status = Document.Status.PUBLISHED
    with pytest.raises(ValidationError, match="primary department"):
        document.full_clean()


def test_only_one_primary_department_is_allowed():
    user = make_user("author")
    first = Department.objects.create(name="First", code="first")
    second = Department.objects.create(name="Second", code="second")
    document = Document.objects.create(title="Draft", created_by=user)
    DocumentDepartment.objects.create(document=document, department=first, is_primary=True)
    with pytest.raises(IntegrityError), transaction.atomic():
        DocumentDepartment.objects.create(document=document, department=second, is_primary=True)


def test_upload_list_preview_download_and_audit(client, tmp_path):
    user = make_user("employee")
    department = Department.objects.create(name="Operations", code="operations")
    Membership.objects.create(user=user, department=department)
    client.force_login(user)
    original = pdf_bytes()

    with override_settings(MEDIA_ROOT=tmp_path):
        response = upload(client, department, original)
        assert response.status_code == 302
        document = Document.objects.get()
        version = document.versions.select_related("stored_file").get()
        assert version.stored_file.sha256 == hashlib.sha256(original).hexdigest()
        assert version.stored_file.file.read() == original

        listing = client.get(reverse("documents:list"))
        assert b"Safety procedure" in listing.content

        preview = client.get(reverse("documents:preview", args=(document.pk,)))
        assert preview.status_code == 200
        assert b"".join(preview.streaming_content) == original
        assert preview["Cache-Control"] == "private, no-store"

        download = client.get(reverse("documents:download", args=(document.pk,)))
        assert download.status_code == 200
        assert "attachment" in download["Content-Disposition"]
        assert b"".join(download.streaming_content) == original

    assert list(AuditEvent.objects.values_list("action", flat=True)) == [
        AuditEvent.Action.DOWNLOAD,
        AuditEvent.Action.VIEW,
        AuditEvent.Action.UPLOAD,
    ]


def test_unauthorized_user_cannot_discover_preview_or_download(client, tmp_path):
    owner = make_user("owner")
    outsider = make_user("outsider")
    department = Department.objects.create(name="Finance", code="finance")
    Membership.objects.create(user=owner, department=department)
    client.force_login(owner)
    marker = pdf_bytes()
    with override_settings(MEDIA_ROOT=tmp_path):
        upload(client, department, marker)
        document = Document.objects.get()
        client.force_login(outsider)

        listing = client.get(reverse("documents:list"))
        assert document.title.encode() not in listing.content
        for route in ("documents:preview", "documents:download"):
            response = client.get(reverse(route, args=(document.pk,)))
            assert response.status_code == 404
            assert not response.streaming
            assert marker not in response.content
    assert AuditEvent.objects.filter(actor=outsider).count() == 0


def test_chief_only_document_requires_department_chief(client, tmp_path):
    user = make_user("employee")
    department = Department.objects.create(name="People", code="people")
    Membership.objects.create(user=user, department=department)
    client.force_login(user)
    data = {
        "sensitivity": Document.Sensitivity.CONFIDENTIAL,
        "confidential_label": "Payroll",
    }
    with override_settings(MEDIA_ROOT=tmp_path):
        denied = upload(client, department, **data)
        assert denied.status_code == 200
        assert Document.objects.count() == 0

        membership = Membership.objects.get(user=user, department=department)
        membership.role = Membership.Role.CHIEF
        membership.save(update_fields=("role",))
        accepted = upload(client, department, **data)
        assert accepted.status_code == 302
        assert b"Safety procedure" in client.get(reverse("documents:list")).content


def test_ordinary_employee_is_not_offered_confidential_classification(client):
    user = make_user("ordinary")
    department = Department.objects.create(name="Warehouse", code="warehouse")
    Membership.objects.create(user=user, department=department)

    form = ManualUploadForm(user=user)
    assert form.fields["sensitivity"].choices == [(Document.Sensitivity.NORMAL, "Normal")]

    client.force_login(user)
    response = client.get(reverse("documents:upload"))
    assert response.status_code == 200
    assert b'value="confidential"' not in response.content


def test_supervisor_and_chief_are_offered_their_classification_levels():
    user = make_user("supervisor")
    department = Department.objects.create(name="Legal", code="legal")
    membership = Membership.objects.create(
        user=user, department=department, role=Membership.Role.SUPERVISOR
    )

    form = ManualUploadForm(user=user)
    assert (Document.Sensitivity.SUPERVISOR, "Supervisor") in form.fields["sensitivity"].choices
    assert (Document.Sensitivity.CONFIDENTIAL, "Chief only") not in form.fields["sensitivity"].choices

    membership.role = Membership.Role.CHIEF
    membership.save(update_fields=("role",))
    form = ManualUploadForm(user=user)
    assert (Document.Sensitivity.CONFIDENTIAL, "Chief only") in form.fields["sensitivity"].choices
