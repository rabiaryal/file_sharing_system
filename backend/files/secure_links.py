"""
Stateless HMAC-SHA256 based secure link engine.
Tokens are cryptographically signed and include expiry information,
eliminating the need for database lookups or state tracking.
"""

import hmac
import hashlib
import time
import structlog
from django.conf import settings

log = structlog.get_logger(__name__)


class SimpleLinkEngine:
    """
    Generates and verifies cryptographically secure tokens without storing state.
    Uses HMAC-SHA256 with Django's SECRET_KEY for symmetric signing.
    """

    @staticmethod
    def generate_token(file_id: int, execution_window_seconds: int = 3600) -> str:
        expiry_time = int(time.time()) + execution_window_seconds
        raw_payload = f"{file_id}-{expiry_time}"
        signature = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            raw_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        token = f"{raw_payload}-{signature}"

        log.info(
            "secure_token_generated",
            file_id=file_id,
            expires_in_seconds=execution_window_seconds,
            expiry_timestamp=expiry_time,
        )
        return token

    @staticmethod
    def verify_token(token: str) -> int | None:
        try:
            parts = token.split("-")
            if len(parts) < 3:
                log.warning("token_malformed", reason="insufficient_parts", parts_count=len(parts))
                return None

            file_id = parts[0]
            expiry_time = parts[1]
            provided_signature = "-".join(parts[2:])
            rebuilt_payload = f"{file_id}-{expiry_time}"

            expected_signature = hmac.new(
                settings.SECRET_KEY.encode('utf-8'),
                rebuilt_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_signature, provided_signature):
                log.warning("token_invalid", reason="signature_mismatch", file_id=file_id)
                return None

            if int(time.time()) > int(expiry_time):
                log.warning("token_expired", file_id=file_id, expiry_timestamp=expiry_time)
                return None

            log.info("token_verified", file_id=int(file_id))
            return int(file_id)

        except (ValueError, AttributeError, IndexError) as e:
            log.warning("token_parse_error", error=str(e))
            return None