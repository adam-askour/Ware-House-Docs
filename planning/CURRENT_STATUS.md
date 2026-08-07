# Current Project Status

Last updated: 2026-08-06 (Africa/Casablanca)

## Current milestone

Phase 0 infrastructure, Phase 1 identity and authorization, Phase 2 document
core and manual upload, and Phase 3 scanner simulation and ingestion are
complete. Phase 4 OCR and searchable PDF generation is in progress.

## Phase 1 delivered

- Custom user model with unique email, scanner code, and active/deactivated
  account controls.
- Authentication by username or email, plus login, logout, and password-change
  routes and templates.
- Departments with multi-department user memberships.
- Employee, supervisor, and department-chief roles scoped per department.
- Three-level document visibility: normal documents for all department members,
  supervisor documents for supervisors and chiefs, and chief-only documents.
- Explicit confidential authorizations independent from Django staff and
  superuser permissions.
- Reusable deny-by-default access-policy helpers.
- Department-scoped policies deny access when the department is inactive.
- Confidential free-text label checks use case-insensitive exact matching.
- Authenticated employee landing page; ordinary users are no longer redirected
  to Django administration after login.
- Django superuser management for users, departments, memberships, chief
  assignments, scanner codes, and confidential grants.
- User administration displays department memberships and explicit
  confidential authorizations together.
- Protected-resource and direct-admin-URL tests verify denied responses do not
  expose protected content.

## Phase 2 delivered

- Document, primary/additional department, metadata, stored-file, version, and
  status-history models.
- Protected randomized storage paths and SHA-256 integrity checksums.
- Parsed PDF-only validation that rejects renamed, corrupt, and encrypted PDFs.
- Manual uploads limited to active department memberships and explicit
  confidentiality grants.
- Permission-filtered document landing page with department/status filters.
- Protected inline preview and attachment download responses with private,
  no-store caching.
- Audit events for successful upload, view, and download actions.
- Database constraints for unique assignments, versions, metadata keys, and a
  single primary department; publication validation requires a primary.

## Phase 2 verification

Verified on 2026-08-04:

- Full test suite: 32 passed.
- Ruff linting: passed.
- Django system checks: passed with no issues.
- Migration consistency check: no changes detected.

The Phase 2 exit criterion is satisfied: authorized employees can safely
upload, list, preview, and download test PDFs, and unauthorized users cannot
discover or retrieve their contents.

## Phase 3 delivered

- Company-wide shared scanner records independent of department ownership.
- Simulator command submitting a PDF, scanner identifier, employee scan code,
  scan timestamp, and optional idempotency key.
- Automatic employee identification and department routing from the scan code;
  employees never select a destination department.
- Safe routing requires exactly one active membership in an active department;
  ambiguous or missing routes are quarantined instead of guessed.
- Stable-file age and non-empty checks prevent premature consumption.
- Idempotent ingestion ledger with scanner, employee, department, checksum,
  document, timestamps, state, attempts, and failure information.
- SHA-256 exact-duplicate detection without unintended document creation.
- Quarantine handling for unknown/inactive codes, inactive scanners, ambiguous
  memberships, and invalid, corrupt, or encrypted PDFs.
- Successful scans create protected version-one documents immediately in
  `Processing` status, with status and upload audit events.

## Phase 3 verification

Verified on 2026-08-06:

- Full test suite: 43 passed.
- Ruff linting: passed.
- Django system checks: passed with no issues.
- Migration consistency check: no changes detected.

## Running environment

The Docker Compose environment established in Phase 0 contains PostgreSQL,
Redis, Django/Gunicorn, Celery worker, Celery Beat, and the Nginx TLS gateway.
The local development certificate is self-signed.

If `docker` is not available on `PATH`, its verified location is:

```text
C:\Users\PC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe
```

## Phase 4 delivered so far

- Durable queued/running/succeeded/failed OCR jobs for each document version.
- Existing-text detection that avoids unnecessary OCR.
- OCRmyPDF derivatives with orientation detection, deskew, conservative cleanup,
  and English, French, and Arabic Tesseract configuration.
- Page-numbered extracted text, warnings, attempt counts, and failure details.
- Original-file preservation and searchable derivatives used for inline preview.
- Automatic OCR queueing for scanner ingestion and manual uploads.
- Administrator-visible OCR job failures and page output.

## Next step

Add the PDF.js page-by-page viewer and an explicit retry action for failed OCR
jobs, then verify representative French, Arabic, English, and rotated samples.
