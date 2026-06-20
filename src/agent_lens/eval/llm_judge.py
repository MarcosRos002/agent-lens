"""LLM-as-judge evaluators (provider-agnostic).

WHY naive LLM-as-judge fails on agent traces (and what we do about it):
- Single-call judging ignores the *trajectory*: a correct final answer reached
  via wrong/expensive/unsafe steps should not score full marks.
- Long traces overflow context and bury the decisive step; judges get lost.
- Position/verbosity/self-preference biases inflate scores.
- Judges are non-deterministic, so a single sample is noisy.

Mitigations this module is built around:
- Score the whole trajectory (rubric rendered over every step), not just output.
- Force a **structured, validated** verdict (re-prompt once on invalid JSON).
- Pin the judge model + ``temperature=0`` in the adapter; record the judge
  ``model``/``provider`` in metadata so eval runs are reproducible.
- Optional **self-consistency**: ``samples`` verdicts aggregated by median.

The judge client is **injected** (a ``JudgeModel`` with ``complete(prompt)->str``)
so this is fully offline-testable. A real adapter for 'anthropic' direct or
'openrouter'/'openai' (OpenAI-compatible, temperature=0) is wired separately.
"""

from __future__ import annotations

import statistics
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from agent_lens.schema import EvalResult, Metric, MetricDirection, Trace

_REPROMPT = (
    "\n\nYour previous reply was not valid JSON for the required schema. "
    'Reply with ONLY: {"score": <0..1>, "rationale": "<text>", "evidence": ["<step ids>"]}'
)


class JudgeModel(Protocol):
    """Injected judge. The adapter pins temperature=0 and the model id."""

    def complete(self, prompt: str) -> str: ...


class JudgeVerdict(BaseModel):
    """The structured verdict a judge must return (validated)."""

    score: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    evidence: list[str] = Field(default_factory=list, description="Step ids/quotes cited.")


class TrajectoryJudgeEvaluator:
    """LLM-as-judge over a full agent trajectory (not a single call)."""

    name = "llm_judge:trajectory"

    def __init__(
        self,
        judge: JudgeModel,
        *,
        model: str,
        rubric: str,
        provider: str = "anthropic",
        samples: int = 1,
        pass_threshold: float = 0.7,
    ) -> None:
        self._judge = judge
        self.model = model
        self.provider = provider
        self.rubric = rubric
        self.samples = samples
        self.pass_threshold = pass_threshold

    def evaluate(self, trace: Trace) -> EvalResult:
        prompt = self._build_prompt(trace)
        verdicts = [self._one_sample(prompt) for _ in range(self.samples)]
        scores = [v.score for v in verdicts]
        score = statistics.median(scores)

        return EvalResult(
            evaluator=self.name,
            session_id=trace.session_id,
            score=score,
            passed=score >= self.pass_threshold,
            metrics=[
                Metric(
                    name="trajectory_score",
                    value=score,
                    direction=MetricDirection.HIGHER_IS_BETTER,
                    unit="ratio",
                )
            ],
            rationale=verdicts[0].rationale,
            metadata={
                "model": self.model,
                "provider": self.provider,
                "samples": self.samples,
                "scores": scores,
                "evidence": verdicts[0].evidence,
            },
        )

    def _one_sample(self, prompt: str) -> JudgeVerdict:
        raw = self._judge.complete(prompt)
        try:
            return JudgeVerdict.model_validate_json(raw)
        except ValidationError:
            raw = self._judge.complete(prompt + _REPROMPT)
            return JudgeVerdict.model_validate_json(raw)

    def _build_prompt(self, trace: Trace) -> str:
        lines = [
            "You are a strict evaluator of an AI agent's full trajectory.",
            "Score the WHOLE trajectory (right tools, sensible order, safe, "
            "cost-aware) — not just the final answer.",
            f"\nRubric:\n{self.rubric}",
            "\nAgent trace (one step per line):",
            *(self._render_step(i, e) for i, e in enumerate(trace.events)),
            '\nReturn ONLY JSON: {"score": <0..1>, "rationale": "<text>", '
            '"evidence": ["<step ids you relied on>"]}',
        ]
        return "\n".join(lines)

    @staticmethod
    def _render_step(i: int, event) -> str:
        bits = [f"[{i}] {event.kind.value} {event.name}", f"status={event.status.value}"]
        if event.tool_name:
            bits.append(f"tool={event.tool_name}")
        if event.error is not None:
            bits.append(f"error={event.error.message}")
        return "  " + " | ".join(bits)
