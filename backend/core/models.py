"""Counters for limits, and the audit log (docs/design/data-model.md)."""
from django.db import models
from django.utils import timezone


class Attempt(models.Model):
    """One try of something that is limited. Removed after 24 hours."""

    kind = models.CharField(max_length=16)
    who_hash = models.CharField(max_length=64)  # a keyed hash, never the address itself
    at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["kind", "who_hash", "at"])]


class AuditLine(models.Model):
    """Who did what, and when. Lines are only added. Ids only: no names, no content (SR-19, SR-20)."""

    at = models.DateTimeField(default=timezone.now)
    actor_id = models.CharField(max_length=22, blank=True)  # empty until there are accounts
    action = models.CharField(max_length=32)
    result = models.CharField(max_length=8)
    target_id = models.CharField(max_length=22, blank=True)
    previous_hash = models.CharField(max_length=64, blank=True)  # fingerprint of the line before

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise TypeError("An audit line cannot be changed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError("An audit line cannot be deleted.")
