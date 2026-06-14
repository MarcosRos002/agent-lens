"""Cost/latency observability: Prometheus exporters + Grafana dashboards.

Exposes session-level metrics (latency P50/P95/P99, tokens, cost per session,
error rate) as Prometheus metrics, scraped into Grafana. The Grafana dashboard
JSON lives alongside this package in ``grafana/`` (added in Phase 1).
"""

from agent_lens.dashboards.prometheus import PrometheusExporter

__all__ = ["PrometheusExporter"]
