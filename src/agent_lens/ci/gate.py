"""Eval-gate runner used by the GitHub Action (Phase 0 stub)."""

from __future__ import annotations

from enum import Enum

from agent_lens.schema import EvalReport


class GateOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class EvalGate:
    """Compares a current EvalReport against a baseline and decides pass/fail.

    Parameters
    ----------
    tolerance:
        Allowed regression (absolute drop in pass_rate / gated score) before the
        gate fails the CI job.
    """

    def __init__(self, *, tolerance: float = 0.02) -> None:
        self.tolerance = tolerance

    def check(
        self, current: EvalReport, baseline: EvalReport
    ) -> GateOutcome:  # pragma: no cover - Phase 0 stub
        """Return PASS/FAIL by comparing current vs baseline within tolerance."""
        ...
