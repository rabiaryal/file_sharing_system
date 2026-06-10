import sys
import traceback
import structlog
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

log = structlog.get_logger(__name__)


def global_api_exception_handler(exc, context):
    """
    Transforms EVERY backend crash into a clean, structural JSON error message.
    """
    view = context.get("view")
    request = context.get("request")

    # 1. Call DRF's default exception handler first
    response = drf_exception_handler(exc, context)

    # 2. Unhandled exception — 500 crash
    if response is None:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        log.error(
            "unhandled_exception",
            exc_type=exc.__class__.__name__,
            exc_message=str(exc),
            view=view.__class__.__name__ if view else None,
            method=request.method if request else None,
            path=request.path if request else None,
            exc_info=True,   # captures full traceback into MongoDB doc
        )

        payload = {
            "status": "error",
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }
        if getattr(settings, "DEBUG", False):
            payload["debug_traceback"] = formatted_traceback

        return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 3. Expected API errors (400, 401, 403, 404 …)
    # Only log 5xx on this path — 4xx are the client's fault, warning is enough
    if response.status_code >= 500:
        log.error(
            "api_error",
            exc_type=exc.__class__.__name__,
            status_code=response.status_code,
            view=view.__class__.__name__ if view else None,
            method=request.method if request else None,
            path=request.path if request else None,
            exc_info=True,
        )
    else:
        log.warning(
            "api_client_error",
            exc_type=exc.__class__.__name__,
            status_code=response.status_code,
            view=view.__class__.__name__ if view else None,
            method=request.method if request else None,
            path=request.path if request else None,
        )

    return Response({
        "status": "fail",
        "error_type": exc.__class__.__name__,
        "details": response.data,
    }, status=response.status_code)