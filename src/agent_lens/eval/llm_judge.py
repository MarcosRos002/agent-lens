"""LLM-as-judge evaluators (provider-agnostic).

WHY naive LLM-as-judge fails on agent traces (and what we do about it):
- Single-call judging ignores the *trajectory*: a correct final answer reached
  via wrong/expensive/unsafe steps should not score full marks.
- Long traces overflow context and bury the decisive step; judges get lost.
- Position/verbosity/self-preference biases inflate scores.
- Judges are non-deterministic, so a single sample is noisy.

Mitigations this module is designed around (implemented in later phases):
- Score the trajectory tree, not just the final output (rubric over steps).
- Decompose into per-step judgments + reference-anchored rubrics.
- Pin judge model + temperature=0; record judge model_version in metadata.
- Optional self-consistency (k samples, majority/median) for high-stakes evals.

Providers are reached behind one interface: 'anthropic' direct, or 'openrouter'
/ 'openai' via the OpenAI-compatible client. The judge model id is explicit and
recorded so eval runs are reproducible.
"""

from __future__ import annotations

from agent_lens.schema import EvalResult, Trace


class TrajectoryJudgeEvaluator:
    """LLM-as-judge over a full agent trajectory (not a single call).

    Parameters
    ----------
    model:
        Judge model id, e.g. ``"claude-sonnet-4"`` or an OpenRouter slug.
    provider:
        ``"anthropic"`` | ``"openrouter"`` | ``"openai"``.
    rubric:
        Natural-language rubric the judge scores against.
    samples:
        Self-consistency samples (1 = single shot). >1 aggregates by median.
    """

    name = "llm_judge:trajectory"

    def __init__(
        self,
        *,
        model: str,
        provider: str = "anthropic",
        rubric: str,
        samples: int = 1,
    ) -> None:
        self.model = model
        self.provider = provider
        self.rubric = rubric
        self.samples = samples

    def evaluate(self, trace: Trace) -> EvalResult:  # pragma: no cover - Phase 0 stub
        ...
