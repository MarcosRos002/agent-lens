"""Tests for the Prometheus exporter (trace -> scrapeable metrics)."""

from __future__ import annotations

from datetime import UTC, datetime

from agent_lens.dashboards.prometheus import PrometheusExporter
from agent_lens.schema import (
    ErrorInfo,
    StepKind,
    StepStatus,
    TokenUsage,
    Trace,
    TraceEvent,
)


def _ev(step_id, kind, *, latency=None, cost=None, tokens=0, model=None, error=False):
    return TraceEvent(
        session_id="s1",
        step_id=step_id,
        kind=kind,
        name=step_id,
        model=model,
        latency_ms=latency,
        cost_usd=cost,
        tokens=TokenUsage(total_tokens=tokens),
        start_time=datetime.now(UTC),
        status=StepStatus.ERROR if error else StepStatus.OK,
        error=ErrorInfo(type="Timeout", message="x") if error else None,
    )


def _trace():
    return Trace(
        session_id="s1",
        events=[
            _ev("a", StepKind.TOOL, latency=10, cost=0.001, tokens=100, model="haiku"),
            _ev("b", StepKind.LLM, latency=20, cost=0.002, tokens=200, model="sonnet"),
            _ev("c", StepKind.LLM, latency=30, error=True, model="sonnet"),
        ],
    )


def _sample_total(registry, name) -> float:
    return sum(s.value for metric in registry.collect() for s in metric.samples if s.name == name)


def test_records_step_count() -> None:
    exp = PrometheusExporter()
    exp.record(_trace())
    assert _sample_total(exp.registry, "agent_lens_steps_total") == 3.0


def test_accumulates_cost_and_tokens() -> None:
    exp = PrometheusExporter()
    exp.record(_trace())
    assert abs(_sample_total(exp.registry, "agent_lens_cost_usd_total") - 0.003) < 1e-9
    assert _sample_total(exp.registry, "agent_lens_tokens_total") == 300.0


def test_latency_histogram_count_and_sum() -> None:
    exp = PrometheusExporter()
    exp.record(_trace())
    assert _sample_total(exp.registry, "agent_lens_step_latency_ms_count") == 3.0
    assert _sample_total(exp.registry, "agent_lens_step_latency_ms_sum") == 60.0


def test_error_counter_labeled_by_type() -> None:
    exp = PrometheusExporter()
    exp.record(_trace())
    assert _sample_total(exp.registry, "agent_lens_errors_total") == 1.0


def test_exporters_use_isolated_registries() -> None:
    # Two exporters must not clash on the global registry.
    a, b = PrometheusExporter(), PrometheusExporter()
    a.record(_trace())
    assert _sample_total(b.registry, "agent_lens_steps_total") == 0.0


def test_expose_returns_scrapeable_text() -> None:
    exp = PrometheusExporter()
    exp.record(_trace())
    text = exp.expose().decode()
    assert "agent_lens_cost_usd_total" in text


def test_grafana_dashboard_json_is_valid() -> None:
    import json
    from pathlib import Path

    path = Path(__file__).parent.parent / "src/agent_lens/dashboards/grafana/agent_lens.json"
    dash = json.loads(path.read_text())
    assert dash["title"]
    assert len(dash["panels"]) >= 1
    # every panel references an agent_lens metric
    exprs = " ".join(t["expr"] for p in dash["panels"] for t in p["targets"])
    assert "agent_lens_" in exprs
