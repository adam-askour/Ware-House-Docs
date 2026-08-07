import hashlib
import shutil
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings
from pypdf import PdfWriter

from documents.models import (
    Document,
    DocumentDepartment,
    DocumentVersion,
    StoredFile,
)
from ocr.models import OcrJob
from ocr.services import has_meaningful_text, process_ocr_job, retry_ocr
from organization.models import Department

pytestmark = pytest.mark.django_db


def pdf_bytes():
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(output)
    return output.getvalue()


def make_job(content):
    user = get_user_model().objects.create_user(
        username="ocr-user", email="ocr@example.com", password="a-secure-password"
    )
    department = Department.objects.create(name="Records", code="records")
    document = Document.objects.create(
        title="Scanned record", status=Document.Status.PROCESSING, created_by=user
    )
    DocumentDepartment.objects.create(document=document, department=department, is_primary=True)
    stored = StoredFile(sha256=hashlib.sha256(content).hexdigest(), size=len(content))
    stored.file.save("original.pdf", ContentFile(content), save=False)
    stored.save()
    version = DocumentVersion.objects.create(
        document=document,
        number=1,
        stored_file=stored,
        original_filename="original.pdf",
        created_by=user,
    )
    return OcrJob.objects.create(version=version), content


def test_meaningful_text_ignores_whitespace_and_short_noise():
    assert not has_meaningful_text(["  page 1  ", "x"])
    assert has_meaningful_text(["", "A sufficiently long machine readable sentence."])


def test_image_pdf_creates_searchable_derivative_and_preserves_original(tmp_path):
    def successful_runner(command, **kwargs):
        shutil.copyfile(command[-2], command[-1])
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with override_settings(MEDIA_ROOT=tmp_path):
        job, original = make_job(pdf_bytes())
        result = process_ocr_job(job.pk, runner=successful_runner)

    assert result.status == OcrJob.Status.SUCCEEDED
    assert result.method == OcrJob.Method.OCR
    assert result.searchable_file_id != result.version.stored_file_id
    assert result.warning
    with result.version.stored_file.file.open("rb") as source:
        assert source.read() == original
    assert list(result.pages.values_list("page_number", flat=True)) == [1]
    result.version.document.refresh_from_db()
    assert result.version.document.status == Document.Status.PUBLISHED


def test_ocr_failure_is_recorded_and_source_is_retained(tmp_path):
    def failed_runner(command, **kwargs):
        return SimpleNamespace(returncode=6, stdout="", stderr="Tesseract language data missing")

    with override_settings(MEDIA_ROOT=tmp_path):
        job, original = make_job(pdf_bytes())
        result = process_ocr_job(job.pk, runner=failed_runner)

    assert result.status == OcrJob.Status.FAILED
    assert "language data" in result.failure_reason
    assert result.searchable_file is None
    with result.version.stored_file.file.open("rb") as source:
        assert source.read() == original
    result.version.document.refresh_from_db()
    assert result.version.document.status == Document.Status.PROCESSING

@pytest.mark.parametrize(
    "pages",
    [
        ["Facture fran\u00e7aise imprim\u00e9e avec un montant total v\u00e9rifiable."],
        [
            "\u062e\u0637\u0627\u0628 \u0625\u062f\u0627\u0631\u064a "
            "\u0639\u0631\u0628\u064a \u0645\u0637\u0628\u0648\u0639 "
            "\u064a\u062d\u062a\u0648\u064a \u0639\u0644\u0649 \u0646\u0635 "
            "\u0648\u0627\u0636\u062d \u0648\u0642\u0627\u0628\u0644 \u0644\u0644\u0628\u062d\u062b."
        ],
        ["Printed English contract with searchable terms and conditions."],
    ],
)
def test_representative_language_text_is_stored_on_its_page(tmp_path, pages):
    with override_settings(MEDIA_ROOT=tmp_path):
        job, _ = make_job(pdf_bytes())
        with patch("ocr.services.extract_page_text", return_value=pages):
            result = process_ocr_job(job.pk)

    assert result.status == OcrJob.Status.SUCCEEDED
    assert result.method == OcrJob.Method.EMBEDDED_TEXT
    assert list(result.pages.values_list("page_number", "text")) == [(1, pages[0])]


def test_failed_job_can_be_explicitly_requeued(django_capture_on_commit_callbacks, tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        job, _ = make_job(pdf_bytes())
        job.status = OcrJob.Status.FAILED
        job.failure_reason = "temporary OCR failure"
        job.save(update_fields=("status", "failure_reason"))

        with patch("ocr.tasks.process_ocr_job_task.delay") as delay:
            with django_capture_on_commit_callbacks(execute=True):
                retried = retry_ocr(job)

    assert retried.status == OcrJob.Status.QUEUED
    assert retried.failure_reason == ""
    assert retried.completed_at is None
    delay.assert_called_once_with(job.pk)


def test_non_failed_job_cannot_be_requeued(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        job, _ = make_job(pdf_bytes())
        with pytest.raises(ValueError, match="Only failed"):
            retry_ocr(job)
