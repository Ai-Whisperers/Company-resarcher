import logging


class CLILogHandler(logging.Handler):
    """
    Custom logging handler that forwards logs to the CLI registry.

    Enables the dashboard to show live logs from CLI-started research runs.
    """

    def __init__(self, run_id: str, registry):
        super().__init__()
        self.run_id = run_id
        self.registry = registry
        self.setLevel(logging.INFO)  # Only INFO and above

    def emit(self, record: logging.LogRecord):
        try:
            # Map logging levels to dashboard levels
            level_map = {
                logging.DEBUG: "debug",
                logging.INFO: "info",
                logging.WARNING: "warning",
                logging.ERROR: "error",
                logging.CRITICAL: "error",
            }
            level = level_map.get(record.levelno, "info")

            # Format the message
            message = self.format(record)

            # Add to registry
            self.registry.add_log(
                run_id=self.run_id,
                level=level,
                source=record.name,
                message=message,
            )
        except Exception:
            pass  # Don't let logging errors break the app
