import logging
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


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
        """Redact sensitive information like API keys."""
        import re

        # Pattern for common API key formats (sk-..., AIza..., etc.)
        patterns = [
            r'(api[_-]?key["\s:=]+)([a-zA-Z0-9-_]{20,})',
            r"(sk-[a-zA-Z0-9]{20,})",
            r"(AIza[a-zA-Z0-9-_]{20,})",
        ]

        sanitized = message
        for pattern in patterns:
            sanitized = re.sub(pattern, r"\1***REDACTED***", sanitized, flags=re.I)
        return sanitized

    def format(self, record):
        # Sanitize the message before formatting
        if isinstance(record.msg, str):
            record.msg = self.sanitize_message(record.msg)

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger instance"""
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler("research.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
