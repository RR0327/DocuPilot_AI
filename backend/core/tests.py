from django.test import TestCase
from django.urls import reverse

class HealthEndpointTests(TestCase):
    def test_health_returns_expected_payload(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "docupilot-api", "phase": "0.1"})

    def test_health_rejects_post(self):
        response = self.client.post(reverse("health"))
        self.assertEqual(response.status_code, 405)
