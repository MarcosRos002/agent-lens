"""The Evaluator Protocol — the extension point of agent-lens.

An evaluator takes a whole ``Trace`` (not a single call) and returns an
``EvalResult``. Operating on the full trace is what enables trajectory and
tool-call evaluation; see docs/contracts/evaluator_protocol.md.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agent_lens.schema import EvalResult, Trace


@runtime_checkable
class Evaluator(Protocol):
    """Anything that scores a trace. Implement this to add a new evaluator.

    Implementations should be pure w.r.t. the trace and cheap to construct;
    expensive resources (LLM clients) are injected at construction time.
    """

    name: str

    def evaluate(self, trace: Trace) -> EvalResult:
        """Score ``trace`` and return a normalized EvalResult."""
        ...
