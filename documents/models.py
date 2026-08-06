import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from organization.models import Department


def protected_upload_path(instance, filename):
    suffix = ".pdf"
    return f"originals/{uuid.uuid4().hex[:2]}/{uuid.uuid4().hex}{suffix}"


class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PROCESSING = "processing", "Processing"
        PUBLISHED = "published", "Published"
        QUARANTINED = "quarantined", "Quarantined"

    class Sensitivity(models.TextChoices):
        NORMAL = "normal", "Normal"
        SUPERVISOR = "supervisor", "Supervisor"
        CONFIDENTIAL = "confidential", "Chief only"

    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    sensitivity = models.CharField(
        max_length=20, choices=Sensitivity.choices, default=Sensitivity.NORMAL
    )
    confidential_label = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_documents"
    )
    departments = models.ManyToManyField(Department, through="DocumentDepartment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-pk")

    def clean(self):
        if self.sensitivity == self.Sensitivity.CONFIDENTIAL and not self.confidential_label.strip():
            raise ValidationError({"confidential_label": "A confidential label is required."})
        if self.sensitivity != self.Sensitivity.CONFIDENTIAL and self.confidential_label:
            raise ValidationError(
                {"confidential_label": "Only chief-only documents can have a label."}
            )
        if (
            self.pk
            and self.status == self.Status.PUBLISHED
            and not self.assignments.filter(is_primary=True).exists()
        ):
            raise ValidationError({"status": "Published documents require one primary department."})

    def __str__(self):
        return self.title


class DocumentDepartment(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="assignments")
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("document", "department"), name="unique_document_department"
            ),
            models.UniqueConstraint(
                fields=("document",),
                condition=Q(is_primary=True),
                name="one_primary_department_per_document",
            ),
        ]


class DocumentMetadata(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="metadata")
    key = models.CharField(max_length=100)
    value = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("document", "key"), name="unique_document_metadata_key")
        ]


class StoredFile(models.Model):
    file = models.FileField(upload_to=protected_upload_path, max_length=255)
    sha256 = models.CharField(max_length=64, db_index=True)
    size = models.PositiveBigIntegerField()
    media_type = models.CharField(max_length=100, default="application/pdf")
    created_at = models.DateTimeField(auto_now_add=True)


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField()
    stored_file = models.OneToOneField(StoredFile, on_delete=models.PROTECT)
    original_filename = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-number",)
        constraints = [
            models.UniqueConstraint(fields=("document", "number"), name="unique_document_version")
        ]


class DocumentStatusEvent(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="status_events")
    status = models.CharField(max_length=20, choices=Document.Status.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "pk")
