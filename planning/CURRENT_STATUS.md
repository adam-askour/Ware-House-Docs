# Current Project Status

Last updated: 2026-08-04 (Africa/Casablanca)

## Current milestone

Phase 0 infrastructure, Phase 1 identity and authorization, and Phase 2
document core and manual upload are complete. The next milestone is Phase 3
scanner simulation and ingestion.

## Phase 1 delivered

- Custom user model with unique email, scanner code, reviewer status, and
  active/deactivated account controls.
- Authentication by username or email, plus login, logout, and password-change
  routes and templates.
- Departments with multi-department user memberships.
- Employee and department-chief roles scoped per department.
- Explicit confidential authorizations independent from Django staff and
  superuser permissions.
- Reusable deny-by-default access-policy helpers.
- Department-scoped policies deny access when the department is inactive.
- Confidential free-text label checks use case-insensitive exact matching.
- Authenticated employee landing page; ordinary users are no longer redirected
  to Django administration after login.
- Django administrator management for users, departments, memberships, chief
  assignments, reviewer status, scanner codes, and confidential grants.
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

## Running environment

The Docker Compose environment established in Phase 0 contains PostgreSQL,
Redis, Django/Gunicorn, Celery worker, Celery Beat, and the Nginx TLS gateway.
The local development certificate is self-signed.

If `docker` is not available on `PATH`, its verified location is:

```text
C:\Users\PC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe
```

## Next step

Begin Phase 3 with scanner records and intake configuration, followed by a
scanner simulator, stable-file detection, an idempotent ingestion ledger,
checksum-based duplicate handling, quarantine/failure areas, and immediate
Processing document creation.
