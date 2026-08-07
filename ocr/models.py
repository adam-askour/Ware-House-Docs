from django.db import models

from documents.models import DocumentVersion, StoredFile


class OcrJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    class Method(models.TextChoices):
        EMBEDDED_TEXT = "embedded_text", "Existing PDF text"
        OCR = "ocr", "Optical character recognition"

    version = models.OneToOneField(DocumentVersion, on_delete=models.CASCADE, related_name="ocr_job")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    method = models.CharField(max_length=20, choices=Method.choices, blank=True)
    searchable_file = models.ForeignKey(
        StoredFile, on_delete=models.PROTECT, null=True, blank=True, related_name="ocr_derivatives"
    )
    languages = models.CharField(max_length=100, default="eng+fra+ara")
    attempts = models.PositiveIntegerField(default=0)
    warning = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class OcrPageText(models.Model):
    job = models.ForeignKey(OcrJob, on_delete=models.CASCADE, related_name="pages")
    page_number = models.PositiveIntegerField()
    text = models.TextField(blank=True)

    class Meta:
        ordering = ("page_number",)
        constraints = [
            models.UniqueConstraint(fields=("job", "page_number"), name="unique_ocr_job_page")
        ]

