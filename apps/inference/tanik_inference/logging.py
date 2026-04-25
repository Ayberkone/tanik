"""Structured logging for the inference service.

Output is logfmt-style: ISO-8601 timestamp, level, logger name, message,
then key=value pairs from the LogRecord's `extra` dict. This is
human-readable in a tail and machine-parseable by log shippers
(Vector, Promtail, Datadog) without dragging in a JSON-logging dep.

Example line:

    2026-04-25T19:17:18.288Z INFO  tanik msg="request" method=POST path=/api/v1/iris/enroll status=201 elapsed_ms=735.6 request_id=17c6713656454f398d3da65e9bae177e
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Reserved attributes set by the stdlib LogRecord; exclude these from the
# extra-fields dump so we don't double-print everything.
_RESERVED = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "asctime",
}


def _quote(value: Any) -> str:
    s = str(value)
    if not s:
        return '""'
    if any(c in s for c in (' ', '"', '=')):
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return s


class LogfmtFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        parts = [
            ts,
            f"{record.levelname:<5}",
            record.name,
            f'msg={_quote(record.getMessage())}',
        ]
        for key, val in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            parts.append(f"{key}={_quote(val)}")
        if record.exc_info:
            parts.append(f"exc={_quote(self.formatException(record.exc_info))}")
        return " ".join(parts)


def setup_logging(level: str = "INFO") -> None:
    # Remove any handlers attached by uvicorn/imports so we get a single
    # consistent format. Uvicorn logs through "uvicorn", "uvicorn.access",
    # and "uvicorn.error" — apply the same formatter to all of them.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(LogfmtFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Quiet uvicorn's access log — our request_context middleware logs the
    # same thing in our format. Keep uvicorn's startup/shutdown lines.
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False


log = logging.getLogger("tanik")
