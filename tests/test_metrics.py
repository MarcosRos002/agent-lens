"""Tests for trace-level observability metrics.

Given a Trace (the wire format any instrumented agent emits), compute the
headline observability numbers: latency percentiles, cost, tokens, error rate,
and a per-step-kind breakdown. Pure/offline.
"""

from __future__ import annotations

from datetime import UTC, datetime

from agent_lens.metrics import compute_trace_metrics, metrics_as_schema
from agent_lens.schema import (
    ErrorInfo,
    Metric,
    StepKind,
    StepStatus,
    TokenUsage,
    Trace,
    TraceEvent,
)


def _ev(step_id, kind, *, latency=None, cost=None, tokens=0, error=False):
    return TraceEvent(
        session_id="s1",
        step_id=step_id,
        kind=kind,
        name=step_id,
        latency_ms=latency,
        cost_usd=cost,
        tokens=TokenUsage(total_tokens=tokens),
        start_time=datetime.now(UTC),
        status=StepStatus.ERROR if error else StepStatus.OK,
        error=ErrorInfo(type="X", message="boom") if error else None,
    )


def _trace():
    return Trace(
        session_id="s1",
        events=[
            _ev("a", StepKind.TOOL, latency=10, cost=0.001, tokens=100),
            _ev("b", StepKind.LLM, latency=20, cost=0.002, tokens=200),
            _ev("c", StepKind.LLM, latency=30, cost=None, tokens=0, error=True),
            _ev("d", StepKind.RETRIEVAL, latency=40, cost=0.004, tokens=50),
        ],
    )


def test_counts_and_kind_breakdown() -> None:
    m = compute_trace_metrics(_trace())
    assert m.total_steps == 4
    assert m.steps_by_kind["llm"] == 2
    assert m.steps_by_kind["tool"] == 1
    assert m.steps_by_kind["retrieval"] == 1


def test_error_rate() -> None:
    m = compute_trace_metrics(_trace())
    assert m.error_steps == 1
    assert m.error_rate == 0.25


def test_cost_and_tokens_sum_ignoring_none() -> None:
    m = compute_trace_metrics(_trace())
    assert abs(m.total_cost_usd - 0.007) < 1e-9
    assert m.total_tokens == 350


def test_latency_total_and_percentiles() -> None:
    m = compute_trace_metrics(_trace())
    assert m.latency_total_ms == 100.0
    # nearest-rank: p50 of [10,20,30,40] -> 20; p95 -> 40
    assert m.latency_p50_ms == 20.0
    assert m.latency_p95_ms == 40.0


def test_empty_trace_is_safe() -> None:
    m = compute_trace_metrics(Trace(session_id="empty", events=[]))
    assert m.total_steps == 0
    assert m.error_rate == 0.0
    assert m.latency_p95_ms == 0.0


def test_metrics_as_schema_emits_named_metrics() -> None:
    schema_metrics = metrics_as_schema(compute_trace_metrics(_trace()))
    assert all(isinstance(x, Metric) for x in schema_metrics)
    names = {x.name for x in schema_metrics}
    assert {"latency_p50_ms", "latency_p95_ms", "total_cost_usd", "error_rate"} <= names
    # error_rate is a lower-is-better metric
    er = next(x for x in schema_metrics if x.name == "error_rate")
    assert er.direction.value == "lower_is_better"
