"""Looks inside a Word or PowerPoint file before anything opens it (SR-08, SR-09, SR-14, AC-03, AC-05).

Such a file is a zip. It is refused when it is not really that kind of document, is damaged or locked, grows
too much when opened, or holds XML that declares its own entities.
"""
import re
import zipfile
import zlib

from django.conf import settings

MAIN_PART = {"docx": "word/document.xml", "pptx": "ppt/presentation.xml"}
SLIDE = re.compile(r"ppt/slides/slide\d+\.xml$", re.IGNORECASE)
MAX_PARTS = 2000
MAX_XML_PART = 50 * 1024 * 1024
FORBIDDEN = tuple(word.encode(coding) for word in ("<!DOCTYPE", "<!ENTITY") for coding in ("utf-8", "utf-16-le", "utf-16-be"))


class Refused(Exception):
    pass


def is_xml(name):
    return name.lower().endswith((".xml", ".rels", ".vml"))


def check(upload, kind, name):
    wrong = Refused(f"Its name says {name}, but the content is something else.")
    damaged = Refused("This file is damaged, or locked with a password.")
    upload.seek(0)
    try:
        with zipfile.ZipFile(upload) as package:
            parts = package.infolist()
            names = [part.filename for part in parts]
            if len(parts) > MAX_PARTS:
                raise Refused("This file has too many parts inside.")
            # "mimetype" marks another family of documents (OpenDocument), which could be opened as that instead.
            if "[Content_Types].xml" not in names or MAIN_PART[kind] not in names or "mimetype" in names:
                raise wrong
            if len(names) != len(set(names)) or any(part.flag_bits & 0x1 for part in parts):
                raise damaged
            grown = sum(part.file_size for part in parts)
            if grown > settings.MAX_EXPANDED_BYTES or grown > upload.size * settings.MAX_EXPANSION:
                raise Refused("This file grows far too much when opened.")
            if kind == "pptx" and sum(1 for n in names if SLIDE.match(n)) > settings.MAX_PAGES:
                raise Refused(f"This file has more than {settings.MAX_PAGES} slides.")
            for part in parts:
                _read_through(package, part)
    except (zipfile.BadZipFile, zlib.error, NotImplementedError, EOFError, ValueError, OSError):
        raise damaged from None
    finally:
        upload.seek(0)


def _read_through(package, part):
    """Reads every part to the end, so a false size or a broken part shows now and not later."""
    xml = is_xml(part.filename)
    if xml and part.file_size > MAX_XML_PART:
        raise Refused("This file grows far too much when opened.")
    tail = b""
    with package.open(part) as content:
        while block := content.read(1024 * 1024):
            if xml:
                window = tail + block
                if any(word in window for word in FORBIDDEN):
                    raise Refused("This file holds instructions that Doc2All does not open.")
                tail = window[-20:]
