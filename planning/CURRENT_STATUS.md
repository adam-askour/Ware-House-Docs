# Current Project Status

Last updated: 2026-08-04 (Africa/Casablanca)

## Current milestone

Phase 0 infrastructure and Phase 1 identity, organization, and authorization
are complete. The next milestone is Phase 2 document core and manual upload.

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

## Phase 1 verification

Verified on 2026-08-04:

- Full test suite: 25 passed.
- Ruff linting: passed.
- Django system checks: passed with no issues.
- Migration consistency check: no changes detected.

The Phase 1 exit criterion is satisfied: role and department rules are enforced
server-side, and administrator status does not implicitly grant confidential
access.

## Running environment

The Docker Compose environment established in Phase 0 contains PostgreSQL,
Redis, Django/Gunicorn, Celery worker, Celery Beat, and the Nginx TLS gateway.
The local development certificate is self-signed.

If `docker` is not available on `PATH`, its verified location is:

```text
C:\Users\PC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe
```

## Next step

Begin Phase 2 with document, department assignment, metadata, storage, version,
and status models. Then add protected PDF validation and storage, manual upload
and listing, permission-checked file serving, and audit events for upload, view,
and download.

Before confidential labels become broadly configurable, replace their current
free-text representation with a dedicated model or controlled choices. Label
authorization checks are case-insensitive in the interim.
