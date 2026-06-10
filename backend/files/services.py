import os
import structlog
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "public")

log = structlog.get_logger(__name__)

_supabase = None

def get_supabase_client():
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            log.warning("supabase_credentials_missing")
            return None
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


def make_presigned_upload(path: str, content_type: str = "application/pdf") -> dict:
    """Return a dict with `upload_url` and `path` for a signed upload, or None if unconfigured."""
    client = get_supabase_client()
    if not client:
        log.warning("presigned_upload_failed_no_client", path=path)
        return {"upload_url": None, "path": path}

    bucket = client.storage.from_(SUPABASE_BUCKET)

    if hasattr(bucket, "create_signed_upload_url"):
        res = bucket.create_signed_upload_url(path)
        if res:
            log.info("presigned_upload_created", path=path)
            return {"upload_url": res.get("signed_url") or res.get("signedURL") or res.get("url"), "path": path}

    log.warning("presigned_upload_not_supported", path=path)
    return {"upload_url": None, "path": path}


def make_presigned_download(path: str, expires_in: int = 60) -> str | None:
    """Return a short-lived signed download URL for a private Supabase bucket."""
    client = get_supabase_client()
    if not client:
        log.warning("presigned_download_failed_no_client", path=path)
        return None

    bucket = client.storage.from_(SUPABASE_BUCKET)
    response = bucket.create_signed_url(path, expires_in)
    if isinstance(response, dict):
        log.info("presigned_download_created", path=path, expires_in=expires_in)
        return response.get("signedUrl") or response.get("signedURL") or response.get("signed_url")
    log.warning("presigned_download_failed", path=path)
    return None
