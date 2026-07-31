import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"Required production setting {name} is missing.")
    return value


SECRET_KEY = required_env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = [host.strip() for host in required_env("DJANGO_ALLOWED_HOSTS").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in required_env("DJANGO_CSRF_TRUSTED_ORIGINS").split(",")
    if origin.strip()
]
if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Wildcard production hosts are forbidden.")

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
