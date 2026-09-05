# app/observability/logger.py
import logging
import json
import time
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Custom log formatter that outputs logs as JSON.
    Makes logs easy to parse and search in production.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "node": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if provided
        if hasattr(record, "run_id"):
            log_entry["run_id"] = record.run_id
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "status"):
            log_entry["status"] = record.status

        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO"):
    """
    Configure JSON logging for the entire application.
    Call this once when the app starts.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.addHandler(handler)


class NodeLogger:
    """
    Helper class to log node execution with timing and run_id tracking.
    Use this in every agent node to log start, end, and duration.
    """

    def __init__(self, node_name: str, run_id: str):
        self.node_name = node_name
        self.run_id = run_id
        self.logger = logging.getLogger(node_name)
        self.start_time = None

    def start(self, message: str = "Node started"):
        self.start_time = time.time()
        extra = {"run_id": self.run_id, "status": "started"}
        self.logger.info(message, extra=extra)

    def success(self, message: str = "Node completed"):
        duration_ms = round((time.time() - self.start_time) * 1000, 2)
        extra = {"run_id": self.run_id, "duration_ms": duration_ms, "status": "success"}
        self.logger.info(message, extra=extra)

    def failure(self, message: str = "Node failed"):
        duration_ms = round((time.time() - self.start_time) * 1000, 2)
        extra = {"run_id": self.run_id, "duration_ms": duration_ms, "status": "failed"}
        self.logger.error(message, extra=extra)