"""Proves that the processing programs really work here, by using them on made-up pages.

Run: python backend/manage.py check_tools
"""
import tempfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core import tools

HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?><office:document office:version="1.2" '
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
)
PAGE = HEAD + (
    'office:mimetype="application/vnd.oasis.opendocument.text"><office:automatic-styles><style:style style:name="Big" style:family="paragraph">'
    '<style:text-properties fo:font-size="36pt"/></style:style></office:automatic-styles>'
    '<office:body><office:text><text:p text:style-name="Big">Safe documents</text:p></office:text></office:body></office:document>'
)
SLIDE = HEAD + (
    'office:mimetype="application/vnd.oasis.opendocument.presentation"><office:body><office:presentation><draw:page draw:name="one">'
    '<draw:frame svg:x="2cm" svg:y="2cm" svg:width="20cm" svg:height="4cm"><draw:text-box><text:p>Safe slides</text:p></draw:text-box></draw:frame>'
    "</draw:page></office:presentation></office:body></office:document>"
)


class Command(BaseCommand):
    help = "Uses LibreOffice and Tesseract on made-up pages, to show they work on this computer."
    requires_system_checks = []

    def handle(self, *args, **options):
        for name in tools.PROGRAMS:
            path = tools.find(name)
            if not path:
                raise CommandError(f"{name} is not installed.")
            self.stdout.write(f"{name}: {path}")
        try:
            with tempfile.TemporaryDirectory(prefix="doc2all-check-") as folder:
                self.use_them(Path(folder))
        except tools.ToolError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(self.style.SUCCESS("Everything works."))

    def use_them(self, folder):
        for title, source, content, kind in (("Word", "page.fodt", PAGE, "docx"), ("PowerPoint", "slides.fodp", SLIDE, "pptx")):
            (folder / source).write_text(content, encoding="utf-8")
            office = tools.office_convert(folder / source, kind, folder)  # make a made-up Office file first
            pdf = tools.office_convert(office, "pdf", folder)
            if not pdf.read_bytes().startswith(b"%PDF"):
                raise tools.ToolError(f"{title} to PDF did not make a PDF.")
            self.stdout.write(f"  {title} to PDF: works")

        picture = tools.office_convert(folder / "page.fodt", "png", folder)
        code, output = tools.tesseract([str(picture), "stdout", "-l", "eng"])
        if code != 0 or "safe documents" not in output.lower():
            raise tools.ToolError("Tesseract could not read the test page.")
        self.stdout.write("  Reading a picture: works")
        code, output = tools.tesseract(["--list-langs"])
        languages = [line.strip() for line in output.splitlines()[1:] if line.strip() not in ("", "osd")]
        self.stdout.write(f"  Reading languages: {', '.join(languages)}")
