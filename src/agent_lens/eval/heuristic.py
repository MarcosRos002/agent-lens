"""Heuristic (non-LLM) evaluators — deterministic, cheap, CI-friendly.

These run with no model calls, so they are fast and free — ideal as the first
gate in CI before invoking the (paid) LLM-as-judge evaluators.
"""

from __future__ import annotations

from agent_lens.schema import EvalResult, Trace


class ToolCallCorrectnessEvaluator:
    """Scores whether the agent called the *expected* tools, in a valid order.

    Compares the trace's TOOL steps against an expected tool sequence supplied
    via ``expected_tools``. Pure/deterministic — no model calls.
    """

    name = "heuristic:tool_call_correctness"

    def __init__(self, expected_tools: list[str], *, ordered: bool = False) -> None:
        self.expected_tools = expected_tools
        self.ordered = ordered

    def evaluate(self, trace: Trace) -> EvalResult:  # pragma: no cover - Phase 0 stub
        ...
