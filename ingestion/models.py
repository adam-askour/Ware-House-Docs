import uuid

from django.conf import settings
from django.db import models


class Scanner(models.Model):
    identifier = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


def source_upload_path(instance, filename):
    return f"ingestion/{instance.state}/{uuid.uuid4().hex}.pdf"


class IngestionRecord(models.Model):
    class State(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"
        QUARANTINED = "quarantined", "Quarantined"
        DUPLICATE = "duplicate", "Duplicate"

    idempotency_key = models.CharField(max_length=128, unique=True)
    scanner = models.ForeignKey(Scanner, on_delete=models.PROTECT, related_name="ingestions")
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="scan_ingestions",
        null=True,
        blank=True,
    )
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.PROTECT,
        related_name="scan_ingestions",
        null=True,
        blank=True,
    )
    document = models.OneToOneField(
        "documents.Document",
        on_delete=models.PROTECT,
        related_name="ingestion",
        null=True,
        blank=True,
    )
    duplicate_of = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="duplicates"
    )
    source_file = models.FileField(upload_to=source_upload_path, max_length=255, blank=True)
    original_filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    size = models.PositiveBigIntegerField(default=0)
    scanned_at = models.DateTimeField()
    state = models.CharField(max_length=20, choices=State.choices, default=State.RECEIVED)
    failure_reason = models.CharField(max_length=255, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-pk")

    def __str__(self):
        return f"{self.scanner.identifier}: {self.original_filename} ({self.state})"

