"""JWT helpers for the users app."""

from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
import structlog

log = structlog.get_logger(__name__)

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


def build_tokens_for_user(user):
    log.info("tokens_built", user_id=user.id)
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def set_token_cookies(response, tokens):
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        tokens["access"],
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        tokens["refresh"],
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
    )
    return response


def clear_token_cookies(response):
    response.delete_cookie(ACCESS_COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)
    return response


def extract_bearer_token(request):
    authorization = request.META.get("HTTP_AUTHORIZATION", "")
    if authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def get_access_token(request):
    return extract_bearer_token(request) or request.COOKIES.get(ACCESS_COOKIE_NAME)


def get_refresh_token(request):
    return request.COOKIES.get(REFRESH_COOKIE_NAME)


def blacklist_refresh_token(refresh_token: str) -> None:
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        log.info("token_blacklisted")
    except TokenError as e:
        log.warning("token_blacklist_failed", error=str(e))
        return