import os
import time
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from pypdf import PdfWriter

from documents.models import Document
from ingestion.models import IngestionRecord, Scanner
from ingestion.services import file_is_stable, ingest_scan
from organization.models import Department, Membership

pytestmark = pytest.mark.django_db


def pdf_bytes():
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(output)
    return output.getvalue()


def make_user(username, *, scanner_code="123456", is_active=True):
    return get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="a-secure-password",
        scanner_code=scanner_code,
        is_active=is_active,
    )


def submit(scanner, code, *, key="event-1", content=None):
    return ingest_scan(
        scanner=scanner,
        employee_code=code,
        upload=SimpleUploadedFile("scan.pdf", content or pdf_bytes()),
        scanned_at=timezone.now(),
        idempotency_key=key,
    )


def test_shared_scanner_routes_from_employee_code_not_scanner_location(tmp_path):
    employee = make_user("amina")
    finance = Department.objects.create(name="Finance", code="finance")
    hr = Department.objects.create(name="Human Resources", code="hr")
    Membership.objects.create(user=employee, department=hr)
    scanner = Scanner.objects.create(
        identifier="finance-floor", name="Finance floor scanner", location="Finance"
    )

    with override_settings(MEDIA_ROOT=tmp_path):
        record = submit(scanner, employee.scanner_code)

    assert record.state == IngestionRecord.State.PROCESSED
    assert record.department == hr
    assert record.department != finance
    assert record.document.status == Document.Status.PROCESSING
    assert record.document.created_by == employee
    assert record.document.assignments.get(is_primary=True).department == hr


@pytest.mark.parametrize("inactive", [False, True])
def test_unknown_or_inactive_employee_code_is_quarantined(tmp_path, inactive):
    if inactive:
        make_user("inactive", scanner_code="blocked", is_active=False)
    scanner = Scanner.objects.create(identifier="reception", name="Reception")

    with override_settings(MEDIA_ROOT=tmp_path):
        record = submit(scanner, "blocked" if inactive else "unknown")

    assert record.state == IngestionRecord.State.QUARANTINED
    assert "unknown or inactive" in record.failure_reason
    assert record.source_file
    assert Document.objects.count() == 0


def test_ambiguous_department_membership_is_quarantined(tmp_path):
    employee = make_user("multi")
    for name in ("Legal", "Operations"):
        department = Department.objects.create(name=name, code=name.lower())
        Membership.objects.create(user=employee, department=department)
    scanner = Scanner.objects.create(identifier="shared", name="Shared scanner")

    with override_settings(MEDIA_ROOT=tmp_path):
        record = submit(scanner, employee.scanner_code)

    assert record.state == IngestionRecord.State.QUARANTINED
    assert "exactly one active department" in record.failure_reason


def test_repeated_event_is_idempotent_and_exact_duplicate_is_flagged(tmp_path):
    employee = make_user("employee")
    department = Department.objects.create(name="Warehouse", code="warehouse")
    Membership.objects.create(user=employee, department=department)
    scanner = Scanner.objects.create(identifier="warehouse", name="Warehouse scanner")
    content = pdf_bytes()

    with override_settings(MEDIA_ROOT=tmp_path):
        first = submit(scanner, employee.scanner_code, key="same-event", content=content)
        replay = submit(scanner, employee.scanner_code, key="same-event", content=content)
        duplicate = submit(scanner, employee.scanner_code, key="new-event", content=content)

    assert replay.pk == first.pk
    assert duplicate.state == IngestionRecord.State.DUPLICATE
    assert duplicate.duplicate_of == first
    assert Document.objects.count() == 1


def test_corrupt_pdf_is_quarantined(tmp_path):
    employee = make_user("employee")
    department = Department.objects.create(name="Warehouse", code="warehouse")
    Membership.objects.create(user=employee, department=department)
    scanner = Scanner.objects.create(identifier="warehouse", name="Warehouse scanner")

    with override_settings(MEDIA_ROOT=tmp_path):
        record = submit(scanner, employee.scanner_code, content=b"not a pdf")

    assert record.state == IngestionRecord.State.QUARANTINED
    assert "not a PDF" in record.failure_reason


def test_partially_written_or_recent_file_is_not_stable(tmp_path):
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"")
    now = time.time()
    assert not file_is_stable(path, minimum_age_seconds=5, now_timestamp=now)

    path.write_bytes(pdf_bytes())
    os.utime(path, (now, now))
    assert not file_is_stable(path, minimum_age_seconds=5, now_timestamp=now + 1)
    assert file_is_stable(path, minimum_age_seconds=5, now_timestamp=now + 6)


def test_inactive_scanner_is_quarantined(tmp_path):
    employee = make_user("employee")
    department = Department.objects.create(name="Warehouse", code="warehouse")
    Membership.objects.create(user=employee, department=department)
    scanner = Scanner.objects.create(identifier="old", name="Old scanner", is_active=False)

    with override_settings(MEDIA_ROOT=tmp_path):
        record = submit(scanner, employee.scanner_code)

    assert record.state == IngestionRecord.State.QUARANTINED
    assert record.failure_reason == "Scanner is inactive."
