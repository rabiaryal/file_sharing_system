from django.db import models
from django.conf import settings
import uuid

class CompressedPDF(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    original_name = models.CharField(max_length=255)
    status = models.CharField(max_length=15, default="PENDING")
    storage_path = models.CharField(max_length=500)
    supabase_url = models.URLField(blank=True, null=True)
    original_size = models.BigIntegerField()
    compressed_size = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

class ShareLink(models.Model):
    """
    Metadata about a shared file.
    Note: The actual token is generated on-the-fly using HMAC-SHA256,
    not stored in the database. This model tracks the file metadata only.
    """
    pdf_record = models.ForeignKey(CompressedPDF, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
