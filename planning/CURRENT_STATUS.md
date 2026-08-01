# Current Project Status

Last updated: 2026-07-31 (Africa/Casablanca)

## Current milestone

Phase 0 infrastructure is complete and operational. Phase 1 implementation is
now underway.

The repository checkpoint is commit `fb6fdaa` on `main`, synchronized with
`origin/main`. The working tree was clean when this status was recorded.

## Latest verification and cleanup

The final Phase 0 cleanup corrected Django import resolution and configuration
warnings:

- Configured VS Code to use the project's local `.venv` interpreter.
- Enabled pytest discovery in VS Code.
- Added explicit imports required by development and production settings.
- Sorted the base-settings imports.
- Suppressed justified security-linter false positives in test-only code.
- Verified the Django ASGI and WSGI imports.
- Confirmed Ruff checks, Django system checks, and the full test suite pass.

## Running environment

The complete Docker Compose stack was built, initialized, and verified:

- PostgreSQL 17.6: running and healthy
- Redis 8.2: running and healthy
- Django/Gunicorn web service: running and healthy
- Celery worker: running
- Celery Beat scheduler: running
- Nginx TLS gateway: running on host port 443

The HTTPS health endpoint returned `200 OK` at:

```text
https://localhost/health/
```

The certificate is self-signed for local development, so browsers will show a
certificate warning unless it is added to the local trust store.

## Initialization completed

- Created the ignored local `.env` with development deployment secrets.
- Generated ignored local TLS files:
  - `deploy/certs/dms.crt`
  - `deploy/certs/dms.key`
- Applied all current Django migrations.
- Collected 127 static files.
- Ran `python manage.py check --deploy` successfully with no issues.

## Project fixes made

- Added the missing `dashboards` Python package required by
  `INSTALLED_APPS`.
- Corrected the web container health check so it supplies
  `X-Forwarded-Proto: https` and is not rejected by Django's HTTPS redirect.
- Configured Celery Beat to store its schedule at
  `/tmp/celerybeat-schedule`, which is writable by the non-root container user.

## Docker note

Docker Desktop initially cached a failure from before WSL 2 was available.
Restarting WSL and Docker Desktop resolved it. Docker Desktop 4.84.0,
Docker Engine 29.6.2, and Docker Compose 5.3.1 were verified.

In a PowerShell session where `docker` is not yet on `PATH`, the executable is:

```text
C:\Users\PC\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe
```

## Useful commands

Run these from the project root:

```powershell
docker compose ps
docker compose logs --tail 100
docker compose up -d
docker compose down
```

If `docker` is not recognized, restart the terminal or invoke the executable
using the full path shown above.

## Next step

Complete the remaining Phase 1 authentication hardening and protected-resource
integration. The first implemented slice provides the custom user, department
membership, department-chief role, reviewer flag, scanner identity,
confidential grants, administrator management, and reusable deny-by-default
policy helpers.
