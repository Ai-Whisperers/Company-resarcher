import logging
import os
import re
import sys
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Pre-compiled regex patterns for API key sanitization (performance optimization)
_API_KEY_PATTERNS = [
    re.compile(r'(api[_-]?key["\s:=]+)([a-zA-Z0-9-_]{20,})', re.I),
    re.compile(r"(sk-[a-zA-Z0-9]{20,})"),
    re.compile(r"(AIza[a-zA-Z0-9-_]{20,})"),
    re.compile(r"(xoxb-[a-zA-Z0-9-]+)"),  # Slack tokens
    re.compile(r"(ghp_[a-zA-Z0-9]{36})"),  # GitHub tokens
]


class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored logs"""

    FORMATS = {
        logging.DEBUG: Fore.CYAN
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
        logging.INFO: Fore.GREEN
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
        logging.ERROR: Fore.RED
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED
        + Style.BRIGHT
        + "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        + Style.RESET_ALL,
    }

    def sanitize_message(self, message: str) -> str:
        """Redact sensitive information like API keys using pre-compiled patterns."""
        sanitized = message
        for pattern in _API_KEY_PATTERNS:
            sanitized = pattern.sub(r"\1***REDACTED***", sanitized)
        return sanitized

    def format(self, record):
        # Sanitize the message before formatting
        if isinstance(record.msg, str):
            record.msg = self.sanitize_message(record.msg)

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger instance with security-validated log path."""
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # File Handler with validated path
    log_dir = Path(os.getenv("LOG_DIR", ".")).resolve()
    log_file = log_dir / "research.log"

    # Security: ensure log file is within log directory (prevent symlink attacks)
    try:
        resolved_log = log_file.resolve()
        # Check that resolved path is under log_dir
        resolved_log.relative_to(log_dir)
    except ValueError:
        # Path traversal attempt - fall back to current directory
        logger.warning(f"Invalid log path detected, using current directory")
        log_file = Path("research.log").resolve()

    # Create directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
