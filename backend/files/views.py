"""The calls for files and work (docs/design/server-interfaces.md). Answers look like docs/design/api-examples.md.

Not yet checked here: who is asking. Accounts bring the sign-in and the owner check.
"""
from datetime import timedelta

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core.errors import Problem

from . import gate, storage, work
from .models import Job, StoredFile

TYPES = {"pdf": "application/pdf"}
DID = {"convert": "Convert"}
STEPS = ["I checked what the file really is", "I opened a copy to work on", "Converting", "Checking the result"]
# kind -> (all is well, title, detail, tag)
FINDINGS = {
    "converted": (True, "Converted to PDF", "Made from a copy of your file.", "Done"),
    "not_checked": (False, "Not checked for hidden content", "That check is not built yet.", "Not checked"),
    "could_not_convert": (False, "This file could not be converted", "It may be damaged or protected by a password.", "Failed"),
    "deleted_meanwhile": (False, "The file was deleted", "Nothing was made from it.", "Stopped"),
}


def _ms(moment):
    return int(moment.timestamp() * 1000)


def _live_file(file_id):
    record = get_object_or_404(StoredFile, pk=file_id)
    if record.gone:
        raise Problem(404, "not_found", "This file was deleted.")
    return record


def _job(job_id):
    job = get_object_or_404(Job.objects.select_related("file"), pk=job_id)
    # A job cut off by a server restart must not look busy for ever.
    if job.status in (Job.WAITING, Job.RUNNING) and timezone.now() - job.started_at > timedelta(seconds=settings.CONVERTER_TIMEOUT * 3):
        work._finish(job.id, Job.FAILED, "failed", ["could_not_convert"], error="interrupted")
        job.refresh_from_db()
    return job


@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload(request):
    storage.purge_expired()
    sent = request.FILES.get("file")
    if sent is None:
        raise Problem(400, "no_file", "Choose a file.")
    try:
        name, kind = gate.check(sent)
    except gate.Refused as refusal:
        raise Problem(400, "refused", str(refusal)) from None
    record = storage.save(sent.chunks(), shown_name=name, kind=kind)
    return Response({"id": record.id, "name": name, "kind": kind, "size": record.size, "expiresAt": _ms(record.delete_after),
                     "allowed": gate.READY[kind], "soon": gate.SOON[kind]})


@api_view(["DELETE"])
def delete_file(request, file_id):
    record = _live_file(file_id)
    storage.remove_with_results(record.job.file if record.job else record)
    return Response({"deletedAt": _ms(timezone.now())})


@api_view(["GET"])
def download(request, file_id):
    storage.purge_expired()
    record = _live_file(file_id)
    try:
        content = open(storage.path_of(record), "rb")
    except FileNotFoundError:
        raise Problem(404, "not_found", "This file was deleted.") from None
    response = FileResponse(content, as_attachment=True, filename=record.shown_name, content_type=TYPES.get(record.kind, "application/octet-stream"))
    response["Cache-Control"] = "no-store"
    return response


@api_view(["POST"])
def start_job(request):
    data = request.data if isinstance(request.data, dict) else {}
    record = _live_file(str(data.get("fileId", "")))
    asked = data.get("actions")
    if not isinstance(asked, list) or not asked:
        raise Problem(400, "no_action", "Choose what to do with the file.")
    if record.job or any(action not in gate.READY[record.kind] for action in asked):
        raise Problem(400, "not_ready", "That cannot be done with this file yet.")
    job = Job.objects.create(file=record, actions=list(dict.fromkeys(asked)))
    work.start(job)
    return Response({"id": job.id})


@api_view(["GET"])
def job_state(request, job_id):
    job = _job(job_id)
    status = job.status if job.status in (Job.DONE, Job.FAILED) else "working"
    steps = [{"label": label, "state": "done" if i < job.stage else "now" if i == job.stage else "waiting"} for i, label in enumerate(STEPS)]
    return Response({"id": job.id, "status": status, "progress": job.stage / len(STEPS), "steps": steps})


@api_view(["GET"])
def report(request, job_id):
    job = _job(job_id)
    found = getattr(job, "report", None)
    if found is None:
        raise Problem(404, "not_ready", "The report is not ready yet.")
    result = job.results.first()
    lines = [dict(zip(("ok", "title", "detail", "tag"), FINDINGS[line.kind])) for line in found.findings.all()]
    return Response({"jobId": job.id, "fileId": job.file.id, "resultId": result.id if result else None, "fileName": job.file.shown_name,
                     "actions": job.actions, "outcome": found.result, "findings": lines, "expiresAt": _ms(job.file.delete_after),
                     "fileDeleted": job.file.gone})


@api_view(["GET"])
def history(request):
    storage.purge_expired()
    latest = {}
    for job in Job.objects.filter(report__isnull=False).select_related("file", "report").order_by("started_at"):
        latest[job.file_id] = job
    items = []
    for job in sorted(latest.values(), key=lambda j: j.started_at, reverse=True):
        result = job.results.first()
        items.append({"id": job.id, "jobId": job.id, "fileId": job.file.id, "resultId": result.id if result else None,
                      "name": job.file.shown_name, "did": ", ".join(DID[a] for a in job.actions), "outcome": job.report.result,
                      "expiresAt": _ms(job.file.delete_after), "deleted": job.file.gone})
    return Response({"items": items})


@api_view(["DELETE"])
def remove_history(request, job_id):
    source = _job(job_id).file
    storage.remove_with_results(source)
    source.delete()  # takes its jobs, results, reports and findings with it
    return Response({"ok": True})
