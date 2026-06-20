"""Run the agent-lens eval suite over example traces and print an EvalReport JSON.

Used by the eval-gate GitHub Action: its stdout is the *current* report, compared
against the committed baseline (`eval/baseline_report.json`). Deterministic so the
gate is stable in CI.

Usage:
    python examples/run_eval_suite.py > current_report.json
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from agent_lens.eval.heuristic import ToolCallCorrectnessEvaluator
from agent_lens.schema import EvalReport, StepKind, Trace, TraceEvent


def _tool_step(session_id: str, name: str) -> TraceEvent:
    # Fixed timestamp so the suite is fully deterministic.
    return TraceEvent(
        session_id=session_id,
        step_id=name,
        kind=StepKind.TOOL,
        name=name,
        tool_name=name,
        start_time=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _example_traces() -> list[Trace]:
    return [
        Trace(
            session_id="audit-1",
            events=[_tool_step("audit-1", "rules_engine.evaluate")],
        ),
        Trace(
            session_id="audit-2",
            events=[
                _tool_step("audit-2", "lookup_cpt"),
                _tool_step("audit-2", "rules_engine.evaluate"),
            ],
        ),
    ]


def build_report() -> EvalReport:
    evaluator = ToolCallCorrectnessEvaluator(expected_tools=["rules_engine.evaluate"])
    results = [evaluator.evaluate(t) for t in _example_traces()]
    return EvalReport(suite="agent-lens-example", results=results)


if __name__ == "__main__":
    print(json.dumps(build_report().model_dump(mode="json"), indent=2))
