"""Files, the work done on them, and the safety report (docs/design/data-model.md).

There is no owner yet: it arrives with the accounts, together with the owner check.
"""
import secrets

from django.db import models
from django.utils import timezone


def new_id():
    return secrets.token_urlsafe(16)  # random, 128 bits (SR-05)


class StoredFile(models.Model):
    """The record of one file. The content sits in the private folder under another random name."""

    id = models.CharField(primary_key=True, max_length=22, default=new_id, editable=False)
    job = models.ForeignKey("Job", null=True, blank=True, on_delete=models.CASCADE, related_name="results")  # set for a result
    shown_name = models.CharField(max_length=120)  # for display only, never a path
    stored_name = models.CharField(max_length=32, unique=True)
    kind = models.CharField(max_length=4)  # decided from the first bytes
    size = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    delete_after = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True, blank=True)  # set when the content is gone

    @property
    def gone(self):
        return self.deleted_at is not None or timezone.now() >= self.delete_after


class Job(models.Model):
    WAITING, RUNNING, DONE, FAILED = "waiting", "running", "done", "failed"

    id = models.CharField(primary_key=True, max_length=22, default=new_id, editable=False)
    file = models.ForeignKey(StoredFile, on_delete=models.CASCADE, related_name="jobs")  # the upload
    actions = models.JSONField(default=list)
    status = models.CharField(max_length=8, default=WAITING)
    stage = models.PositiveSmallIntegerField(default=0)  # how many of the four steps are finished
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=32, blank=True)  # a code, never file content


class Report(models.Model):
    id = models.CharField(primary_key=True, max_length=22, default=new_id, editable=False)
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name="report")
    result = models.CharField(max_length=16)
    created_at = models.DateTimeField(default=timezone.now)


class Finding(models.Model):
    """One line of a report. The words come from the kind, so nothing found in a file is ever saved (SR-19)."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="findings")
    kind = models.CharField(max_length=32)
    how_many = models.PositiveIntegerField(default=1)
