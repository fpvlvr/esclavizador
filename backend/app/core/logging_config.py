"""Logging configuration for Google Cloud Run deployment."""

import logging
import sys
from pythonjsonlogger import jsonlogger


class CloudRunJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter optimized for Google Cloud Run logging."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        """Add fields to the log record for GCP compatibility."""
        super().add_fields(log_record, record, message_dict)

        # Map Python log levels to GCP severity levels
        severity_mapping = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }
        log_record["severity"] = severity_mapping.get(record.levelname, "DEFAULT")

        # Include exception info if present (keeps stacktrace in single field)
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)


def configure_logging() -> None:
    """Configure JSON logging for the application."""
    # Create JSON formatter
    formatter = CloudRunJsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add stdout handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Configure uvicorn loggers to use JSON format
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.addHandler(handler)
        logger.propagate = False
