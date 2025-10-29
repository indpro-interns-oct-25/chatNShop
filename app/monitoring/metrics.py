"""Lightweight metric helpers for observability."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional


_logger = logging.getLogger("app.monitoring.metrics")


def log_metric(name: str, value: float, *, tags: Optional[Dict[str, Any]] = None) -> None:
    """Emit a structured metric event."""

    payload = {"metric": name, "value": value, "tags": tags or {}}
    _logger.info("metric_event", extra={"metric_payload": payload})


def log_latency(name: str, *, start_time: float, tags: Optional[Dict[str, Any]] = None) -> None:
    """Convenience wrapper to record elapsed milliseconds for a span."""

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    log_metric(name, elapsed_ms, tags=tags)


__all__ = ["log_metric", "log_latency"]
