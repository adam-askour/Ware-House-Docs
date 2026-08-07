from django.contrib import admin

from .models import OcrJob, OcrPageText


class OcrPageTextInline(admin.TabularInline):
    model = OcrPageText
    extra = 0
    readonly_fields = ("page_number", "text")


@admin.register(OcrJob)
class OcrJobAdmin(admin.ModelAdmin):
    list_display = ("version", "status", "method", "attempts", "queued_at", "completed_at")
    list_filter = ("status", "method")
    readonly_fields = (
        "version",
        "status",
        "method",
        "searchable_file",
        "attempts",
        "warning",
        "failure_reason",
        "queued_at",
        "started_at",
        "completed_at",
    )
    inlines = (OcrPageTextInline,)

