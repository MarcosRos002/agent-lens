"""Tests for the trace-capture primitives (instrument an agent -> a Trace)."""

from __future__ import annotations

import pytest

from agent_lens.schema import StepKind, Trace
from agent_lens.tracing.capture import trace_session, trace_step


def test_assembles_a_trace_with_one_session_id() -> None:
    with trace_session(session_id="sess-1") as session:
        with trace_step(name="a", kind=StepKind.TOOL):
            pass
        with trace_step(name="b", kind=StepKind.LLM):
            pass
    trace = session.trace
    assert isinstance(trace, Trace)
    assert trace.session_id == "sess-1"
    assert [e.name for e in trace.events] == ["a", "b"]
    assert {e.session_id for e in trace.events} == {"sess-1"}


def test_nested_steps_get_parent_linkage() -> None:
    with trace_session() as session:  # noqa: SIM117 — explicit nesting is the point
        with trace_step(name="outer", kind=StepKind.AGENT):
            with trace_step(name="inner", kind=StepKind.TOOL):
                pass
    events = {e.name: e for e in session.trace.events}
    assert events["outer"].parent_step_id is None
    assert events["inner"].parent_step_id == events["outer"].step_id


def test_records_output_latency_and_model() -> None:
    with trace_session() as session, trace_step(name="call", kind=StepKind.LLM) as step:
        step.record_output("answer")
        step.record_model("sonnet", provider="anthropic", total_tokens=120, cost_usd=0.003)
    ev = session.trace.events[0]
    assert ev.output == "answer"
    assert ev.model == "sonnet" and ev.provider == "anthropic"
    assert ev.tokens.total_tokens == 120 and ev.cost_usd == 0.003
    assert ev.latency_ms is not None and ev.latency_ms >= 0


def test_exception_marks_step_error_and_reraises() -> None:
    with trace_session() as session:  # noqa: SIM117
        with pytest.raises(ValueError):
            with trace_step(name="boom", kind=StepKind.TOOL):
                raise ValueError("kaboom")
    ev = session.trace.events[0]
    assert ev.status.value == "error"
    assert ev.error is not None and "kaboom" in ev.error.message


def test_kind_accepts_a_string() -> None:
    with trace_session() as session, trace_step(name="r", kind="retrieval"):
        pass
    assert session.trace.events[0].kind is StepKind.RETRIEVAL


def test_trace_step_outside_session_raises() -> None:
    with pytest.raises(RuntimeError), trace_step(name="orphan"):
        pass
