"""Tests for the heuristic ToolCallCorrectnessEvaluator (trace-level, no LLM)."""

from __future__ import annotations

from datetime import UTC, datetime

from agent_lens.eval.base import Evaluator
from agent_lens.eval.heuristic import ToolCallCorrectnessEvaluator
from agent_lens.schema import StepKind, Trace, TraceEvent


def _tool(name):
    return TraceEvent(
        session_id="s1",
        step_id=name,
        kind=StepKind.TOOL,
        name=name,
        tool_name=name,
        start_time=datetime.now(UTC),
    )


def _llm(name):
    return TraceEvent(
        session_id="s1",
        step_id=name,
        kind=StepKind.LLM,
        name=name,
        start_time=datetime.now(UTC),
    )


def _trace(*events):
    return Trace(session_id="s1", events=list(events))


def test_all_expected_tools_called_scores_one() -> None:
    ev = ToolCallCorrectnessEvaluator(expected_tools=["search", "lookup"])
    result = ev.evaluate(_trace(_tool("search"), _llm("think"), _tool("lookup")))
    assert result.score == 1.0
    assert result.passed is True
    assert result.session_id == "s1"


def test_missing_expected_tool_scores_partial_and_fails() -> None:
    ev = ToolCallCorrectnessEvaluator(expected_tools=["search", "lookup"])
    result = ev.evaluate(_trace(_tool("search")))
    assert result.score == 0.5
    assert result.passed is False


def test_ordered_mode_requires_subsequence() -> None:
    ev = ToolCallCorrectnessEvaluator(expected_tools=["a", "b"], ordered=True)
    assert ev.evaluate(_trace(_tool("a"), _tool("b"))).passed is True
    # called in the wrong order -> not a subsequence -> fails
    assert ev.evaluate(_trace(_tool("b"), _tool("a"))).passed is False


def test_emits_a_named_metric() -> None:
    ev = ToolCallCorrectnessEvaluator(expected_tools=["search"])
    result = ev.evaluate(_trace(_tool("search")))
    assert any(m.name == "tool_call_correctness" for m in result.metrics)


def test_satisfies_evaluator_protocol() -> None:
    assert isinstance(ToolCallCorrectnessEvaluator(expected_tools=["x"]), Evaluator)
