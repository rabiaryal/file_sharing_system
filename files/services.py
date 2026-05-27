import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "public")

_supabase = None

def get_supabase_client():
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return None
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


def make_presigned_upload(path: str, content_type: str = "application/pdf") -> dict:
    """Return a dict with `upload_url` and `path` for a signed upload, or None if unconfigured."""
    client = get_supabase_client()
    if not client:
        return {"upload_url": None, "path": path}

    bucket = client.storage.from_(SUPABASE_BUCKET)

    if hasattr(bucket, "create_signed_upload_url"):
        res = bucket.create_signed_upload_url(path)
        if res:
            return {"upload_url": res.get("signed_url") or res.get("signedURL") or res.get("url"), "path": path}

    return {"upload_url": None, "path": path}


def make_presigned_download(path: str, expires_in: int = 60) -> str | None:
    """Return a short-lived signed download URL for a private Supabase bucket."""
    client = get_supabase_client()
    if not client:
        return None

    bucket = client.storage.from_(SUPABASE_BUCKET)
    response = bucket.create_signed_url(path, expires_in)
    if isinstance(response, dict):
        return response.get("signedUrl") or response.get("signedURL") or response.get("signed_url")
    return None
