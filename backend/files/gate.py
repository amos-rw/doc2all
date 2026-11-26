"""The one door for files. The server decides the type from the name and the first bytes, never the browser.

Adapted from the upload checks of Cohortly. Still to add when the work is protected: page limit, upload rate,
bomb checks and a look inside Office files.
"""
from pathlib import PurePath

from django.conf import settings

FIRST_BYTES = {
    "pdf": b"%PDF",
    "docx": b"PK\x03\x04",
    "pptx": b"PK\x03\x04",
    "png": b"\x89PNG",
    "jpg": b"\xff\xd8\xff",
}
# What can be done today, and what is still being built, for each kind of file.
READY = {"docx": ["convert"], "pptx": ["convert"], "pdf": [], "png": [], "jpg": []}
SOON = {
    "docx": ["clean", "blackout"], "pptx": ["clean", "blackout"], "pdf": ["convert", "clean", "scan", "blackout"],
    "png": ["clean", "scan"], "jpg": ["clean", "scan"],
}


class Refused(Exception):
    """Why a file was not accepted, in words that are safe to show."""


def clean_name(name):
    """A name fit to show: no folders, no control characters, not too long."""
    name = PurePath(str(name).replace("\\", "/")).name
    name = "".join(c for c in name if c.isprintable()).strip() or "file"
    if len(name) <= 120:
        return name
    suffix = PurePath(name).suffix[:10]
    return name[: 120 - len(suffix)] + suffix


def check(upload):
    """Returns (shown name, kind), or raises Refused."""
    name = clean_name(upload.name)
    kind = PurePath(name).suffix.lower().lstrip(".")
    kind = "jpg" if kind == "jpeg" else kind
    if kind not in FIRST_BYTES:
        raise Refused("Only PDF, Word, PowerPoint, PNG and JPG files are accepted.")
    if upload.size > settings.MAX_UPLOAD_BYTES:
        raise Refused("The file is larger than 20 MB.")
    upload.seek(0)
    start = upload.read(8)
    upload.seek(0)
    if start.startswith(b"MZ"):
        raise Refused(f"Its name says {name}, but it is a program.")
    if not start.startswith(FIRST_BYTES[kind]):
        raise Refused(f"Its name says {name}, but the content is something else.")
    return name, kind
