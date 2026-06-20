"""Eval-gate runner used by the GitHub Action.

Compares a *current* ``EvalReport`` against a *baseline* and fails the build when
any gated quantity regresses beyond ``tolerance`` — **respecting each metric's
direction**, so lower-is-better metrics (cost, latency) can't silently pass when
they get worse.

Everything is unified into direction-aware quantities compared with a *relative*
tolerance:
- per-evaluator normalized ``score`` (higher-is-better),
- every ``Metric`` an evaluator emits (its own ``direction``).

Gating is **per-evaluator** (apples-to-apples), deliberately NOT the global
``pass_rate`` — that aggregate is confounded when the evaluator set changes (e.g.
adding a new, intentionally-strict evaluator would look like a regression).
Quantities present only in the current report (new evaluators/metrics) are not
gated — there is no baseline to regress against. An empty baseline (first run)
always passes.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from agent_lens.schema import EvalReport, MetricDirection


class GateOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True)
class Regression:
    key: str
    direction: MetricDirection
    baseline: float
    current: float

    def __str__(self) -> str:
        arrow = "down" if self.direction is MetricDirection.HIGHER_IS_BETTER else "up"
        return f"{self.key}: {self.baseline:.4g} -> {self.current:.4g} ({arrow}, regressed)"


@dataclass
class GateResult:
    outcome: GateOutcome
    regressions: list[Regression] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.outcome is GateOutcome.PASS

    def summary(self) -> str:
        if self.outcome is GateOutcome.PASS:
            return "eval-gate PASS - no regressions beyond tolerance."
        lines = "\n".join(f"  - {r}" for r in self.regressions)
        return f"eval-gate FAIL - {len(self.regressions)} regression(s):\n{lines}"


# (value, direction) for every gated quantity in a report, keyed by name.
_Gated = dict[str, tuple[float, MetricDirection]]


def _gated_quantities(report: EvalReport) -> _Gated:
    out: _Gated = {}
    for r in report.results:
        out[f"{r.evaluator}:score"] = (r.score, MetricDirection.HIGHER_IS_BETTER)
        for m in r.metrics:
            out[f"{r.evaluator}:{m.name}"] = (m.value, m.direction)
    return out


class EvalGate:
    """Compares a current EvalReport against a baseline and decides pass/fail.

    Parameters
    ----------
    tolerance:
        Allowed *relative* regression (fraction of the baseline magnitude) before
        the gate fails. With a zero baseline, ``tolerance`` is used as an absolute
        allowance.
    """

    def __init__(self, *, tolerance: float = 0.02) -> None:
        self.tolerance = tolerance

    def evaluate(self, current: EvalReport, baseline: EvalReport) -> GateResult:
        base = _gated_quantities(baseline)
        cur = _gated_quantities(current)
        regressions = [
            Regression(key, direction, b, cur[key][0])
            for key, (b, direction) in base.items()
            if key in cur and self._regressed(b, cur[key][0], direction)
        ]
        outcome = GateOutcome.FAIL if regressions else GateOutcome.PASS
        return GateResult(outcome=outcome, regressions=regressions)

    def check(self, current: EvalReport, baseline: EvalReport) -> GateOutcome:
        """Convenience: return just the PASS/FAIL outcome (CI exit-code source)."""
        return self.evaluate(current, baseline).outcome

    def _regressed(self, baseline: float, current: float, direction: MetricDirection) -> bool:
        allowed = abs(baseline) * self.tolerance if baseline else self.tolerance
        if direction is MetricDirection.HIGHER_IS_BETTER:
            return current < baseline - allowed
        return current > baseline + allowed


# --------------------------------------------------------------------------- #
# CLI entrypoint (invoked by the GitHub Action)
# --------------------------------------------------------------------------- #
def run_gate(
    baseline_path: str | Path, current_path: str | Path, *, tolerance: float = 0.02
) -> int:
    """Load two EvalReport JSON files, run the gate, return a CI exit code (0/1)."""
    baseline = EvalReport.model_validate_json(Path(baseline_path).read_text())
    current = EvalReport.model_validate_json(Path(current_path).read_text())
    result = EvalGate(tolerance=tolerance).evaluate(current, baseline)
    print(result.summary())
    return 0 if result.outcome is GateOutcome.PASS else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="agent-lens eval-gate")
    parser.add_argument("baseline", help="Path to the baseline EvalReport JSON.")
    parser.add_argument("current", help="Path to the current EvalReport JSON.")
    parser.add_argument(
        "--tolerance", type=float, default=0.02, help="Allowed relative regression."
    )
    args = parser.parse_args(argv)
    return run_gate(args.baseline, args.current, tolerance=args.tolerance)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
