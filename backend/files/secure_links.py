"""
Stateless HMAC-SHA256 based secure link engine.
Tokens are cryptographically signed and include expiry information,
eliminating the need for database lookups or state tracking.
"""

import hmac
import hashlib
import time
from django.conf import settings


class SimpleLinkEngine:
    """
    Generates and verifies cryptographically secure tokens without storing state.
    Uses HMAC-SHA256 with Django's SECRET_KEY for symmetric signing.
    """

    @staticmethod
    def generate_token(file_id: int, execution_window_seconds: int = 3600) -> str:
        """
        Creates a secure token combining file_id, expiry, and an HMAC signature.
        
        Args:
            file_id: The ID of the file to share
            execution_window_seconds: How long the link remains valid (default: 1 hour)
        
        Returns:
            A token string in format: "file_id-expiry_timestamp-signature"
        """
        # 1. Calculate expiration timestamp (current time + window)
        expiry_time = int(time.time()) + execution_window_seconds
        
        # 2. Construct the raw string payload (using hyphens for URL compatibility)
        raw_payload = f"{file_id}-{expiry_time}"
        
        # 3. Sign the payload using Django's SECRET_KEY with SHA-256
        signature = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            raw_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 4. Return the combined token string
        return f"{raw_payload}-{signature}"

    @staticmethod
    def verify_token(token: str) -> int | None:
        """
        Validates the signature and checks expiration.
        Uses constant-time comparison to prevent timing attacks.
        
        Args:
            token: The token string to verify
        
        Returns:
            The file_id (int) if valid, None if invalid/expired/tampered
        """
        try:
            # Parse the token: "file_id-expiry_time-signature"
            parts = token.split("-")
            if len(parts) < 3:
                return None
            
            # The signature is everything after the second hyphen (in case signature has hyphens)
            file_id = parts[0]
            expiry_time = parts[1]
            provided_signature = "-".join(parts[2:])
                
            # Reconstruct the exact string payload we expect
            rebuilt_payload = f"{file_id}-{expiry_time}"
            
            # Re-calculate what the signature should be
            expected_signature = hmac.new(
                settings.SECRET_KEY.encode('utf-8'),
                rebuilt_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Check 1: Constant-time comparison (prevents tampering/timing attacks)
            if not hmac.compare_digest(expected_signature, provided_signature):
                return None
                
            # Check 2: Has the link expired? (prevents outdated access)
            if int(time.time()) > int(expiry_time):
                return None
                
            # Convert file_id to integer and return
            return int(file_id)
            
        except (ValueError, AttributeError, IndexError):
            # Malformed token or conversion errors
            return None
