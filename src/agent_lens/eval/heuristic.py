"""Heuristic (non-LLM) evaluators — deterministic, cheap, CI-friendly.

These run with no model calls, so they are fast and free — ideal as the first
gate in CI before invoking the (paid) LLM-as-judge evaluators.
"""

from __future__ import annotations

from agent_lens.schema import EvalResult, Metric, MetricDirection, StepKind, Trace


class ToolCallCorrectnessEvaluator:
    """Scores whether the agent called the *expected* tools (optionally in order).

    Compares the trace's TOOL steps against an expected tool sequence. Pure and
    deterministic — no model calls. ``score`` is the fraction of expected tools
    satisfied; ``passed`` is ``score == 1.0``.

    - unordered (default): fraction of expected tools that appear anywhere.
    - ordered: expected must appear as an in-order *subsequence* of the calls.
    """

    name = "heuristic:tool_call_correctness"

    def __init__(self, expected_tools: list[str], *, ordered: bool = False) -> None:
        self.expected_tools = expected_tools
        self.ordered = ordered

    def evaluate(self, trace: Trace) -> EvalResult:
        actual = [(e.tool_name or e.name) for e in trace.events if e.kind is StepKind.TOOL]
        if not self.expected_tools:
            score = 1.0
        elif self.ordered:
            score = self._subsequence_fraction(self.expected_tools, actual)
        else:
            present = sum(1 for t in self.expected_tools if t in actual)
            score = present / len(self.expected_tools)

        return EvalResult(
            evaluator=self.name,
            session_id=trace.session_id,
            score=score,
            passed=score == 1.0,
            metrics=[
                Metric(
                    name="tool_call_correctness",
                    value=score,
                    direction=MetricDirection.HIGHER_IS_BETTER,
                    unit="ratio",
                )
            ],
            rationale=f"expected={self.expected_tools} ordered={self.ordered} actual={actual}",
        )

    @staticmethod
    def _subsequence_fraction(expected: list[str], actual: list[str]) -> float:
        """How many of ``expected`` match as an in-order subsequence of ``actual``."""
        it = iter(actual)
        matched = 0
        for tool in expected:
            for a in it:
                if a == tool:
                    matched += 1
                    break
        return matched / len(expected)
