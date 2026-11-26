"""Does a job: copies the file into a throwaway folder, runs the program, keeps the result, writes the report."""
import io
import logging
import tempfile
import threading
from pathlib import Path, PurePath

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from pypdf import PdfReader

from core import audit, tools

from . import neutralize, storage
from .models import Finding, Job, Report, StoredFile

log = logging.getLogger(__name__)


def start(job):
    if settings.JOBS_INLINE:
        run(job.id)
    else:
        # In the server process for now. The design puts a separate sandbox runner here.
        threading.Thread(target=_in_thread, args=(job.id,), daemon=True).start()


def _in_thread(job_id):
    try:
        run(job_id)
    finally:
        connection.close()


def _stage(job_id, stage):
    changes = {"started_at": timezone.now()} if stage == 1 else {}
    Job.objects.filter(pk=job_id).update(status=Job.RUNNING, stage=stage, **changes)


def run(job_id):
    try:
        job = Job.objects.select_related("file").get(pk=job_id)
        source = job.file
        _stage(job_id, 1)
        with tempfile.TemporaryDirectory(prefix="doc2all-job-", dir=settings.CONVERTER_WORKDIR or None, ignore_cleanup_errors=True) as folder:
            copy = Path(folder) / f"input.{source.kind}"
            removed = neutralize.safe_copy(storage.path_of(source), copy, source.kind)
            _stage(job_id, 2)
            pdf = tools.office_convert(copy, "pdf", folder)
            _stage(job_id, 3)
            content = pdf.read_bytes()
            if not content.startswith(b"%PDF"):
                raise tools.ToolError("No PDF was made.")
            if len(PdfReader(io.BytesIO(content)).pages) > settings.MAX_PAGES:
                _finish(job_id, Job.FAILED, "failed", {"too_long": 1}, error="too_long")
                return
            _keep(job_id, content, {kind: n for kind, n in removed.items() if n})
    except (Job.DoesNotExist, StoredFile.DoesNotExist):
        return  # removed from History while we were working
    except (tools.ToolError, neutralize.Unreadable):
        _finish(job_id, Job.FAILED, "failed", {"could_not_convert": 1}, error="convert_failed")
    except Exception:  # anything unexpected still ends the job; the log keeps the details, the user does not see them
        log.exception("Job %s failed", job_id)
        _finish(job_id, Job.FAILED, "failed", {"could_not_convert": 1}, error="internal")


def _keep(job_id, content, removed):
    with transaction.atomic():
        job = Job.objects.select_related("file").get(pk=job_id)
        if job.file.gone:  # deleted while we were working: keep nothing
            _finish(job_id, Job.FAILED, "failed", {"deleted_meanwhile": 1}, error="deleted")
            return
        name = f"{PurePath(job.file.shown_name).stem[:100]}.pdf"
        storage.save([content], shown_name=name, kind="pdf", job=job, delete_after=job.file.delete_after)
        _finish(job_id, Job.DONE, "converted", {"converted": 1, **removed, "not_checked": 1})


def _finish(job_id, status, result, found, error=""):
    """Ends a job: `found` is {kind of finding: how many}."""
    if not Job.objects.filter(pk=job_id).update(status=status, stage=4, finished_at=timezone.now(), error_code=error):
        return
    report, _ = Report.objects.get_or_create(job_id=job_id, defaults={"result": result})
    Finding.objects.bulk_create(Finding(report=report, kind=kind, how_many=n) for kind, n in found.items())
    target = Job.objects.values_list("file_id", flat=True).get(pk=job_id)
    audit.record("Convert file", "OK" if status == Job.DONE else "Failed", target)
