"""Prometheus exporter for trace-derived metrics (Phase 0 stub).

Translates TraceEvents/Traces into prometheus_client metrics:
- histograms for step + session latency (yield P50/P95/P99 via quantiles),
- counters for tokens and USD cost, labeled by model/provider/status,
- a counter for errors labeled by error type.
"""

from __future__ import annotations

from agent_lens.schema import Trace


class PrometheusExporter:
    """Registers and updates Prometheus metrics from traces (Phase 0 stub)."""

    def __init__(self, *, namespace: str = "agent_lens") -> None:
        self.namespace = namespace

    def record(self, trace: Trace) -> None:  # pragma: no cover - Phase 0 stub
        """Update all registered metrics from a completed trace."""
        ...
