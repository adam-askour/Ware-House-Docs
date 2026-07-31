# Configuration

All secrets come from environment variables. `.env.example` contains names and
non-secret placeholders only.

- `DJANGO_SETTINGS_MODULE`: environment settings module.
- `DJANGO_SECRET_KEY`: required in production; long random value.
- `DJANGO_ALLOWED_HOSTS`: required comma-separated production hosts.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: required HTTPS origins.
- `POSTGRES_*`: least-privilege application database connection.
- `REDIS_PASSWORD`: Redis authentication secret.
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: authenticated private Redis URLs.
- `BACKUP_DESTINATION`: separate protected disk or network location.
- `CLAMAV_ENABLED`: `auto` permits explicitly reported degraded development mode.
- `DJANGO_HSTS_SECONDS`: production HSTS duration.

Production imports fail closed when the secret, hosts, or trusted origins are
missing and reject wildcard hosts.
