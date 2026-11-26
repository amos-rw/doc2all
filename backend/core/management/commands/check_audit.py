"""Checks the audit log fingerprints. Run: python backend/manage.py check_audit"""
from django.core.management.base import BaseCommand, CommandError

from core import audit
from core.models import AuditLine


class Command(BaseCommand):
    help = "Reports any audit line that was changed or removed in the database."

    def handle(self, *args, **options):
        broken = audit.broken_lines()
        if broken:
            raise CommandError(f"The audit log was altered before line(s): {', '.join(map(str, broken))}")
        self.stdout.write(self.style.SUCCESS(f"{AuditLine.objects.count()} lines, none altered."))
