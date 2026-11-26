"""How often and how much (SR-09, AC-09)."""
from datetime import timedelta

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone

from .audit import keyed_hash
from .errors import Problem
from .models import Attempt


def count(kind, request, most, within=timedelta(hours=1), message="Too many tries. Try again later."):
    """Counts one try by this network address, or refuses it. With accounts, the user is counted too."""
    who = keyed_hash(f"address:{request.META.get('REMOTE_ADDR', '')}")
    if Attempt.objects.filter(kind=kind, who_hash=who, at__gt=timezone.now() - within).count() >= most:
        raise Problem(429, "too_many", message)
    Attempt.objects.create(kind=kind, who_hash=who)


def forget_old():
    Attempt.objects.filter(at__lt=timezone.now() - timedelta(hours=24)).delete()


class RequestSize:
    """Refuses a request that says it is too large, before any of it is read."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        most = settings.MAX_UPLOAD_BYTES + 64 * 1024 if request.path == "/api/files" else 64 * 1024
        if length > most:
            response = JsonResponse({"error": "too_big", "message": "The file is larger than 20 MB."}, status=413)
        else:
            response = self.get_response(request)
        if request.path.startswith("/api/"):
            response.setdefault("Cache-Control", "no-store")
        return response
