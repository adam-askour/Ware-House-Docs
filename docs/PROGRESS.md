# Implementation progress

Last updated: 2026-08-04 (Africa/Casablanca)

## Phase 0 — Project foundation

- [x] Django project and cohesive module skeleton
- [x] PostgreSQL, Redis, Celery worker, and scheduler configuration
- [x] Docker Compose topology with private backend network
- [x] Environment-specific settings and placeholder-only example
- [x] Structured logging and minimal health/readiness endpoints
- [x] Isolated test configuration and static/security tooling
- [x] Protected media/quarantine/static directory separation
- [x] Production-style Nginx TLS and security headers
- [x] Automated tests and static checks
- [x] Docker runtime environment established

## Phase 1 — Identity, organization, and authorization

- [x] Custom user model and username-or-email authentication
- [x] Login, logout, password change, and authenticated employee landing page
- [x] Departments and multi-department memberships
- [x] Department-scoped employee and chief roles
- [x] Explicit confidential grants independent from administrator permissions
- [x] Deny-by-default access-policy helpers
- [x] Administrator management screens
- [x] Direct-URL and protected-resource authorization tests
- [x] Inactive users, memberships, grants, and departments denied by policy
- [x] Case-insensitive exact matching for current free-text confidential labels

Phase 1 is complete. Its exit criterion is satisfied: role and department rules
are enforced server-side, and administrator status does not implicitly grant
confidential access.

## Phase 2 — Document core and manual upload

- [x] Document, department assignment, metadata, protected storage, version,
  and status-history models
- [x] Randomized protected original paths with SHA-256 checksums
- [x] Parsed PDF validation rejecting renamed, corrupt, and encrypted files
- [x] Department- and confidentiality-authorized manual upload
- [x] Permission-filtered document landing page and basic filters
- [x] Permission-checked preview and download endpoints
- [x] Upload, view, and download audit events
- [x] Primary-department publication and single-primary constraints

Phase 2 is complete. Its exit criterion is satisfied: authorized employees can
upload, list, preview, and download test PDFs, while unauthorized requests
receive no protected content.

## Current verification

Verified on 2026-08-04:

- Full test suite: 32 passed
- Ruff linting: passed
- Django system checks: passed with no issues
- Migration consistency check: no changes detected

## Next milestone

Phase 3 — scanner simulator and ingestion. This includes scanner records,
stable-file detection, an idempotent ingestion ledger, duplicate detection,
  quarantine/failure handling, and immediate Processing documents. Uncertain
  scans return to the scanning employee, with department-chief escalation.
