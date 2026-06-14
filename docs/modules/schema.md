# Module: `schema`

**Status:** concrete (the only non-stub module). **The cross-repo contract.**

## Purpose

Defines the canonical wire format every other module and sibling repo depends
on: `TraceEvent`, `Trace`, `EvalResult`, `Metric`, `EvalReport`, plus the enums
(`StepKind`, `StepStatus`, `MetricDirection`) and helpers (`TokenUsage`,
`ErrorInfo`). See the full spec in `docs/contracts/`.

## Interface

```python
from agent_lens.schema import (
    TraceEvent, Trace, TokenUsage, ErrorInfo, StepKind, StepStatus,
    EvalResult, Metric, MetricDirection, EvalReport, SCHEMA_VERSION,
)
```

Top-level re-exports (`from agent_lens import TraceEvent, Trace, EvalResult, ...`)
exist for ergonomics.

## Dependencies

- `pydantic>=2`. No internal deps — this is the foundation everything imports.

## How to test

```bash
pytest tests/test_schema_contract.py
```

Contract tests cover: defaults/`schema_version`, the `error`-requires-payload
invariant, session-id consistency in `Trace`, and JSON round-trip. **These are
the regression guard for the contract — keep them green.**

## Senior concerns

- **Backwards compatibility is the whole job.** Any field change is breaking:
  bump `SCHEMA_VERSION`, update `docs/contracts/trace_event.md`, write an ADR,
  and coordinate with `claims-auditor`.
- Prefer **additive, optional** fields over changing existing ones.
- Keep models cheap to (de)serialize — they cross process/repo boundaries as JSON.
- Validation belongs here (e.g. `error` consistency), not scattered in consumers.
