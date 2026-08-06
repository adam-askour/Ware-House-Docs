# Internal Document Management System

Production-minded, zero-license-cost Django prototype for secure local PDF
ingestion, OCR, classification, permission-filtered search, and lifecycle
management.

## Current state

Phases 0–3 provide the infrastructure, identity and department authorization,
protected PDF storage, manual upload, permission-filtered access, document
auditing, and shared-scanner simulation with automatic employee-code routing.
Product features are added strictly in the order in
`planning/IMPLEMENTATION_ROADMAP.md`.

## Scanner simulation

Create an active scanner in Django administration, then submit a stable test PDF:

```text
python manage.py simulate_scan sample.pdf --scanner reception-1 --employee-code 123456
```

The employee code determines the employee and their active department; scanner
location never determines ownership. Automatic routing requires exactly one
active department membership. Unknown/inactive codes, invalid PDFs, inactive
scanners, and ambiguous memberships are quarantined. `--event-key` can carry a
scanner event identifier for idempotent retries.

## Local development

Use Python 3.12 or 3.13. Create and activate a virtual environment, then:

```text
python -m pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver
```

Development defaults to SQLite only so the web process and tests remain
runnable without containers. PostgreSQL is mandatory for the integrated stack
and search phases. Set `USE_SQLITE=0` to use the configured PostgreSQL service.

Run checks:

```text
pytest
ruff check .
bandit -c pyproject.toml -r .
python manage.py check
```

## Docker Compose

Copy `.env.example` to `.env`, replace every placeholder with generated
secrets, install local TLS certificates as described in `deploy/certs/README.md`,
then run `docker compose up --build`. PostgreSQL and Redis have no host ports
and are reachable only on the internal container network.

Never reuse development placeholder secrets in a shared or production-style
deployment.
