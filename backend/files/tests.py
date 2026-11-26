"""Upload and convert, from the first call to the last. The conversion really runs when LibreOffice is installed."""
import shutil
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from core import tools

from . import attacks
from .models import Finding, Job, Report, StoredFile

SAMPLES = Path(__file__).resolve().parents[2] / "samples" / "public"


class FilesCase(TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix="doc2all-test-"))
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        overrides = override_settings(PRIVATE_FILES_DIR=self.folder, JOBS_INLINE=True)
        overrides.enable()
        self.addCleanup(overrides.disable)

    def upload(self, name, content):
        return self.client.post("/api/files", {"file": SimpleUploadedFile(name, content)})

    def sample(self, name):
        return self.upload(name, (SAMPLES / name).read_bytes()).json()

    def convert(self, file_id):
        return self.client.post("/api/jobs", {"fileId": file_id, "actions": ["convert"]}, content_type="application/json")


class UploadTests(FilesCase):
    def test_a_program_with_a_document_name_is_refused_and_not_saved(self):
        response = self.upload("report.pdf", b"MZ\x90\x00 not a document")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "refused")
        self.assertIn("it is a program", response.json()["message"])
        self.assertEqual(StoredFile.objects.count(), 0)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_other_types_and_wrong_content_are_refused(self):
        for name, content in (("notes.txt", b"hello"), ("sheet.xlsx", b"PK\x03\x04"), ("photo.png", b"%PDF-1.7"), ("empty.docx", b"")):
            with self.subTest(name):
                self.assertEqual(self.upload(name, content).status_code, 400)

    @override_settings(MAX_UPLOAD_BYTES=10)
    def test_too_large_is_refused(self):
        self.assertEqual(self.upload("big.pdf", b"%PDF-1.7 and more").status_code, 400)

    def test_saved_under_a_random_name_with_a_random_id(self):
        first = self.upload("../../letter.pdf", b"%PDF-1.7").json()
        second = self.upload("letter.pdf", b"%PDF-1.7").json()
        self.assertEqual(first["name"], "letter.pdf")
        self.assertEqual(len(first["id"]), 22)
        self.assertNotEqual(first["id"], second["id"])
        stored = sorted(p.name for p in self.folder.iterdir())
        self.assertEqual(stored, sorted(StoredFile.objects.values_list("stored_name", flat=True)))
        self.assertTrue(all("letter" not in name for name in stored))
        self.assertEqual(first["allowed"], [])  # PDF work is not built yet

    def test_only_work_that_exists_can_be_started(self):
        file = self.upload("letter.pdf", b"%PDF-1.7").json()
        self.assertEqual(self.convert(file["id"]).status_code, 400)
        self.assertEqual(self.convert("unknown").status_code, 404)
        self.assertEqual(self.client.get("/api/jobs/unknown").json(), {"error": "not_found", "message": "Not found."})


@unittest.skipUnless(tools.find("libreoffice"), "LibreOffice is not installed")
class ConvertTests(FilesCase):
    def test_word_and_powerpoint_become_real_pdfs(self):
        for name in ("sample-letter.docx", "sample-slides.pptx"):
            with self.subTest(name):
                file = self.sample(name)
                job = self.convert(file["id"]).json()["id"]
                self.assertEqual(self.client.get(f"/api/jobs/{job}").json()["status"], "done")
                report = self.client.get(f"/api/jobs/{job}/report").json()
                self.assertEqual(report["outcome"], "converted")  # never "all clear" while nothing is checked
                download = self.client.get(f"/api/files/{report['resultId']}/download")
                self.assertEqual(download.status_code, 200)
                self.assertIn(name.replace(name.split(".")[-1], "pdf"), download["Content-Disposition"])
                self.assertTrue(b"".join(download.streaming_content).startswith(b"%PDF"))

    def test_history_delete_and_remove(self):
        file = self.sample("sample-letter.docx")
        job = self.convert(file["id"]).json()["id"]
        result = self.client.get(f"/api/jobs/{job}/report").json()["resultId"]
        self.assertEqual(len(self.client.get("/api/history").json()["items"]), 1)
        self.assertEqual(len(list(self.folder.iterdir())), 2)

        self.assertEqual(self.client.delete(f"/api/files/{file['id']}").status_code, 200)
        self.assertEqual(list(self.folder.iterdir()), [])  # the upload and the result
        for file_id in (file["id"], result):
            self.assertEqual(self.client.get(f"/api/files/{file_id}/download").status_code, 404)
        self.assertTrue(self.client.get("/api/history").json()["items"][0]["deleted"])

        self.assertEqual(self.client.delete(f"/api/history/{job}").status_code, 200)
        for model in (StoredFile, Job, Report, Finding):
            self.assertEqual(model.objects.count(), 0, model.__name__)

    def test_content_goes_after_24_hours(self):
        file = self.sample("sample-letter.docx")
        job = self.convert(file["id"]).json()["id"]
        StoredFile.objects.update(delete_after=timezone.now() - timedelta(seconds=1))
        self.assertTrue(self.client.get("/api/history").json()["items"][0]["deleted"])
        self.assertEqual(list(self.folder.iterdir()), [])
        self.assertEqual(self.client.get(f"/api/files/{file['id']}/download").status_code, 404)
        self.assertTrue(self.client.get(f"/api/jobs/{job}/report").json()["fileDeleted"])

    def test_a_damaged_file_ends_with_a_clear_message(self):
        damaged = attacks.rebuild("sample-letter.docx", {"word/document.xml": lambda xml: "<broken"})
        file = self.upload("broken.docx", damaged).json()
        job = self.convert(file["id"]).json()["id"]
        report = self.client.get(f"/api/jobs/{job}/report").json()
        self.assertEqual((self.client.get(f"/api/jobs/{job}").json()["status"], report["outcome"]), ("failed", "failed"))
        self.assertIsNone(report["resultId"])
