from django.conf import settings
from django.http import Http404
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import tools


@api_view(["GET"])
def session(request):
    """Who am I, and the form token. There are no accounts yet, so nobody is signed in."""
    return Response({"state": "signed_out", "formToken": get_token(request)})


@api_view(["GET"])
def dev_health(request):
    """A helper for developers: is the server up, and are the processing programs installed?

    It exists only in development mode and never says where anything is on the computer.
    """
    if not settings.DEBUG:
        raise Http404
    return Response({"server": "ok", "tools": {name: tools.find(name) is not None for name in tools.PROGRAMS}})
