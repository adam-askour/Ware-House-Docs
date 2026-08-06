from django.contrib import admin

from .models import IngestionRecord, Scanner


@admin.register(Scanner)
class ScannerAdmin(admin.ModelAdmin):
    list_display = ("identifier", "name", "location", "is_active")
    list_filter = ("is_active",)
    search_fields = ("identifier", "name", "location")


@admin.register(IngestionRecord)
class IngestionRecordAdmin(admin.ModelAdmin):
    list_display = ("idempotency_key", "scanner", "employee", "department", "state", "scanned_at")
    list_filter = ("state", "scanner", "department")
    search_fields = ("idempotency_key", "original_filename", "sha256", "employee__username")
    readonly_fields = (
        "idempotency_key",
        "employee",
        "department",
        "document",
        "duplicate_of",
        "sha256",
        "size",
        "state",
        "failure_reason",
        "attempts",
        "created_at",
        "updated_at",
    )

