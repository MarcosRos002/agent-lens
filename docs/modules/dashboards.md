# Module: `dashboards`

**Status:** Phase-0 stub.

## Purpose

Cost/latency observability. Translate traces into Prometheus metrics and ship a
Grafana dashboard JSON: latency P50/P95/P99, tokens, cost per session, error rate
— labeled by model / provider / status.

## Interface (intended)

```python
from agent_lens.dashboards import PrometheusExporter

exporter = PrometheusExporter(namespace="agent_lens")
exporter.record(trace)   # updates histograms/counters; scraped by Prometheus
```

A Grafana dashboard JSON will live under the package (`grafana/`) for one-click import.

## Dependencies

- `prometheus-client`.
- `agent_lens.schema` (reads `Trace` / `TraceEvent`).
- Runtime: a Prometheus scrape target + Grafana (both free/self-hostable).

## How to test

- Metric registration + label cardinality.
- Histogram buckets produce sensible P50/P95/P99.
- Cost/token counters accumulate correctly across a trace.

## Senior concerns

- **Label cardinality** — don't label by `session_id`/`step_id` (unbounded);
  aggregate by model/provider/status/tool.
- Quantiles via histogram buckets (Prometheus-side `histogram_quantile`) rather
  than client-side summaries when possible.
- Cost attribution must match the `cost_usd` the producer emits — single source
  of truth.
