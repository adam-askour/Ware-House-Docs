from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.db import connection, transaction
from django.db.models import Case, F, FloatField, Q, Value, When

from access.policies import AccessPolicy
from ocr.models import OcrJob

from .models import DocumentSearchPage

SEARCH_CONFIG = "simple"


@transaction.atomic
def rebuild_document_search(document):
    """Replace the document index using OCR output from its latest version."""
    DocumentSearchPage.objects.filter(document=document).delete()
    version = document.versions.order_by("-number").first()
    if version is None:
        return []
    try:
        job = version.ocr_job
    except OcrJob.DoesNotExist:
        return []
    if job.status != OcrJob.Status.SUCCEEDED:
        return []

    metadata_text = " ".join(
        f"{key} {value}" for key, value in document.metadata.values_list("key", "value")
    )
    entries = DocumentSearchPage.objects.bulk_create(
        [
            DocumentSearchPage(
                document=document,
                ocr_page=page,
                page_number=page.page_number,
                title=document.title,
                metadata_text=metadata_text,
                body=page.text,
            )
            for page in job.pages.all()
        ]
    )
    vector = (
        SearchVector("title", weight="A", config=SEARCH_CONFIG)
        + SearchVector("metadata_text", weight="B", config=SEARCH_CONFIG)
        + SearchVector("body", weight="C", config=SEARCH_CONFIG)
    )
    DocumentSearchPage.objects.filter(pk__in=[entry.pk for entry in entries]).update(
        search_vector=vector if connection.vendor == "postgresql" else Value(metadata_text)
    )
    return entries


def search_pages(*, user, query_text, department="", status="", sensitivity=""):
    """Rank page hits after authorization and document filters are applied."""
    visible = AccessPolicy.visible_documents(user)
    if department:
        visible = visible.filter(assignments__department__code=department)
    if status:
        visible = visible.filter(status=status)
    if sensitivity:
        visible = visible.filter(sensitivity=sensitivity)

    if connection.vendor != "postgresql":
        match = (
            Q(title__icontains=query_text)
            | Q(metadata_text__icontains=query_text)
            | Q(body__icontains=query_text)
        )
        return (
            DocumentSearchPage.objects.filter(document__in=visible)
            .filter(match)
            .select_related("document")
            .annotate(
                rank=Case(
                    When(title__icontains=query_text, then=Value(3.0)),
                    When(metadata_text__icontains=query_text, then=Value(2.0)),
                    default=Value(1.0),
                    output_field=FloatField(),
                ),
                snippet=F("body"),
            )
            .order_by("-rank", "document_id", "page_number")
        )

    query = SearchQuery(query_text, config=SEARCH_CONFIG, search_type="plain")
    return (
        DocumentSearchPage.objects.filter(document__in=visible, search_vector=query)
        .select_related("document")
        .annotate(
            rank=SearchRank(F("search_vector"), query),
            snippet=SearchHeadline(
                "body",
                query,
                config=SEARCH_CONFIG,
                start_sel="[[[HIT]]]",
                stop_sel="[[[/HIT]]]",
                max_words=32,
                min_words=12,
                short_word=2,
            ),
        )
        .order_by("-rank", "document_id", "page_number")
    )
