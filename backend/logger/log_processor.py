"""
log_processor.py
----------------
A structlog processor that enqueues log documents for async MongoDB insertion.

It must be placed in the structlog processor chain BEFORE the final renderer
(ConsoleRenderer / JSONRenderer).  It passes the event_dict through unchanged
so the next processor still gets a complete dict.

Example chain:
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        AsyncMongoProcessor(),          ← enqueues, then passes through
        structlog.dev.ConsoleRenderer(),
    ]
"""

from datetime import datetime, timezone
from .log_worker import get_log_queue


class AsyncMongoProcessor:
    """
    Structlog processor — called synchronously in the request thread
    but only does a queue.put_nowait() which takes < 1 microsecond.

    Never blocks. If the queue is full it silently drops the document
    rather than stalling the request.
    """

    # Fields that are structlog internals — strip them from the stored doc
    _STRIP_FIELDS = frozenset({"_record", "_from_structlog"})

    def __call__(self, logger, method: str, event_dict: dict) -> dict:
        doc = self._build_doc(method, event_dict)
        try:
            get_log_queue().put_nowait(doc)
        except Exception:
            # Queue full or any other error — drop silently, never raise
            pass
        return event_dict   # ← pass through unmodified to the next processor

    # ------------------------------------------------------------------
    def _build_doc(self, method: str, event_dict: dict) -> dict:
        """
        Build the MongoDB document from structlog's event_dict.

        structlog already attached:
          - "event"      → the log message string
          - "level"      → from add_log_level processor
          - "timestamp"  → from TimeStamper processor (ISO string)
          - "request_id" → from django-structlog RequestMiddleware
          - "user_id"    → from django-structlog RequestMiddleware
          + any kwargs you passed to log.info(...)

        We store everything as-is plus add a native datetime for the TTL index.
        """
        doc = {
            k: v
            for k, v in event_dict.items()
            if k not in self._STRIP_FIELDS
        }

        # Native datetime required for MongoDB TTL index
        # (TimeStamper gives us an ISO string; we need a datetime object)
        doc["timestamp"] = datetime.now(timezone.utc)

        # Fallback level if add_log_level processor hasn't run yet
        if "level" not in doc:
            doc["level"] = method.upper()

        return doc