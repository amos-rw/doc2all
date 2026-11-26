"""The form token: a change is accepted only with the token that our own page holds, from our own address."""
from rest_framework.authentication import CSRFCheck
from rest_framework.permissions import BasePermission

from .errors import Problem


class FormToken(BasePermission):
    def has_permission(self, request, view):
        check = CSRFCheck(lambda _request: None)
        check.process_request(request)
        if check.process_view(request, None, (), {}):  # a reason means "refused"; reading is always let through
            raise Problem(403, "token", "The page is out of date. Please try again.")
        return True
