"""Adds lines to the audit log and checks that none was changed.

Each line holds a keyed fingerprint of the line before it. Changing or removing a line in the middle breaks
the chain. It cannot show that the newest lines were cut off (see the data model).
"""
import hashlib
import hmac
import threading

from django.conf import settings
from django.db import transaction

from .models import AuditLine

_one_writer = threading.Lock()


def keyed_hash(text):
    return hmac.new(settings.AUDIT_KEY.encode(), text.encode(), hashlib.sha256).hexdigest()


def _fingerprint(line):
    return keyed_hash("|".join([str(line.pk), line.at.isoformat(), line.actor_id, line.action, line.result, line.target_id, line.previous_hash]))


def record(action, result="OK", target="", actor=""):
    with _one_writer, transaction.atomic():
        last = AuditLine.objects.select_for_update().order_by("-pk").first()
        AuditLine.objects.create(action=action, result=result, target_id=target, actor_id=actor, previous_hash=_fingerprint(last) if last else "")


def broken_lines():
    """The numbers of the lines whose link to the line before no longer holds."""
    broken, before = [], None
    for line in AuditLine.objects.order_by("pk").iterator():
        expected = _fingerprint(before) if before else ""
        if not hmac.compare_digest(line.previous_hash, expected):
            broken.append(line.pk)
        before = line
    return broken
