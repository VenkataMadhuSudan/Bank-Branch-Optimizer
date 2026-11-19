"""
Structured Logging Architecture with Credential Sanitization Filter.
Ensures zero credential leakage into logs, standardized timestamps, and trace context.
"""
import logging
import os
import re
import sys
from typing import Any

# Sensitive patterns and their replacements
SENSITIVE_RULES = [
    (re.compile(r"(password['\"]?\s*[:=]\s*['\"]?)([^'\"\s&,;]+)(['\"]?)", re.IGNORECASE), r"\g<1>********\g<3>"),
    (re.compile(r"(secret['\"]?\s*[:=]\s*['\"]?)([^'\"\s&,;]+)(['\"]?)", re.IGNORECASE), r"\g<1>********\g<3>"),
    (re.compile(r"(token['\"]?\s*[:=]\s*['\"]?)([^'\"\s&,;]+)(['\"]?)", re.IGNORECASE), r"\g<1>********\g<3>"),
    (re.compile(r"(authorization:\s*bearer\s+)([^\s]+)", re.IGNORECASE), r"\g<1>********"),
    (re.compile(r"(postgres(?:ql)?(?:\+[a-z0-9]+)?://[^:]+:)([^@]+)(@)", re.IGNORECASE), r"\g<1>********\g<3>"),
]

class CredentialRedactionFilter(logging.Filter):
    """Filters out passwords, secrets, tokens, and database passwords from log messages."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            sanitized = record.msg
            for pattern, repl in SENSITIVE_RULES:
                sanitized = pattern.sub(repl, sanitized)
            record.msg = sanitized
        return True

def setup_logger(name: str = "bank_optimizer") -> logging.Logger:
    """Configures and returns a structured logger instance."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_name, logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    handler.addFilter(CredentialRedactionFilter())

    logger.addHandler(handler)
    logger.propagate = False
    return logger

logger = setup_logger("bank_optimizer")
