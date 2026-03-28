import logging
import sys
import json
from datetime import datetime, timezone
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "redirect-service",
            "environment": "development" if settings.DEBUG else "production",
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger = logging.getLogger("redirect")
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

logger = setup_logging()