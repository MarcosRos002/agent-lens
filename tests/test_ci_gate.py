"""Tests for the CI eval-gate.

The gate compares a current EvalReport against a baseline and fails the build
when any gated quantity regresses beyond tolerance, **respecting each metric's
direction** (lower-is-better metrics like cost/latency must not silently pass).
"""

from __future__ import annotations

from agent_lens.ci.gate import EvalGate, GateOutcome
from agent_lens.schema import EvalReport, EvalResult, Metric, MetricDirection


def _result(evaluator, score, *, metrics=None):
    return EvalResult(
        evaluator=evaluator,
        session_id="s1",
        score=score,
        passed=score >= 0.5,
        metrics=metrics or [],
    )


def _report(*results):
    return EvalReport(suite="test", results=list(results))


def _cost(value):
    return Metric(
        name="cost_usd", value=value, direction=MetricDirection.LOWER_IS_BETTER, unit="usd"
    )


def test_passes_when_scores_hold() -> None:
    base = _report(_result("judge", 0.90))
    cur = _report(_result("judge", 0.90))
    assert EvalGate().check(cur, base) is GateOutcome.PASS


def test_fails_when_score_regresses_beyond_tolerance() -> None:
    base = _report(_result("judge", 0.90))
    cur = _report(_result("judge", 0.50))  # big drop
    result = EvalGate(tolerance=0.02).evaluate(cur, base)
    assert result.outcome is GateOutcome.FAIL
    assert any("judge:score" in r.key for r in result.regressions)


def test_small_drop_within_tolerance_passes() -> None:
    base = _report(_result("judge", 0.90))
    cur = _report(_result("judge", 0.895))  # within 2%
    assert EvalGate(tolerance=0.02).check(cur, base) is GateOutcome.PASS


def test_lower_is_better_metric_regression_fails() -> None:
    # Cost doubled — a higher-is-better-only gate would miss this.
    base = _report(_result("judge", 0.9, metrics=[_cost(0.010)]))
    cur = _report(_result("judge", 0.9, metrics=[_cost(0.020)]))
    result = EvalGate(tolerance=0.02).evaluate(cur, base)
    assert result.outcome is GateOutcome.FAIL
    assert any("cost_usd" in r.key for r in result.regressions)


def test_lower_is_better_metric_improvement_passes() -> None:
    base = _report(_result("judge", 0.9, metrics=[_cost(0.010)]))
    cur = _report(_result("judge", 0.9, metrics=[_cost(0.004)]))  # cheaper = good
    assert EvalGate(tolerance=0.02).check(cur, base) is GateOutcome.PASS


def test_empty_baseline_passes_first_run() -> None:
    base = _report()  # no prior results
    cur = _report(_result("judge", 0.9))
    assert EvalGate().check(cur, base) is GateOutcome.PASS


def test_new_evaluator_does_not_fail_the_gate() -> None:
    base = _report(_result("judge", 0.9))
    cur = _report(_result("judge", 0.9), _result("new_evaluator", 0.1))
    assert EvalGate().check(cur, base) is GateOutcome.PASS


def test_failure_summary_names_the_regressor() -> None:
    base = _report(_result("judge", 0.90))
    cur = _report(_result("judge", 0.40))
    result = EvalGate().evaluate(cur, base)
    assert "judge:score" in result.summary()


def test_run_gate_cli_returns_exit_codes(tmp_path) -> None:
    from agent_lens.ci.gate import run_gate

    base = tmp_path / "baseline.json"
    base.write_text(_report(_result("judge", 0.90)).model_dump_json())

    ok = tmp_path / "ok.json"
    ok.write_text(_report(_result("judge", 0.90)).model_dump_json())
    assert run_gate(base, ok) == 0  # no regression -> exit 0

    bad = tmp_path / "bad.json"
    bad.write_text(_report(_result("judge", 0.40)).model_dump_json())
    assert run_gate(base, bad) == 1  # regression -> non-zero exit fails CI
