from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "development-only-change-me")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

if os.environ.get("USE_SQLITE", "1") == "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "var" / "development.sqlite3",
        }
    }
