"""Security tests of upload and convert. Each class names the abuse cases (AC) it tries, from report section 3.6."""
import io
import os
import sys
import time
import zipfile
from datetime import timedelta
from pathlib import Path
from unittest import mock, skipUnless
from xml.dom import minidom

from django.test import Client, SimpleTestCase, override_settings
from django.utils import timezone
from pypdf import PdfReader

from core import audit, tools
from core.models import AuditLine

from . import attacks, neutralize, timer
from .models import Job, StoredFile
from .tests import SAMPLES, FilesCase

HAS_OFFICE = tools.find("libreoffice") is not None


class LookInsideTests(FilesCase):
    """AC-03 a file that is not what its name says, AC-05 a bomb."""

    def refused(self, content, words, name="a.docx"):
        response = self.upload(name, content)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn(words, response.json()["message"])
        self.assertEqual(StoredFile.objects.count(), 0)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_the_samples_are_accepted(self):
        for name in ("sample-letter.docx", "sample-slides.pptx"):
            self.assertIn("id", self.sample(name))

    def test_another_kind_of_document_with_a_word_name(self):
        self.refused(attacks.odt_renamed(), "something else")

    def test_a_powerpoint_with_a_word_name(self):
        self.refused((SAMPLES / "sample-slides.pptx").read_bytes(), "something else")

    def test_a_large_bomb(self):
        self.refused(attacks.docx_bomb(600), "grows far too much")

    def test_a_small_file_that_grows_more_than_100_times(self):
        self.refused(attacks.docx_bomb(20), "grows far too much")

    @override_settings(MAX_EXPANDED_BYTES=1000)
    def test_the_total_size_limit(self):
        self.refused((SAMPLES / "sample-letter.docx").read_bytes(), "grows far too much")

    def test_too_many_parts(self):
        extra = {f"word/extra{i}.txt": b"x" for i in range(2001)}
        self.refused(attacks.rebuild("sample-letter.docx", add=extra), "too many parts")

    def test_xml_that_declares_its_own_entities(self):
        for coding in ("utf-8", "utf-16"):
            with self.subTest(coding):
                evil = f'<?xml version="1.0" encoding="{coding}"?><!DOCTYPE a [<!ENTITY b "bbbb">]><a>&b;</a>'.encode(coding)
                self.refused(attacks.rebuild("sample-letter.docx", add={"word/extra.xml": evil}), "does not open")

    def test_a_damaged_package(self):
        self.refused(b"PK\x03\x04" + bytes(range(256)) * 4, "damaged")

    @override_settings(MAX_PAGES=1)
    def test_too_many_slides(self):
        self.refused((SAMPLES / "sample-slides.pptx").read_bytes(), "slides", "a.pptx")


class SafeCopyTests(SimpleTestCase):
    """AC-06: the copy that is opened holds no macros and nothing that can reach outside."""

    def copy_of(self, content, kind="docx"):
        target = io.BytesIO()
        removed = neutralize.safe_copy(io.BytesIO(content), target, kind)
        return removed, zipfile.ZipFile(target)

    def targets(self, package):
        for name in package.namelist():
            if name.endswith(".rels"):
                for relation in minidom.parseString(package.read(name)).getElementsByTagName("Relationship"):
                    yield relation.getAttribute("Type").rsplit("/", 1)[-1], relation.getAttribute("Target")

    def test_outside_links_are_blocked(self):
        for kind, content in (("docx", attacks.docx_with_outside_picture("http://example.invalid/a.png")),
                              ("docx", attacks.docx_with_outside_picture("file:///C:/secret.png")),
                              ("docx", attacks.docx_with_outside_picture("\\\\server\\share\\a.png")),
                              ("docx", attacks.docx_with_outside_template("http://example.invalid/t.dotx")),
                              ("pptx", attacks.pptx_with_outside_picture("http://example.invalid/a.png"))):
            removed, package = self.copy_of(content, kind)
            self.assertEqual(removed["outside_link"], 1)
            joined = " ".join(target for _kind, target in self.targets(package))
            for word in ("example.invalid", "secret", "server"):
                self.assertNotIn(word, joined)

    def test_a_link_the_reader_may_click_stays(self):
        content = attacks.rebuild("sample-letter.docx", {"word/_rels/document.xml.rels": attacks._add_relationship(
            attacks._relationship("rIdWeb", "hyperlink", "https://example.com/"))})
        removed, package = self.copy_of(content)
        self.assertEqual(removed["outside_link"], 0)
        self.assertIn(("hyperlink", "https://example.com/"), list(self.targets(package)))

    def test_macros_are_left_out(self):
        content = attacks.rebuild("sample-letter.docx", add={"word/vbaProject.bin": b"macro", "word/activeX/a.bin": b"x"})
        removed, package = self.copy_of(content)
        self.assertEqual(removed["macro"], 2)
        self.assertFalse([n for n in package.namelist() if "vba" in n.lower() or "activex" in n.lower()])

    def test_fetching_fields_are_emptied_also_when_cut_into_pieces(self):
        for instruction in ('INCLUDETEXT "C:/secret.txt"', "includepicture http://example.invalid/a.png", "DDEAUTO cmd x"):
            for split in (False, True):
                with self.subTest(instruction, split=split):
                    removed, package = self.copy_of(attacks.docx_with_field(instruction, split))
                    self.assertEqual(removed["outside_field"], 1)
                    body = package.read("word/document.xml").decode()
                    self.assertNotIn("secret", body)
                    self.assertNotIn("example.invalid", body)
                    self.assertIn("saved text", body)

    def test_an_ordinary_file_is_not_changed(self):
        content = (SAMPLES / "sample-letter.docx").read_bytes()
        removed, package = self.copy_of(content)
        self.assertEqual(set(removed.values()), {0})
        with zipfile.ZipFile(io.BytesIO(content)) as original:
            self.assertTrue(all(package.read(n) == original.read(n) for n in original.namelist()))


@skipUnless(HAS_OFFICE, "LibreOffice is not installed")
class OutsideReachTests(FilesCase):
    """AC-06: opening a trick file reaches nothing outside it."""

    def converted(self, name, content):
        job = self.convert(self.upload(name, content).json()["id"]).json()["id"]
        report = self.client.get(f"/api/jobs/{job}/report").json()
        self.assertEqual(report["outcome"], "converted", report)
        pdf = b"".join(self.client.get(f"/api/files/{report['resultId']}/download").streaming_content)
        return report, PdfReader(io.BytesIO(pdf))

    def test_nothing_is_fetched_and_the_report_says_so(self):
        with attacks.listener() as (address, seen):
            for name, content in (("a.docx", attacks.docx_with_outside_picture(address + "/picture.png")),
                                  ("b.docx", attacks.docx_with_outside_template(address + "/template.dotx")),
                                  ("c.pptx", attacks.pptx_with_outside_picture(address + "/slide.png"))):
                report, _pdf = self.converted(name, content)
                self.assertIn("Outside links blocked: 1", [f["title"] for f in report["findings"]])
        self.assertEqual(seen, [])

    def test_libreoffice_alone_also_fetches_nothing(self):
        """The second wall: even without our safe copy, the settings stop it."""
        with attacks.listener() as (address, seen):
            (self.folder / "a.docx").write_bytes(attacks.docx_with_outside_picture(address + "/picture.png"))
            tools.office_convert(self.folder / "a.docx", "pdf", self.folder)
        self.assertEqual(seen, [])

    def test_files_on_the_server_do_not_reach_the_pdf(self):
        secret = self.folder.parent / f"{self.folder.name}-secret.txt"
        secret.write_text("CANARY-5521", encoding="ascii")
        self.addCleanup(secret.unlink)
        _report, pdf = self.converted("a.docx", attacks.docx_with_field(f"INCLUDETEXT {secret.as_posix()}"))
        self.assertNotIn("CANARY", "".join(page.extract_text() for page in pdf.pages))

    @override_settings(MAX_PAGES=2)
    def test_a_document_over_the_page_limit_gives_nothing(self):
        job = self.convert(self.upload("long.docx", attacks.docx_with_pages(3)).json()["id"]).json()["id"]
        report = self.client.get(f"/api/jobs/{job}/report").json()
        self.assertEqual((report["outcome"], report["resultId"]), ("failed", None))
        self.assertIn("longer than 100 pages", report["findings"][0]["title"])


class ProgramLimitTests(SimpleTestCase):
    """AC-05 and AC-06: a program that runs too long, takes too much, or looks for secrets."""

    def python(self, code):
        return tools.run([sys.executable, "-c", code])

    def test_it_is_not_given_the_server_secrets(self):
        with mock.patch.dict(os.environ, {"DJANGO_SECRET_KEY": "very-secret", "AUDIT_KEY": "very-secret"}):
            code, output = self.python("import os; print(sorted(os.environ.items()))")
        self.assertEqual(code, 0, output)
        self.assertNotIn("very-secret", output)

    @override_settings(CONVERTER_TIMEOUT=2)
    def test_time_limit(self):
        started = time.monotonic()
        with self.assertRaisesMessage(tools.ToolError, "too long"):
            self.python("import time; time.sleep(30)")
        self.assertLess(time.monotonic() - started, 15)

    @override_settings(CONVERTER_MEMORY_MB=200)
    def test_memory_limit(self):
        code, output = self.python("b = bytearray(400 * 1024 * 1024); print('took it')")
        self.assertNotEqual(code, 0)
        self.assertNotIn("took it", output)

    def test_a_crowd_of_processes_is_stopped(self):
        code, output = self.python(
            "import subprocess, sys\n"
            "started = [subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(3)']) for _ in range(20)]\n"
            "print('started them all')")
        self.assertNotIn("started them all", output)

    def test_an_administrator_account_opens_nothing(self):
        with mock.patch.object(tools, "running_as_administrator", return_value=True), self.assertRaisesMessage(tools.ToolError, "administrator"):
            self.python("print()")


class LimitTests(FilesCase):
    """AC-09: many uploads, many jobs, a huge request."""

    @override_settings(UPLOADS_PER_HOUR=3)
    def test_uploads_in_an_hour(self):
        codes = [self.upload("a.pdf", b"%PDF-1.7").status_code for _ in range(4)]
        self.assertEqual(codes, [200, 200, 200, 429])

    def test_a_huge_request_is_refused_before_it_is_read(self):
        response = self.upload("huge.pdf", b"%PDF" + bytes(21 * 1024 * 1024))
        self.assertEqual((response.status_code, response.json()["error"]), (413, "too_big"))
        self.assertEqual(StoredFile.objects.count(), 0)

    def test_one_job_for_a_file_and_only_a_few_at_once(self):
        files = [self.sample("sample-letter.docx")["id"] for _ in range(6)]
        for file_id in files[:5]:
            Job.objects.create(file_id=file_id, actions=["convert"], status=Job.RUNNING)
        again = self.convert(files[0])
        another = self.convert(files[5])
        self.assertEqual((again.status_code, another.status_code), (429, 429))
        self.assertIn("already", again.json()["message"])
        self.assertIn("busy", another.json()["message"])


class FormTokenTests(FilesCase):
    """Another website must not be able to act through the user's browser."""

    def post(self, client, **headers):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return client.post("/api/files", {"file": SimpleUploadedFile("a.pdf", b"%PDF-1.7")}, **headers)

    def test_without_the_token_nothing_changes(self):
        stranger = Client(enforce_csrf_checks=True)
        self.assertEqual(self.post(stranger).json()["error"], "token")
        self.assertEqual(stranger.delete("/api/files/anything").status_code, 403)
        self.assertEqual(stranger.delete("/api/history/anything").status_code, 403)
        self.assertEqual(stranger.post("/api/jobs", {}, content_type="application/json").status_code, 403)
        self.assertEqual(StoredFile.objects.count(), 0)

    def test_our_page_with_its_token_is_accepted_another_site_is_not(self):
        browser = Client(enforce_csrf_checks=True)
        token = browser.get("/api/session").json()["formToken"]
        ours = self.post(browser, HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN="http://testserver")
        theirs = self.post(browser, HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN="https://stranger.example")
        self.assertEqual((ours.status_code, theirs.status_code), (200, 403))

    def test_the_token_cookie_is_hidden_from_scripts(self):
        cookie = Client().get("/api/session").cookies["csrftoken"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Strict")


class HeaderTests(FilesCase):
    """SR-21: a download is saved, never run in the page."""

    def test_download_headers(self):
        file = self.upload("a.pdf", b"%PDF-1.7").json()
        response = self.client.get(f"/api/files/{file['id']}/download")
        self.assertTrue(response["Content-Disposition"].startswith("attachment"))
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("sandbox", response["Content-Security-Policy"])
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        response.close()


class AuditTests(FilesCase):
    """AC-11 and SR-19, SR-20."""

    def do_things(self):
        file = self.upload("private-diary.pdf", b"%PDF-1.7").json()
        self.upload("virus.pdf", b"MZ")
        self.client.get(f"/api/files/{file['id']}/download").close()
        self.client.delete(f"/api/files/{file['id']}")
        return file["id"]

    def test_actions_are_recorded_with_ids_and_no_names(self):
        file_id = self.do_things()
        lines = list(AuditLine.objects.order_by("pk").values_list("action", "result", "target_id"))
        self.assertEqual(lines, [("Upload", "OK", file_id), ("Upload", "Refused", ""), ("Download", "OK", file_id), ("Delete file", "OK", file_id)])
        everything = str(list(AuditLine.objects.values()))
        for private in ("diary", "virus", ".pdf"):
            self.assertNotIn(private, everything)

    def test_the_application_cannot_change_or_delete_a_line(self):
        self.do_things()
        line = AuditLine.objects.first()
        line.result = "changed"
        with self.assertRaises(TypeError):
            line.save()
        with self.assertRaises(TypeError):
            line.delete()

    def test_a_line_changed_or_removed_in_the_database_shows(self):
        self.do_things()
        self.assertEqual(audit.broken_lines(), [])
        second, third = AuditLine.objects.order_by("pk")[1:3]
        AuditLine.objects.filter(pk=second.pk).update(result="OK")  # as someone with the database could
        self.assertEqual(audit.broken_lines(), [third.pk])
        AuditLine.objects.filter(pk=second.pk).update(result="Refused")
        AuditLine.objects.filter(pk=second.pk)._raw_delete("default")
        self.assertEqual(audit.broken_lines(), [third.pk])


class TimerTests(FilesCase):
    """AC-11: files go after 24 hours although nobody uses the app."""

    def test_the_timer_deletes_expired_content(self):
        file = self.upload("a.pdf", b"%PDF-1.7").json()
        StoredFile.objects.update(delete_after=timezone.now() - timedelta(seconds=1))
        timer.tidy()
        self.assertEqual(list(self.folder.iterdir()), [])
        self.assertIsNotNone(StoredFile.objects.get().deleted_at)
        self.assertTrue(AuditLine.objects.filter(action="Delete after 24 hours", target_id=file["id"]).exists())

    def test_left_over_content_goes_and_nothing_else(self):
        old = time.time() - 7200
        forgotten, young, not_ours = self.folder / ("a" * 32), self.folder / ("b" * 32), self.folder / "keep-me.txt"
        for path in (forgotten, young, not_ours):
            path.write_bytes(b"x")
        os.utime(forgotten, (old, old))
        os.utime(not_ours, (old, old))
        timer.tidy()
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), sorted([young.name, not_ours.name]))
