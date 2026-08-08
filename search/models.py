from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from documents.models import Document
from ocr.models import OcrPageText


class DocumentSearchPage(models.Model):
    """Denormalized, permission-neutral search material for one OCR page."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="search_pages")
    ocr_page = models.OneToOneField(
        OcrPageText, on_delete=models.CASCADE, related_name="search_entry"
    )
    page_number = models.PositiveIntegerField()
    title = models.TextField()
    metadata_text = models.TextField(blank=True)
    body = models.TextField(blank=True)
    search_vector = SearchVectorField(null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("document_id", "page_number")
        indexes = [GinIndex(fields=("search_vector",), name="search_page_vector_gin")]
        constraints = [
            models.UniqueConstraint(
                fields=("document", "page_number"), name="unique_document_search_page"
            )
        ]
