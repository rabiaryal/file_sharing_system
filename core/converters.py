"""
Custom URL converters for Django URL routing.
"""

from django.urls.converters import StringConverter


class TokenConverter(StringConverter):
    """
    Custom converter for stateless HMAC tokens.
    
    Token format: <file_id>-<expiry>-<signature>
    Example: 42-1779887140-ce5118942adf07916cccb53f09667439d601...0ed93457
    
    This converter allows hyphens and hex characters in the token.
    """
    regex = regex = r'[^/]+'  # Alphanumeric, hyphens, underscores, 10+ chars
