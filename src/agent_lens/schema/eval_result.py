"""Eval result + metric schemas.

These are the OUTPUT contract: what evaluators return and what dashboards and
CI eval-gates consume. Concrete (small, stable) on purpose — the eval-gate in
CI keys off ``EvalResult.score`` and ``EvalResult.passed``.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MetricDirection(str, Enum):
    """Whether higher or lower is better — needed for regression gating."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class Metric(BaseModel):
    """A single named measurement over a trace or a step."""

    name: str = Field(..., description="Metric id, e.g. 'tool_call_correctness'.")
    value: float
    direction: MetricDirection = MetricDirection.HIGHER_IS_BETTER
    unit: str | None = Field(None, description="e.g. 'ratio', 'usd', 'ms', 'tokens'.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalResult(BaseModel):
    """The result of running ONE evaluator over ONE trace (or step).

    ``score`` is the normalized headline number in [0, 1]; ``passed`` is the
    boolean the CI eval-gate reads; ``metrics`` carries the breakdown.
    """

    evaluator: str = Field(..., description="Evaluator name, e.g. 'llm_judge:trajectory'.")
    session_id: str = Field(..., description="Trace this result is about.")
    step_id: str | None = Field(None, description="Set when the result scopes a single step.")

    score: float = Field(..., ge=0.0, le=1.0, description="Normalized headline score in [0,1].")
    passed: bool = Field(..., description="Threshold decision the CI eval-gate consumes.")

    metrics: list[Metric] = Field(default_factory=list)
    rationale: str | None = Field(
        None, description="Judge/heuristic explanation — kept for failure analysis."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalReport(BaseModel):
    """Aggregate of many EvalResults — what a CI run or dashboard refresh emits."""

    suite: str = Field(..., description="Eval suite name, e.g. 'claims-auditor-nightly'.")
    results: list[EvalResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.passed for r in self.results) / len(self.results)
