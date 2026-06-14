"""Example: instrument a toy agent with agent-lens, then evaluate the trace.

This is an ergonomics SKETCH for Phase 0 — the tracing/eval internals are stubs,
so the instrumented section is commented out. It shows the intended ~5-line
developer experience and how a TraceEvent is constructed by hand in the
meantime (the concrete schema already works today).

Run (once Phase 1 lands):
    python examples/instrument_toy_agent.py
"""

from __future__ import annotations

from datetime import UTC, datetime

from agent_lens import Trace, TraceEvent
from agent_lens.schema import StepKind, TokenUsage

# ---------------------------------------------------------------------------
# INTENDED ERGONOMICS (Phase 1) — instrument any agent in ~5 lines:
#
#   from agent_lens.tracing import trace_session, trace_step
#
#   with trace_session() as session:
#       with trace_step(kind="llm", name="plan"):
#           plan = my_llm("decide which tool to call")
#       with trace_step(kind="tool", tool_name="search"):
#           docs = search(plan.query)
#
#   from agent_lens.eval import TrajectoryJudgeEvaluator
#   result = TrajectoryJudgeEvaluator(
#       model="claude-sonnet-4",
#       rubric="Did the agent pick the right tools to answer the question?",
#   ).evaluate(session.trace)
#   print(result.score, result.passed)
# ---------------------------------------------------------------------------


def build_demo_trace() -> Trace:
    """Construct a trace by hand using the concrete schema (works today)."""
    now = datetime.now(UTC)
    plan = TraceEvent(
        session_id="demo",
        step_id="step-1",
        kind=StepKind.LLM,
        name="plan",
        model="claude-sonnet-4",
        provider="anthropic",
        inputs={"prompt": "What is the capital of France?"},
        output="I should answer directly.",
        tokens=TokenUsage(prompt_tokens=12, completion_tokens=6, total_tokens=18),
        cost_usd=0.0004,
        latency_ms=310.0,
        start_time=now,
        end_time=now,
    )
    answer = TraceEvent(
        session_id="demo",
        step_id="step-2",
        parent_step_id="step-1",
        kind=StepKind.LLM,
        name="answer",
        model="claude-sonnet-4",
        provider="anthropic",
        output="Paris.",
        tokens=TokenUsage(prompt_tokens=20, completion_tokens=2, total_tokens=22),
        cost_usd=0.0005,
        latency_ms=180.0,
        start_time=now,
        end_time=now,
    )
    return Trace(session_id="demo", events=[plan, answer])


if __name__ == "__main__":
    trace = build_demo_trace()
    print(f"Built trace {trace.session_id!r} with {len(trace.events)} steps:")
    for ev in trace.events:
        parent = ev.parent_step_id or "ROOT"
        print(f"  {ev.step_id} ({ev.kind.value}) <- {parent}: {ev.output!r}")
