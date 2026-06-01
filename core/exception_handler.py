import sys
import traceback
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


def global_api_exception_handler(exc, context):
    """
    Transforms EVERY backend crash into a clean, structural JSON error message.
    """
    # 1. Call DRF's default exception handler first to get the standard error response
    response = drf_exception_handler(exc, context)

    # 2. If response is None, it means Django crashed violently on an unhandled exception (500)
    if response is None:
        # Extract the deep Python traceback data
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Explicitly print the full traceback to the server stderr so hosting logs capture it
        print("\n=== !!! CRITICAL API CRASH !!! ===", file=sys.stderr)
        print(formatted_traceback, file=sys.stderr)
        print("==================================\n", file=sys.stderr)

        payload = {
            "status": "error",
            "error_type": exc.__class__.__name__,
            "message": str(exc),
        }

        # Only include debug_traceback when DEBUG is truthy to avoid leaking internals in prod
        if getattr(settings, "DEBUG", False):
            payload["debug_traceback"] = formatted_traceback

        return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 3. For expected API errors (like 400 Bad Request, 401 Unauthorized), structure them cleanly
    return Response({
        "status": "fail",
        "error_type": exc.__class__.__name__,
        "details": response.data,
    }, status=response.status_code)
