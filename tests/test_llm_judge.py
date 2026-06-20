"""Tests for the LLM-as-judge trajectory evaluator (judge model injected => offline).

Exercises the mitigations for naive LLM-as-judge: structured/validated verdicts
with a bounded re-prompt, self-consistency via median over samples, and recording
the judge model for reproducibility.
"""

from __future__ import annotations

from datetime import UTC, datetime

from agent_lens.eval.base import Evaluator
from agent_lens.eval.llm_judge import TrajectoryJudgeEvaluator
from agent_lens.schema import StepKind, Trace, TraceEvent


class FakeJudge:
    """Replays canned JSON verdicts; counts calls (for self-consistency tests)."""

    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return self._replies.pop(0)


def _trace():
    return Trace(
        session_id="s1",
        events=[
            TraceEvent(
                session_id="s1",
                step_id="1",
                kind=StepKind.TOOL,
                name="rules_engine.evaluate",
                tool_name="rules_engine.evaluate",
                start_time=datetime.now(UTC),
            ),
            TraceEvent(
                session_id="s1",
                step_id="2",
                kind=StepKind.LLM,
                name="classifier.classify",
                start_time=datetime.now(UTC),
            ),
        ],
    )


def _judge(replies, *, samples=1, threshold=0.7):
    model = FakeJudge(replies)
    ev = TrajectoryJudgeEvaluator(
        model,
        model="claude-sonnet-4-6",
        rubric="Right tools, sensible order, safe.",
        samples=samples,
        pass_threshold=threshold,
    )
    return ev, model


def test_scores_from_a_single_verdict() -> None:
    ev, _ = _judge(['{"score": 0.9, "rationale": "good trajectory", "evidence": ["1"]}'])
    result = ev.evaluate(_trace())
    assert result.score == 0.9
    assert result.passed is True
    assert result.session_id == "s1"
    assert result.evaluator == "llm_judge:trajectory"


def test_low_score_fails_the_threshold() -> None:
    ev, _ = _judge(['{"score": 0.3, "rationale": "wrong tools"}'], threshold=0.7)
    assert ev.evaluate(_trace()).passed is False


def test_self_consistency_aggregates_by_median() -> None:
    replies = [
        '{"score": 0.6, "rationale": "a"}',
        '{"score": 0.9, "rationale": "b"}',
        '{"score": 0.8, "rationale": "c"}',
    ]
    ev, judge = _judge(replies, samples=3)
    result = ev.evaluate(_trace())
    assert result.score == 0.8  # median of 0.6/0.9/0.8
    assert judge.calls == 3


def test_invalid_json_reprompts_once_then_succeeds() -> None:
    ev, judge = _judge(["{not json", '{"score": 0.85, "rationale": "ok"}'])
    result = ev.evaluate(_trace())
    assert result.score == 0.85
    assert judge.calls == 2  # one re-prompt


def test_records_judge_model_for_reproducibility() -> None:
    ev, _ = _judge(['{"score": 0.9, "rationale": "ok"}'])
    md = ev.evaluate(_trace()).metadata
    assert md["model"] == "claude-sonnet-4-6"
    assert md["provider"] == "anthropic"


def test_emits_trajectory_score_metric() -> None:
    ev, _ = _judge(['{"score": 0.9, "rationale": "ok"}'])
    result = ev.evaluate(_trace())
    assert any(m.name == "trajectory_score" for m in result.metrics)


def test_satisfies_evaluator_protocol() -> None:
    ev, _ = _judge(['{"score": 0.9, "rationale": "ok"}'])
    assert isinstance(ev, Evaluator)
