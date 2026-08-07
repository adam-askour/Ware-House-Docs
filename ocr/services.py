import hashlib
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from documents.models import Document, DocumentStatusEvent, StoredFile

from .models import OcrJob, OcrPageText


class OcrProcessingError(Exception):
    pass


def extract_page_text(pdf_source):
    """Return text by page without changing the source stream position."""
    try:
        pdf_source.seek(0)
        reader = PdfReader(pdf_source, strict=False)
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except (PdfReadError, ValueError, OSError) as exc:
        raise OcrProcessingError("The PDF text layer could not be read.") from exc
    finally:
        pdf_source.seek(0)
    return pages


def has_meaningful_text(pages, *, minimum_characters=20):
    return any(len("".join(text.split())) >= minimum_characters for text in pages)


def run_ocrmypdf(source_path, output_path, *, languages, runner=subprocess.run):
    command = [
        "ocrmypdf",
        "--skip-text",
        "--rotate-pages",
        "--deskew",
        "--clean",
        "--optimize",
        "1",
        "--language",
        languages,
        str(source_path),
        str(output_path),
    ]
    try:
        result = runner(command, capture_output=True, text=True, timeout=510, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise OcrProcessingError("OCR engine is unavailable or timed out.") from exc
    if result.returncode != 0 or not output_path.is_file():
        detail = (result.stderr or result.stdout or "OCR engine failed.").strip()
        raise OcrProcessingError(detail[-2000:])


def _store_pages(job, pages):
    job.pages.all().delete()
    OcrPageText.objects.bulk_create(
        [OcrPageText(job=job, page_number=index, text=text) for index, text in enumerate(pages, 1)]
    )


@transaction.atomic
def process_ocr_job(job_id, *, runner=subprocess.run):
    job = OcrJob.objects.select_for_update().select_related(
        "version__stored_file", "version__document", "version__created_by"
    ).get(pk=job_id)
    if job.status == OcrJob.Status.SUCCEEDED:
        return job

    job.status = OcrJob.Status.RUNNING
    job.attempts += 1
    job.started_at = timezone.now()
    job.failure_reason = ""
    job.save(update_fields=("status", "attempts", "started_at", "failure_reason"))
    version = job.version

    try:
        with version.stored_file.file.open("rb") as source:
            existing_pages = extract_page_text(source)
            if has_meaningful_text(existing_pages):
                _store_pages(job, existing_pages)
                job.method = OcrJob.Method.EMBEDDED_TEXT
                job.searchable_file = version.stored_file
            else:
                with tempfile.TemporaryDirectory(prefix="dms-ocr-") as temp_dir:
                    source_path = Path(temp_dir) / "source.pdf"
                    output_path = Path(temp_dir) / "searchable.pdf"
                    source.seek(0)
                    source_path.write_bytes(source.read())
                    run_ocrmypdf(source_path, output_path, languages=job.languages, runner=runner)
                    output = output_path.read_bytes()
                    pages = extract_page_text(ContentFile(output))
                    if not has_meaningful_text(pages):
                        job.warning = "OCR completed, but little or no machine-readable text was found."
                    derivative = StoredFile(
                        sha256=hashlib.sha256(output).hexdigest(),
                        size=len(output),
                        media_type="application/pdf",
                    )
                    derivative.file.save("searchable.pdf", ContentFile(output), save=False)
                    derivative.save()
                    _store_pages(job, pages)
                    job.method = OcrJob.Method.OCR
                    job.searchable_file = derivative
    except OcrProcessingError as exc:
        job.status = OcrJob.Status.FAILED
        job.failure_reason = str(exc)[:4000]
        job.completed_at = timezone.now()
        job.save(update_fields=("status", "failure_reason", "completed_at"))
        return job

    job.status = OcrJob.Status.SUCCEEDED
    job.completed_at = timezone.now()
    job.save(
        update_fields=("status", "method", "searchable_file", "warning", "completed_at")
    )
    document = version.document
    if document.status == Document.Status.PROCESSING:
        document.status = Document.Status.PUBLISHED
        document.full_clean()
        document.save(update_fields=("status", "updated_at"))
        DocumentStatusEvent.objects.create(
            document=document, status=document.status, actor=version.created_by
        )
    return job


def queue_ocr(version):
    job, _ = OcrJob.objects.get_or_create(
        version=version, defaults={"languages": settings.OCR_LANGUAGES}
    )
    from .tasks import process_ocr_job_task

    transaction.on_commit(lambda: process_ocr_job_task.delay(job.pk))
    return job
