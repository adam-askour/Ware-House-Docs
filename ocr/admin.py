from django.contrib import admin

from .models import OcrJob, OcrPageText
from .services import retry_ocr


class OcrPageTextInline(admin.TabularInline):
    model = OcrPageText
    extra = 0
    readonly_fields = ("page_number", "text")


@admin.register(OcrJob)
class OcrJobAdmin(admin.ModelAdmin):
    actions = ("retry_failed_jobs",)
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
    @admin.action(description="Retry selected failed OCR jobs")
    def retry_failed_jobs(self, request, queryset):
        retried = 0
        for job in queryset.filter(status=OcrJob.Status.FAILED):
            retry_ocr(job)
            retried += 1
        self.message_user(request, f"Queued {retried} failed OCR job(s) for retry.")
