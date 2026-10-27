import logging
import sys
import re
from app.core.config import settings


class SensitiveDataFilter(logging.Filter):
    """Filter out API keys and sensitive tokens from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # Redact configured key if set
            if settings.LLM_API_KEY and len(settings.LLM_API_KEY) > 5:
                record.msg = record.msg.replace(settings.LLM_API_KEY, "[REDACTED_API_KEY]")
            # Redact common key patterns
            record.msg = re.sub(r'(?i)(api[_-]?key|token|bearer|secret)\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{8,}["\']?', r'\1=[REDACTED]', record.msg)
            # Redact AIza Google API keys if present
            record.msg = re.sub(r'AIza[0-9A-Za-z\-_]{35}', '[REDACTED_GEMINI_KEY]', record.msg)
        return True


def setup_logging() -> logging.Logger:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger("medigraph")
    logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
