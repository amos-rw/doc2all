from django.test import SimpleTestCase, override_settings


class DevHealthTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_reports_the_tools_in_development(self):
        response = self.client.get("/api/dev/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["server"], "ok")
        self.assertEqual(set(response.json()["tools"]), {"libreoffice", "tesseract"})
        self.assertTrue(all(isinstance(found, bool) for found in response.json()["tools"].values()))

    @override_settings(DEBUG=False)
    def test_hidden_outside_development(self):
        self.assertEqual(self.client.get("/api/dev/health").status_code, 404)
