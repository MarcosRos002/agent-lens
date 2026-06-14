"""OTel-based trace capture: decorators + context managers.

Intended ergonomics (Phase 1):

    from agent_lens.tracing import trace_session, trace_step

    with trace_session() as session:
        with trace_step(kind="tool", tool_name="search") as step:
            step.record_output(result)

Under the hood each ``trace_step`` opens an OpenTelemetry span and, on exit,
serializes it into a canonical ``TraceEvent`` (see agent_lens.schema). The OTel
mapping keeps us compatible with existing collectors and with Langfuse/LangSmith
concepts.
"""

from agent_lens.tracing.capture import trace_session, trace_step

__all__ = ["trace_session", "trace_step"]
