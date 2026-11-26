"""The server's own timer: deletes files after 24 hours even when nobody uses the app (SR-18, AC-11)."""
import logging
import re
import shutil
import tempfile
import threading
import time
from pathlib import Path

from django.conf import settings
from django.db import connection

from core import limits, tools

from . import storage
from .models import StoredFile

log = logging.getLogger(__name__)
OURS = re.compile(r"[0-9a-f]{32}")  # the names we give; nothing else is ever deleted
LEFT_OVER_AFTER = 3600


def tidy():
    storage.purge_expired()
    limits.forget_old()
    old = time.time() - LEFT_OVER_AFTER
    folder = Path(settings.PRIVATE_FILES_DIR)
    if folder.is_dir():  # content without a record, left by a crash
        known = set(StoredFile.objects.values_list("stored_name", flat=True))
        for path in folder.iterdir():
            if OURS.fullmatch(path.name) and path.name not in known and path.stat().st_mtime < old:
                path.unlink(missing_ok=True)
    temporary = Path(settings.CONVERTER_WORKDIR or tempfile.gettempdir())
    for pattern, since in (("doc2all-job-*", old), (f"{tools.TEMPLATE_PREFIX}*", time.time() - 24 * 3600)):
        for folder in temporary.glob(pattern):
            if folder.is_dir() and folder.stat().st_mtime < since and not tools.is_current_template(folder):
                shutil.rmtree(folder, ignore_errors=True)


def _loop(every):
    while True:
        try:
            tidy()
        except Exception:  # the timer must keep going
            log.exception("The tidy-up failed")
        finally:
            connection.close()
        time.sleep(every)


def _prepare():
    try:
        tools.office_template()  # so the first job does not wait for LibreOffice's slow first start
    except tools.ToolError:
        log.warning("LibreOffice could not be prepared")


def start(every=60):
    threading.Thread(target=_prepare, daemon=True, name="doc2all-prepare").start()
    threading.Thread(target=_loop, args=(every,), daemon=True, name="doc2all-timer").start()
