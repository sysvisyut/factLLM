import sys
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from app.core.config import settings

# Ensure standard output can handle Unicode (e.g. currency symbols like ₹ on Windows)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class StructuredFormatter(logging.Formatter):
    """Formats logs with standardized ISO timestamps and structured metadata."""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "stage"):
            log_data["stage"] = getattr(record, "stage")
        if hasattr(record, "job_id"):
            log_data["job_id"] = str(getattr(record, "job_id"))
        if hasattr(record, "document_id"):
            log_data["document_id"] = str(getattr(record, "document_id"))
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = getattr(record, "duration_ms")
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logger(name: str = "factmesh") -> logging.Logger:
    logger = logging.getLogger(name)
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


logger = setup_logger()


def log_stage(
    stage: str,
    status: str,
    message: str,
    job_id: Optional[str] = None,
    document_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None
):
    """Utility function to log pipeline execution events with structured attributes."""
    log_record = logging.LogRecord(
        name="factmesh.pipeline",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    setattr(log_record, "stage", stage)
    setattr(log_record, "status", status)
    if job_id:
        setattr(log_record, "job_id", job_id)
    if document_id:
        setattr(log_record, "document_id", document_id)
    if duration_ms is not None:
        setattr(log_record, "duration_ms", duration_ms)
    if extra:
        for k, v in extra.items():
            setattr(log_record, k, v)
    logger.handle(log_record)
