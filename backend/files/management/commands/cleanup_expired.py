from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from files.models import ShareLink, CompressedPDF
from files.services import get_supabase_client
import os
import structlog

log = structlog.get_logger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = "Cleans up expired share links, Supabase files, and orphaned guest users."

    def handle(self, *args, **options):
        log.info("cleanup_expired_command_started")
        now = timezone.now()
        expired_links = ShareLink.objects.filter(expires_at__lte=now)
        expired_count = expired_links.count()

        if expired_count == 0:
            log.info("cleanup_expired_command_completed", deleted_count=0)
            return

        client = get_supabase_client()
        bucket = client.storage.from_(os.getenv("SUPABASE_BUCKET", "public"))

        for link in expired_links:
            pdf = link.pdf_record
            user = pdf.user
            try:
                raw_path = pdf.storage_path
                try:
                    bucket.remove([raw_path])
                except Exception as storage_err:
                    log.warning("supabase_file_deletion_failed", path=raw_path, error=str(storage_err))

                pdf.delete()
                log.info("pdf_record_deleted", pdf_id=pdf.id)

                if not CompressedPDF.objects.filter(user=user).exists():
                    user.delete()
                    log.info("ephemeral_user_deleted", user_id=user.id)
            except Exception as e:
                log.error("cleanup_item_failed", pdf_id=pdf.id, error=str(e))

        log.info("cleanup_expired_command_completed", deleted_count=expired_count)
