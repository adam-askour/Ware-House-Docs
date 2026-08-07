import hashlib
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction

from audit.models import AuditEvent
from documents.models import (
    Document,
    DocumentDepartment,
    DocumentStatusEvent,
    DocumentVersion,
    StoredFile,
)
from documents.services import validate_pdf
from organization.models import Membership

from .models import IngestionRecord


def file_is_stable(path, *, minimum_age_seconds, now_timestamp):
    """A scanner file is consumable only after it has stopped changing for a safe interval."""
    path = Path(path)
    if not path.is_file():
        return False
    stat = path.stat()
    return stat.st_size > 0 and now_timestamp - stat.st_mtime >= minimum_age_seconds


def _quarantine(record, content, reason):
    record.state = IngestionRecord.State.QUARANTINED
    record.failure_reason = reason
    record.size = len(content)
    record.sha256 = hashlib.sha256(content).hexdigest() if content else ""
    if content:
        record.source_file.save(record.original_filename, ContentFile(content), save=False)
    record.save()
    return record


@transaction.atomic
def ingest_scan(*, scanner, employee_code, upload, scanned_at, idempotency_key):
    """Import one completed scanner event exactly once and route it from its employee code."""
    record, created = IngestionRecord.objects.select_for_update().get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "scanner": scanner,
            "original_filename": Path(upload.name).name[:255],
            "scanned_at": scanned_at,
        },
    )
    if not created:
        return record

    record.attempts = 1
    content = upload.read()
    checksum = hashlib.sha256(content).hexdigest()

    if not scanner.is_active:
        return _quarantine(record, content, "Scanner is inactive.")

    user = (
        get_user_model().objects.filter(scanner_code=employee_code, is_active=True).first()
        if employee_code
        else None
    )
    if user is None:
        return _quarantine(record, content, "Employee scan code is unknown or inactive.")
    record.employee = user

    memberships = list(
        Membership.objects.select_related("department").filter(
            user=user, is_active=True, department__is_active=True
        )
    )
    if len(memberships) != 1:
        return _quarantine(
            record,
            content,
            "Employee must have exactly one active department for automatic routing.",
        )
    department = memberships[0].department
    record.department = department

    duplicate = IngestionRecord.objects.filter(
        sha256=checksum, state=IngestionRecord.State.PROCESSED
    ).first()
    if duplicate:
        record.sha256 = checksum
        record.size = len(content)
        record.state = IngestionRecord.State.DUPLICATE
        record.duplicate_of = duplicate
        record.save()
        return record

    try:
        validate_pdf(ContentFile(content, name=record.original_filename))
    except ValidationError as exc:
        return _quarantine(record, content, "; ".join(exc.messages))

    record.state = IngestionRecord.State.PROCESSING
    record.sha256 = checksum
    record.size = len(content)
    record.save()

    document = Document.objects.create(
        title=Path(record.original_filename).stem[:255] or "Scanned document",
        status=Document.Status.PROCESSING,
        sensitivity=Document.Sensitivity.NORMAL,
        created_by=user,
    )
    DocumentDepartment.objects.create(document=document, department=department, is_primary=True)
    stored = StoredFile(sha256=checksum, size=len(content), media_type="application/pdf")
    stored.file.save(record.original_filename, ContentFile(content), save=False)
    stored.save()
    version = DocumentVersion.objects.create(
        document=document,
        number=1,
        stored_file=stored,
        original_filename=record.original_filename,
        created_by=user,
    )
    DocumentStatusEvent.objects.create(
        document=document, status=Document.Status.PROCESSING, actor=user
    )
    AuditEvent.objects.create(actor=user, document=document, action=AuditEvent.Action.UPLOAD)
    record.document = document
    record.state = IngestionRecord.State.PROCESSED
    record.save()
    from ocr.services import queue_ocr

    queue_ocr(version)
    return record
