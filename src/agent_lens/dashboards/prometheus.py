"""Prometheus exporter for trace-derived metrics.

Translates ``TraceEvent``s into prometheus_client metrics that Grafana scrapes:
- a latency histogram per step kind (PromQL ``histogram_quantile`` -> P50/P95/P99),
- counters for cost (USD) and tokens, labeled by model,
- a step counter labeled by kind/status, and an error counter labeled by type.

Each exporter owns its own ``CollectorRegistry`` so instances never clash on the
global default registry. Scrape via ``expose()`` (or point Prometheus at the
registry). A Grafana dashboard JSON lives in ``dashboards/grafana/``.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

from agent_lens.schema import StepStatus, Trace

_LATENCY_BUCKETS_MS = (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, float("inf"))


class PrometheusExporter:
    """Registers and updates Prometheus metrics from traces."""

    def __init__(self, *, namespace: str = "agent_lens") -> None:
        self.namespace = namespace
        self.registry = CollectorRegistry()
        self._latency = Histogram(
            f"{namespace}_step_latency_ms",
            "Per-step latency (ms)",
            ["kind"],
            buckets=_LATENCY_BUCKETS_MS,
            registry=self.registry,
        )
        self._steps = Counter(
            f"{namespace}_steps", "Steps recorded", ["kind", "status"], registry=self.registry
        )
        self._cost = Counter(
            f"{namespace}_cost_usd", "Cost in USD", ["model"], registry=self.registry
        )
        self._tokens = Counter(
            f"{namespace}_tokens", "Total tokens", ["model"], registry=self.registry
        )
        self._errors = Counter(f"{namespace}_errors", "Errors", ["type"], registry=self.registry)

    def record(self, trace: Trace) -> None:
        """Update all registered metrics from a completed trace."""
        for e in trace.events:
            self._steps.labels(kind=e.kind.value, status=e.status.value).inc()
            if e.latency_ms is not None:
                self._latency.labels(kind=e.kind.value).observe(e.latency_ms)
            model = e.model or "unknown"
            if e.cost_usd:
                self._cost.labels(model=model).inc(e.cost_usd)
            if e.tokens.total_tokens:
                self._tokens.labels(model=model).inc(e.tokens.total_tokens)
            if e.status is StepStatus.ERROR and e.error is not None:
                self._errors.labels(type=e.error.type).inc()

    def expose(self) -> bytes:
        """Return the Prometheus text exposition for scraping."""
        return generate_latest(self.registry)
