# Architecture

The system is a modular Django monolith. HTTP requests terminate at Nginx over
TLS and reach the Django web process. PostgreSQL is the system of record and
full-text search engine. Redis is a private Celery broker/result backend.
Celery workers run document processing outside web requests. Originals and
derivatives live in protected storage with no public media URL.

Application boundaries follow the roadmap: accounts, organization, documents,
ingestion, OCR, classification, search, access, reviews, notifications, audit,
retention, and dashboards. Cross-cutting authorization will be centralized in
the access module and invoked by list querysets, object actions, file routes,
search, dashboards, and background jobs.

## Trust boundaries

Browser, upload, scanner, OCR, metadata, and classifier data are untrusted.
Nginx is the TLS boundary. Scanner adapters and workers receive separate
service identity and least-privilege controls in their implementation phases.
No file under protected storage is served by Nginx directly.
