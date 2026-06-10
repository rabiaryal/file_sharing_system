"""JWT cookie middleware for request authentication and token rotation."""

import structlog
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .services import build_tokens_for_user, get_access_token, get_refresh_token, set_token_cookies

User = get_user_model()
log = structlog.get_logger(__name__)


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.jwt_tokens = None
        self._authenticate_request(request)
        response = self.get_response(request)
        tokens = getattr(request, "jwt_tokens", None)
        if tokens:
            set_token_cookies(response, tokens)
        return response

    def _authenticate_request(self, request):
        access_token = get_access_token(request)
        if access_token:
            user = self._user_from_access_token(access_token)
            if user is not None:
                request.user = user
                request._cached_user = user
                return

        refresh_token = get_refresh_token(request)
        if not refresh_token:
            return

        rotated_user = self._user_from_refresh_token(request, refresh_token)
        if rotated_user is not None:
            request.user = rotated_user
            request._cached_user = rotated_user

    def _user_from_access_token(self, access_token):
        try:
            token = AccessToken(access_token)
            user_id = token["user_id"]
            user = User.objects.get(pk=user_id)
            if user.is_active:
                return user
        except (InvalidToken, TokenError):
            log.warning("access_token_invalid", reason="token_error")
        except User.DoesNotExist:
            log.warning("access_token_invalid", reason="user_not_found")
        except KeyError:
            log.warning("access_token_invalid", reason="missing_user_id_claim")
        return None

    def _user_from_refresh_token(self, request, refresh_token):
        try:
            token = RefreshToken(refresh_token)
            user_id = token["user_id"]
            user = User.objects.get(pk=user_id)
            if not user.is_active:
                log.warning("refresh_token_rejected", reason="user_inactive", user_id=user_id)
                return None
            request.jwt_tokens = build_tokens_for_user(user)
            log.info("token_rotated", user_id=user.id)
            return user
        except (InvalidToken, TokenError):
            log.warning("refresh_token_invalid", reason="token_error")
        except User.DoesNotExist:
            log.warning("refresh_token_invalid", reason="user_not_found")
        except KeyError:
            log.warning("refresh_token_invalid", reason="missing_user_id_claim")
        return None