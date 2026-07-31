import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


class ProductionSettingsTests(SimpleTestCase):
    def run_check(self, overrides):
        env = os.environ.copy()
        env.update(overrides)
        env["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
        return subprocess.run(  # noqa: S603 - fixed interpreter and command
            [sys.executable, "-c", "import django; django.setup()"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_missing_secret_fails_closed(self):
        result = self.run_check(
            {
                "DJANGO_SECRET_KEY": "",
                "DJANGO_ALLOWED_HOSTS": "dms.internal",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "https://dms.internal",
            }
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("unsafe-development-only-key", result.stdout + result.stderr)

    def test_wildcard_host_fails_closed(self):
        result = self.run_check(
            {
                "DJANGO_SECRET_KEY": "a" * 64,
                "DJANGO_ALLOWED_HOSTS": "*",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "https://dms.internal",
            }
        )
        self.assertNotEqual(result.returncode, 0)
