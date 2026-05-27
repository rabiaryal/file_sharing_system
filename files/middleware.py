"""
Middleware for verifying stateless secure tokens before they reach views.
This gatekeeper pattern ensures expired or tampered tokens are rejected
at the middleware layer before expensive view operations occur.
"""

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .secure_links import SimpleLinkEngine


class SecureTokenMiddleware(MiddlewareMixin):
    """
    Intercepts requests with 'token' parameter and verifies them cryptographically.
    If verification fails, immediately returns 403 Forbidden.
    If verification succeeds, attaches verified_file_id to the request object.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Called before the view function executes.
        Intercepts routes containing our custom 'token' parameter.
        """
        # Only process routes that have a 'token' parameter
        if 'token' in view_kwargs:
            token = view_kwargs['token']

            # Run the cryptographic verification
            file_id = SimpleLinkEngine.verify_token(token)

            if file_id is None:
                # Token is invalid, expired, or tampered with
                return JsonResponse(
                    {
                        "error": "Link Invalid or Expired",
                        "detail": "This link has either been modified or its access window has closed.",
                    },
                    status=403,
                )

            # Token is valid! Store the verified file_id for the view to use
            request.verified_file_id = file_id

        return None
