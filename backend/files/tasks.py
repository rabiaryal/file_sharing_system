from celery import shared_task
from .models import CompressedPDF
import time

@shared_task
def compress_pdf_task(record_id: int):
    # Minimal placeholder task: mark as completed after a short sleep.
    try:
        record = CompressedPDF.objects.get(id=record_id)
        # simulate work
        time.sleep(2)
        record.compressed_size = int(record.original_size * 0.6)
        record.status = "COMPLETED"
        record.supabase_url = record.storage_path.replace("raw/", "compressed/")
        record.save()
    except CompressedPDF.DoesNotExist:
        return None

@shared_task
def write_back_sync_task():
    # Placeholder: would sync Redis counters to DB
    return True

@shared_task
def self_destruct_task(pdf_id: int):
    try:
        pdf = CompressedPDF.objects.get(id=pdf_id)
        pdf.delete()
        return True
    except CompressedPDF.DoesNotExist:
        return False
