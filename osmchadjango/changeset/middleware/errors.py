from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse


class ExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if not isinstance(exception, ValidationError):
            return None  # no special handling
        else:
            return HttpResponse(exception.messages, status=401)
