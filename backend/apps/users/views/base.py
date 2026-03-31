from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.views import APIView


class ServiceAPIView(APIView):
    def handle_exception(self, exc):
        if isinstance(exc, DjangoValidationError):
            if hasattr(exc, "message_dict"):
                exc = ValidationError(exc.message_dict)
            elif hasattr(exc, "messages"):
                exc = ValidationError(exc.messages)
            else:
                exc = ValidationError(str(exc))
        elif isinstance(exc, DjangoPermissionDenied):
            exc = PermissionDenied(str(exc))
        elif isinstance(exc, Http404):
            exc = NotFound()

        return super().handle_exception(exc)
