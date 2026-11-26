"""Every refused call answers the same way: a status, and {"error": code, "message": plain words}."""
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class Problem(APIException):
    def __init__(self, status_code, code, message):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


PLAIN = {400: ("bad_request", "Something in the request is wrong."), 404: ("not_found", "Not found."), 405: ("not_allowed", "Not allowed.")}


def handler(error, context):
    response = exception_handler(error, context)
    if response is None:
        return None  # an unexpected error: Django answers 500, without details outside development
    if isinstance(error, Problem):
        response.data = {"error": error.code, "message": error.message}
    else:
        code, message = PLAIN.get(response.status_code, ("refused", "The request was refused."))
        response.data = {"error": code, "message": message}
    return response
