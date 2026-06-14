# Module: `tracing`

**Status:** Phase-0 stub.

## Purpose

Capture live agent execution as canonical `TraceEvent`s using OpenTelemetry.
Provides the developer-facing ergonomics — context managers (and later
decorators) — that turn an instrumented agent into a `Trace`.

## Interface (intended)

```python
from agent_lens.tracing import trace_session, trace_step

with trace_session() as session:          # opens a root → one session_id
    with trace_step(kind="tool", tool_name="search") as step:
        step.record_output(result)        # becomes a TraceEvent on exit
trace = session.trace                       # assembled Trace
```

Each `trace_step` opens an OTel span; on exit it serializes the span into a
`TraceEvent`, assigning `session_id` / `step_id` / `parent_step_id` from the
active OTel context.

## Dependencies

- `opentelemetry-api`, `opentelemetry-sdk`.
- `agent_lens.schema` (emits `TraceEvent` / `Trace`).

## How to test

- Span → `TraceEvent` field mapping (kind, name, tokens, latency, status/error).
- Parent/child linkage: nested `trace_step`s produce correct `parent_step_id`.
- Timing: `start_time`/`end_time`/`latency_ms` populated and consistent.

## Senior concerns

- **Low overhead / non-blocking.** Capture must not slow the agent's hot path;
  prefer async export and sampling.
- **PII/PHI redaction hooks** before `inputs`/`output` are recorded.
- Correct context propagation across threads/async tasks (OTel context vars).
- Don't lose in-flight steps on crash — flush spans defensively.
