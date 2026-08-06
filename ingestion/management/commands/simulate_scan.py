import time
import uuid
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ingestion.models import Scanner
from ingestion.services import file_is_stable, ingest_scan


class Command(BaseCommand):
    help = "Submit a completed PDF as if it came from a company scanner."

    def add_arguments(self, parser):
        parser.add_argument("pdf", type=Path)
        parser.add_argument("--scanner", required=True, dest="scanner_identifier")
        parser.add_argument("--employee-code", required=True)
        parser.add_argument("--event-key", default=None)
        parser.add_argument("--scanned-at", default=None, help="ISO-8601 timestamp")
        parser.add_argument("--skip-stability-check", action="store_true")

    def handle(self, *args, **options):
        path = options["pdf"].resolve()
        if not path.is_file():
            raise CommandError(f"PDF does not exist: {path}")
        if not options["skip_stability_check"] and not file_is_stable(
            path,
            minimum_age_seconds=settings.INGESTION_STABILITY_SECONDS,
            now_timestamp=time.time(),
        ):
            raise CommandError("File is empty, incomplete, or too recent; try again when stable.")
        try:
            scanner = Scanner.objects.get(identifier=options["scanner_identifier"])
        except Scanner.DoesNotExist as exc:
            raise CommandError("Unknown scanner identifier.") from exc
        try:
            scanned_at = (
                datetime.fromisoformat(options["scanned_at"])
                if options["scanned_at"]
                else timezone.now()
            )
        except ValueError as exc:
            raise CommandError("--scanned-at must be an ISO-8601 timestamp.") from exc
        if timezone.is_naive(scanned_at):
            scanned_at = timezone.make_aware(scanned_at)
        event_key = options["event_key"] or uuid.uuid4().hex
        with path.open("rb") as stream:
            record = ingest_scan(
                scanner=scanner,
                employee_code=options["employee_code"],
                upload=File(stream, name=path.name),
                scanned_at=scanned_at,
                idempotency_key=event_key,
            )
        self.stdout.write(
            self.style.SUCCESS(f"Ingestion {record.idempotency_key}: {record.state}")
        )
