"""Tests for causal root-cause analysis over a session's step tree."""

from __future__ import annotations

from datetime import UTC, datetime

from agent_lens.analysis.causal import find_root_cause
from agent_lens.schema import ErrorInfo, StepKind, StepStatus, Trace, TraceEvent


def _step(step_id, *, parent=None, error=False, second=0, kind=StepKind.TOOL):
    return TraceEvent(
        session_id="s1",
        step_id=step_id,
        parent_step_id=parent,
        kind=kind,
        name=step_id,
        start_time=datetime(2026, 1, 1, 0, 0, second, tzinfo=UTC),
        status=StepStatus.ERROR if error else StepStatus.OK,
        error=ErrorInfo(type="Boom", message="fail") if error else None,
    )


def test_returns_none_when_nothing_failed() -> None:
    trace = Trace(session_id="s1", events=[_step("a"), _step("b", parent="a")])
    assert find_root_cause(trace) is None


def test_returns_the_originating_failure_not_the_downstream_symptom() -> None:
    # a (ok) -> b (ERROR, the cause) -> c (ERROR, propagated symptom)
    trace = Trace(
        session_id="s1",
        events=[
            _step("a", second=0),
            _step("b", parent="a", error=True, second=1),
            _step("c", parent="b", error=True, second=2),
        ],
    )
    culprit = find_root_cause(trace)
    assert culprit is not None
    assert culprit.step_id == "b"  # not the last error "c"


def test_picks_the_earliest_of_independent_failures() -> None:
    # two independent error branches (neither is the other's ancestor)
    trace = Trace(
        session_id="s1",
        events=[
            _step("root", second=0),
            _step("x", parent="root", error=True, second=3),
            _step("y", parent="root", error=True, second=1),  # earlier
        ],
    )
    assert find_root_cause(trace).step_id == "y"


def test_single_error_is_its_own_root_cause() -> None:
    trace = Trace(
        session_id="s1", events=[_step("a"), _step("b", parent="a", error=True, second=1)]
    )
    assert find_root_cause(trace).step_id == "b"
