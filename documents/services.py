import hashlib

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from audit.models import AuditEvent

from .models import Document, DocumentDepartment, DocumentStatusEvent, DocumentVersion, StoredFile


def validate_pdf(upload):
    upload.seek(0)
    if upload.read(5) != b"%PDF-":
        raise ValidationError("The uploaded file is not a PDF.")
    upload.seek(0)
    try:
        reader = PdfReader(upload, strict=True)
        if reader.is_encrypted:
            raise ValidationError("Encrypted or password-protected PDFs are not accepted.")
        len(reader.pages)
    except ValidationError:
        raise
    except (PdfReadError, ValueError, OSError) as exc:
        raise ValidationError("The PDF is corrupt or cannot be read.") from exc
    finally:
        upload.seek(0)


@transaction.atomic
def create_manual_document(*, user, title, department, upload, sensitivity, label="", ip=None):
    validate_pdf(upload)
    content = upload.read()
    checksum = hashlib.sha256(content).hexdigest()
    document = Document.objects.create(
        title=title,
        status=Document.Status.DRAFT,
        sensitivity=sensitivity,
        confidential_label=label.strip(),
        created_by=user,
    )
    document.full_clean()
    DocumentDepartment.objects.create(document=document, department=department, is_primary=True)
    stored = StoredFile(sha256=checksum, size=len(content), media_type="application/pdf")
    stored.file.save(upload.name, ContentFile(content), save=False)
    stored.save()
    DocumentVersion.objects.create(
        document=document,
        number=1,
        stored_file=stored,
        original_filename=upload.name,
        created_by=user,
    )
    document.status = Document.Status.PUBLISHED
    document.full_clean()
    document.save(update_fields=("status", "updated_at"))
    DocumentStatusEvent.objects.create(document=document, status=document.status, actor=user)
    AuditEvent.objects.create(
        actor=user, document=document, action=AuditEvent.Action.UPLOAD, ip_address=ip
    )
    return document
