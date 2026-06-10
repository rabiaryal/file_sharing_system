"""
log_worker.py
-------------
Owns the in-process queue and the background daemon thread that drains it.

Flow:
  structlog processor  →  _log_queue.put_nowait()   (< 1 µs, never blocks)
  daemon thread        →  drains queue in batches   (every FLUSH_INTERVAL seconds)
  pymongo              →  insert_many() into MongoDB
"""

import queue
import threading
import logging
import os
from datetime import datetime, timezone

from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

# ---------------------------------------------------------------------------
# Config — override via environment variables
# ---------------------------------------------------------------------------
MONGO_URI        = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB         = os.getenv("MONGO_LOG_DB", "myapp")
MONGO_COLLECTION = os.getenv("MONGO_LOG_COLLECTION", "logs")

QUEUE_MAX_SIZE   = int(os.getenv("LOG_QUEUE_MAX", "10000"))   # drop if full
BATCH_SIZE       = int(os.getenv("LOG_BATCH_SIZE", "50"))     # docs per insert_many
FLUSH_INTERVAL   = float(os.getenv("LOG_FLUSH_INTERVAL", "2.0"))  # seconds

# TTL: auto-delete documents older than this many seconds (default 30 days)
TTL_SECONDS      = int(os.getenv("LOG_TTL_SECONDS", str(30 * 24 * 3600)))

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------
_log_queue: queue.Queue = queue.Queue(maxsize=QUEUE_MAX_SIZE)
_worker_thread: threading.Thread | None = None
_fallback_logger = logging.getLogger("log_worker")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_log_queue() -> queue.Queue:
    """Return the shared queue. Used by AsyncMongoProcessor."""
    return _log_queue


def start_log_worker() -> threading.Thread:
    """
    Create the MongoDB collection, ensure the TTL index, then
    spin up the background daemon thread.

    Call this ONCE from CoreConfig.ready().
    """
    global _worker_thread

    if _worker_thread is not None and _worker_thread.is_alive():
        return _worker_thread  # already running — idempotent

    client = MongoClient(
        MONGO_URI,
        maxPoolSize=5,          # small pool — only the worker thread uses it
        serverSelectionTimeoutMS=5_000,
    )
    col = client[MONGO_DB][MONGO_COLLECTION]

    # TTL index — MongoDB will auto-expire documents after TTL_SECONDS
    col.create_index(
        [("timestamp", ASCENDING)],
        expireAfterSeconds=TTL_SECONDS,
        background=True,
        name="ttl_timestamp",
    )

    # Regular index for fast level-based queries (e.g. find all ERRORs)
    col.create_index(
        [("level", ASCENDING)],
        background=True,
        name="idx_level",
    )

    _worker_thread = threading.Thread(
        target=_worker_loop,
        args=(col,),
        daemon=True,        # exits automatically when the Django process exits
        name="mongo-log-worker",
    )
    _worker_thread.start()
    _fallback_logger.info(
        "mongo-log-worker started | db=%s col=%s ttl=%ds",
        MONGO_DB, MONGO_COLLECTION, TTL_SECONDS,
    )
    return _worker_thread


# ---------------------------------------------------------------------------
# Worker loop (runs in the daemon thread)
# ---------------------------------------------------------------------------
def _worker_loop(col) -> None:
    """
    Continuously drains _log_queue and bulk-inserts into MongoDB.

    Strategy:
      - Block on queue.get(timeout=FLUSH_INTERVAL)
      - Once we have at least one doc, immediately drain everything else
        available right now (non-blocking) up to BATCH_SIZE
      - insert_many() the batch
      - Repeat

    If the queue stays empty for FLUSH_INTERVAL seconds we just loop again.
    If insert_many() fails we log the error to stderr but DO NOT crash —
    we drop the batch rather than block the queue indefinitely.
    """
    batch: list[dict] = []

    while True:
        # ── wait for at least one item ──────────────────────────────────────
        try:
            doc = _log_queue.get(timeout=FLUSH_INTERVAL)
            batch.append(doc)
        except queue.Empty:
            # Nothing arrived during the interval — flush whatever we have
            if batch:
                _flush(col, batch)
                batch.clear()
            continue

        # ── drain everything else available right now ───────────────────────
        while len(batch) < BATCH_SIZE:
            try:
                batch.append(_log_queue.get_nowait())
            except queue.Empty:
                break

        # ── flush the batch ─────────────────────────────────────────────────
        if len(batch) >= BATCH_SIZE:
            _flush(col, batch)
            batch.clear()
        # else: keep accumulating until FLUSH_INTERVAL fires


def _flush(col, batch: list[dict]) -> None:
    """Insert a batch into MongoDB. Silently drops on error — never blocks."""
    try:
        col.insert_many(batch, ordered=False)
    except PyMongoError as exc:
        _fallback_logger.error(
            "mongo insert_many failed — dropped %d docs: %s", len(batch), exc
        )
    except Exception as exc:
        _fallback_logger.error(
            "unexpected error in log worker — dropped %d docs: %s", len(batch), exc
        )