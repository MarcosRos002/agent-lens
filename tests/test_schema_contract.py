"""Contract tests for the canonical TraceEvent schema.

These are real (not stubs): the schema is the cross-repo contract, so it ships
with tests from Phase 0. If these fail, downstream repos break.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agent_lens import Trace, TraceEvent
from agent_lens.schema import ErrorInfo, StepKind, StepStatus, TokenUsage


def _now() -> datetime:
    return datetime.now(UTC)


def _llm_event(session_id: str = "s1", step_id: str = "e1") -> TraceEvent:
    return TraceEvent(
        session_id=session_id,
        step_id=step_id,
        kind=StepKind.LLM,
        name="plan",
        model="claude-sonnet-4",
        provider="anthropic",
        tokens=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        cost_usd=0.0003,
        latency_ms=420.0,
        start_time=_now(),
        end_time=_now(),
    )


def test_minimal_event_has_schema_version_and_defaults() -> None:
    ev = _llm_event()
    assert ev.schema_version  # populated from SCHEMA_VERSION
    assert ev.parent_step_id is None
    assert ev.status is StepStatus.OK
    assert ev.tokens.total_tokens == 15


def test_error_status_requires_error_payload() -> None:
    with pytest.raises(ValueError):
        TraceEvent(
            session_id="s1",
            step_id="e_err",
            kind=StepKind.TOOL,
            name="search",
            tool_name="search",
            status=StepStatus.ERROR,  # no error payload -> must raise
            start_time=_now(),
        )


def test_error_event_with_payload_is_valid() -> None:
    ev = TraceEvent(
        session_id="s1",
        step_id="e_err",
        kind=StepKind.TOOL,
        name="search",
        tool_name="search",
        status=StepStatus.ERROR,
        error=ErrorInfo(type="TimeoutError", message="upstream timed out", retryable=True),
        start_time=_now(),
    )
    assert ev.error is not None
    assert ev.error.retryable is True


def test_trace_rejects_mismatched_session_ids() -> None:
    good = _llm_event(session_id="s1", step_id="e1")
    bad = _llm_event(session_id="OTHER", step_id="e2")
    with pytest.raises(ValueError):
        Trace(session_id="s1", events=[good, bad])


def test_trace_roundtrips_through_json() -> None:
    root = _llm_event(step_id="root")
    child = _llm_event(step_id="child")
    child.parent_step_id = "root"
    trace = Trace(session_id="s1", events=[root, child])

    dumped = trace.model_dump_json()
    restored = Trace.model_validate_json(dumped)

    assert restored.session_id == "s1"
    assert [e.step_id for e in restored.events] == ["root", "child"]
    assert restored.events[1].parent_step_id == "root"
