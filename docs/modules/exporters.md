# Module: `exporters`

**Status:** implemented (Phase 1). `LangfuseExporter.to_observations(trace)` and `LangSmithExporter.to_runs(trace)` map the canonical Trace onto each platform's schema (parent linkage, tokens, cost, latency, status/error). `export()` lazily pushes via the SDK. Pinned by `tests/test_exporters.py`.

## Purpose

Export canonical `Trace`s to external observability platforms so teams already on
a hosted product can adopt agent-lens's trace-level evaluators without
re-instrumenting. `TraceEvent` maps cleanly onto both Langfuse and LangSmith
span/trace models.

## Interface (intended)

```python
from agent_lens.exporters import LangfuseExporter, LangSmithExporter

LangfuseExporter(public_key=..., secret_key=...).export(trace)
LangSmithExporter(api_key=..., project=...).export(trace)
```

## Dependencies

- `agent_lens.schema` (reads `Trace`).
- Optional, lazily-imported platform SDKs (kept out of core deps so the base
  install stays light/free).

## How to test

- Mapping correctness: `TraceEvent` fields → platform span fields, including
  parent/child linkage, tokens, cost, latency, status/error.
- Mock the platform client; assert payload shape and batching.

## Senior concerns

- **Optional/lazy imports** — don't force every user to install Langfuse/LangSmith.
- Faithful mapping of the trajectory tree (parent/child) into the target model.
- This is also the honest "when NOT to use agent-lens" escape hatch (see ADR
  0001): if you want a turnkey hosted UI, export to one of these.
