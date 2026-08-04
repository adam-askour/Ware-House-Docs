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

## Current verification

Verified on 2026-08-04:

- Full test suite: 25 passed
- Ruff linting: passed
- Django system checks: passed with no issues
- Migration consistency check: no changes detected

## Next milestone

Phase 2 — document core and manual upload. This includes document and version
models, protected PDF validation and storage, manual upload and listing,
permission-checked file serving, and upload/view/download audit events.

The employee landing page is intentionally minimal until the Phase 2 document
list becomes its primary content. Confidential labels should later move from
free text to a dedicated model or controlled choices. Reviewer scope must also
be defined before reviewer status is used as a document-access grant.
