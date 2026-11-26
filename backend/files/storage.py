"""The private folder. Content is kept under random names, outside anything the web server serves."""
import secrets
import shutil
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from core import audit

from .models import StoredFile

KEEP_FOR = timedelta(hours=24)


def path_of(record):
    return Path(settings.PRIVATE_FILES_DIR) / record.stored_name


def save(chunks, *, shown_name, kind, job=None, delete_after=None):
    """Writes the content under a new random name and returns its record."""
    folder = Path(settings.PRIVATE_FILES_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = secrets.token_hex(16)
    size = 0
    with open(folder / stored_name, "xb") as target:
        for chunk in chunks:
            target.write(chunk)
            size += len(chunk)
    return StoredFile.objects.create(
        job=job, shown_name=shown_name, stored_name=stored_name, kind=kind, size=size,
        delete_after=delete_after or timezone.now() + KEEP_FOR,
    )


def copy_to(record, target):
    shutil.copyfile(path_of(record), target)


def remove_content(record):
    path_of(record).unlink(missing_ok=True)
    if record.deleted_at is None:
        record.deleted_at = timezone.now()
        record.save(update_fields=["deleted_at"])


def remove_with_results(source):
    """The content of an upload and of everything made from it."""
    for record in [source, *StoredFile.objects.filter(job__file=source)]:
        remove_content(record)


def purge_expired():
    """Removes content older than 24 hours. Called by the server's timer, and also when files are used."""
    for record in StoredFile.objects.filter(deleted_at__isnull=True, delete_after__lte=timezone.now()):
        remove_content(record)
        if record.job_id is None:
            audit.record("Delete after 24 hours", target=record.id)
