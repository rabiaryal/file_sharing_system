from celery import shared_task
from .models import CompressedPDF, ShareLink
from .services import get_supabase_client
import structlog
import tempfile
import os
import pikepdf
from django.utils import timezone
from django.contrib.auth import get_user_model

log = structlog.get_logger(__name__)

@shared_task
def compress_pdf_task(record_id: int):
    try:
        record = CompressedPDF.objects.get(id=record_id)
        log.info("pdf_compression_started", record_id=record_id, original_size=record.original_size)

        client = get_supabase_client()
        bucket = client.storage.from_(os.getenv("SUPABASE_BUCKET", "public"))

        # 1. Download original file from Supabase
        file_bytes = bucket.download(record.storage_path)

        # 2. Compress using pikepdf
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
            tmp_in.write(file_bytes)
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path.replace(".pdf", "_compressed.pdf")

        with pikepdf.open(tmp_in_path) as pdf:
            pdf.save(tmp_out_path, compress_streams=True, recompress_flate=True)

        # 3. Upload compressed file back to Supabase
        compressed_path = record.storage_path.replace("raw/", "compressed/")
        with open(tmp_out_path, "rb") as f:
            bucket.upload(compressed_path, f, {"content-type": "application/pdf"})

        compressed_size = os.path.getsize(tmp_out_path)

        # 4. Cleanup temp files
        os.unlink(tmp_in_path)
        os.unlink(tmp_out_path)

        # 5. Update record
        record.compressed_size = compressed_size
        record.status = "COMPLETED"
        record.supabase_url = compressed_path
        record.save()

        log.info(
            "pdf_compression_completed",
            record_id=record_id,
            original_size=record.original_size,
            compressed_size=compressed_size,
            reduction_pct=round((1 - compressed_size / record.original_size) * 100, 2),
        )

    except CompressedPDF.DoesNotExist:
        log.warning("pdf_compression_record_not_found", record_id=record_id)
        return None
    except Exception as e:
        log.error("pdf_compression_failed", record_id=record_id, error=str(e), exc_info=True)
        raise


@shared_task
def self_destruct_task(pdf_id: int):
    try:
        pdf = CompressedPDF.objects.get(id=pdf_id)

        # Delete from Supabase storage too
        client = get_supabase_client()
        bucket = client.storage.from_(os.getenv("SUPABASE_BUCKET", "public"))

        # Delete from Supabase storage too
        bucket.remove([pdf.storage_path])

        # Delete DB record
        pdf.delete()
        log.info("pdf_self_destructed", pdf_id=pdf_id)
        return True

    except CompressedPDF.DoesNotExist:
        log.warning("pdf_self_destruct_not_found", pdf_id=pdf_id)
        return False
    except Exception as e:
        log.error("pdf_self_destruct_failed", pdf_id=pdf_id, error=str(e), exc_info=True)
        raise


@shared_task
def write_back_sync_task():
    log.info("write_back_sync_task_started")
    log.info("write_back_sync_task_completed")
    return True


@shared_task
def cleanup_expired_links_and_users():
    log.info("cleanup_expired_links_started")
    now = timezone.now()
    expired_links = ShareLink.objects.filter(expires_at__lte=now)
    expired_count = expired_links.count()

    if expired_count == 0:
        log.info("cleanup_expired_links_completed", deleted_count=0)
        return True

    client = get_supabase_client()
    bucket = client.storage.from_(os.getenv("SUPABASE_BUCKET", "public"))
    User = get_user_model()

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

    log.info("cleanup_expired_links_completed", deleted_count=expired_count)
    return True