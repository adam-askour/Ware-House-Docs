from django.test import TestCase
from django.urls import reverse


class HealthTests(TestCase):
    def test_liveness_is_non_cacheable_and_minimal(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertIn("no-cache", response.headers["Cache-Control"])

    def test_readiness_checks_database_without_disclosing_details(self):
        response = self.client.get(reverse("core:readiness"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})
        self.assertNotContains(response, "sqlite", status_code=200)
