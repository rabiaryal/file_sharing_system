"""
Middleware for verifying stateless secure tokens before they reach views.
This gatekeeper pattern ensures expired or tampered tokens are rejected
at the middleware layer before expensive view operations occur.
"""

import structlog
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .secure_links import SimpleLinkEngine

log = structlog.get_logger(__name__)


class SecureTokenMiddleware(MiddlewareMixin):
    """
    Intercepts requests with 'token' parameter and verifies them cryptographically.
    If verification fails, immediately returns 403 Forbidden.
    If verification succeeds, attaches verified_file_id to the request object.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'token' not in view_kwargs:
            return None

        token = view_kwargs['token']
        file_id = SimpleLinkEngine.verify_token(token)

        if file_id is None:
            log.warning(
                "secure_token_rejected",
                path=request.path,
                method=request.method,
                ip=request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR"),
            )
            return JsonResponse(
                {
                    "error": "Link Invalid or Expired",
                    "detail": "This link has either been modified or its access window has closed.",
                },
                status=403,
            )

        log.info("secure_token_accepted", file_id=file_id, path=request.path)
        request.verified_file_id = file_id
        return None