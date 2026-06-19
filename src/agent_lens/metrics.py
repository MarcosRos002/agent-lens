"""Trace-level observability metrics.

Turns a ``Trace`` (the wire format any instrumented agent emits) into the
headline numbers a dashboard or README leads with: latency percentiles, cost,
tokens, error rate, and a per-step-kind breakdown. Pure and offline — no model
calls.

Percentiles use the **nearest-rank** method (``p`` -> the value at rank
``ceil(p/100 * n)``), which is unambiguous for the small step counts typical of
an agent trace.
"""

from __future__ import annotations

import math
from collections import Counter

from pydantic import BaseModel, Field

from agent_lens.schema import Metric, MetricDirection, StepStatus, Trace


class TraceMetrics(BaseModel):
    """Computed observability metrics for one trace."""

    session_id: str
    total_steps: int
    steps_by_kind: dict[str, int] = Field(default_factory=dict)
    error_steps: int = 0
    error_rate: float = 0.0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    latency_total_ms: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100.0 * len(ordered)))
    return float(ordered[rank - 1])


def compute_trace_metrics(trace: Trace) -> TraceMetrics:
    events = trace.events
    n = len(events)
    latencies = [e.latency_ms for e in events if e.latency_ms is not None]
    errors = sum(1 for e in events if e.status is StepStatus.ERROR)

    return TraceMetrics(
        session_id=trace.session_id,
        total_steps=n,
        steps_by_kind=dict(Counter(e.kind.value for e in events)),
        error_steps=errors,
        error_rate=(errors / n) if n else 0.0,
        total_cost_usd=sum(e.cost_usd for e in events if e.cost_usd is not None),
        total_tokens=sum(e.tokens.total_tokens for e in events),
        latency_total_ms=sum(latencies),
        latency_p50_ms=_percentile(latencies, 50),
        latency_p95_ms=_percentile(latencies, 95),
    )


def metrics_as_schema(m: TraceMetrics) -> list[Metric]:
    """Project ``TraceMetrics`` onto the schema ``Metric`` list dashboards consume."""
    lower = MetricDirection.LOWER_IS_BETTER
    return [
        Metric(name="total_steps", value=float(m.total_steps), direction=lower, unit="count"),
        Metric(name="error_rate", value=m.error_rate, direction=lower, unit="ratio"),
        Metric(name="total_cost_usd", value=m.total_cost_usd, direction=lower, unit="usd"),
        Metric(name="total_tokens", value=float(m.total_tokens), direction=lower, unit="tokens"),
        Metric(name="latency_p50_ms", value=m.latency_p50_ms, direction=lower, unit="ms"),
        Metric(name="latency_p95_ms", value=m.latency_p95_ms, direction=lower, unit="ms"),
    ]
