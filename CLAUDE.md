# CLAUDE.md — agent-lens

> Best entry point for a fresh Claude Code session. Read this first, then
> `docs/architecture.md` and `docs/contracts/`.

## What this repo is

**agent-lens** is a pip-installable, open-source library for **evaluation +
observability of LLM agents** — the production layer you build *around* any
agent. It is explicitly **not** a competitor to Claude Code or to any agent
framework; it is the measurement/observability harness you wrap around them.

Its headline differentiator is **trace-level evaluation** (not single-call):
it scores whole multi-step agent trajectories — tool-call correctness, step
ordering, causal failure analysis — rather than grading one prompt/response in
isolation. See `docs/architecture.md`.

Core capabilities:
- **Trace-level eval**: tool-call correctness, trajectory scoring, multi-turn
  traces; addresses why naive LLM-as-judge fails on agent traces + mitigations.
- **Causal failure analysis** across multi-step sessions.
- **Cost/latency dashboards** (P50/P95/P99, tokens, cost/session) via
  OpenTelemetry → Prometheus/Grafana.
- **CI eval-gates**: a GitHub Action that blocks merges on eval regression
  (e.g., when a model version bumps).
- Defines the **canonical `TraceEvent` schema** that the flagship
  `claims-auditor` emits and this library consumes. **This schema is the key
  contract** — design/change it carefully.

## Role in the program (it measures the flagship)

agent-lens is the **measurement layer** for the flagship `claims-auditor`.
claims-auditor emits `TraceEvent`s; agent-lens consumes them to evaluate
trajectories, analyze failures, and chart cost/latency. The `TraceEvent` schema
in this repo (`src/agent_lens/schema/trace.py`) is the cross-repo contract.

## Sibling repos (part of a 4-repo program)
- claims-auditor (flagship): https://github.com/MarcosRos002/claims-auditor
- agent-lens (eval/observability): https://github.com/MarcosRos002/agent-lens
- fine-tune-lab (LoRA/distillation): https://github.com/MarcosRos002/fine-tune-lab
- portfolio (website): https://github.com/MarcosRos002/portfolio
Relationship: claims-auditor is measured by agent-lens, fed a cheap model by fine-tune-lab, and exhibited in portfolio.

## Conventions

- **Contract-first.** The `TraceEvent` / `EvalResult` schemas in
  `src/agent_lens/schema/` are public API. Changing a field is a breaking change
  and requires updating `docs/contracts/` + a new ADR. Treat them like a wire format.
- **Docs are context infrastructure.** Every module has a `docs/modules/*.md`.
  Keep them current; they're how the next agent gets context.
- **100% free-tier stack.** Provider-agnostic LLM-as-judge (Anthropic direct or
  OpenRouter/OpenAI-compatible). No paid SaaS required to run.
- **Python ≥ 3.11**, package name `agent-lens`, import name `agent_lens`,
  `src/` layout.
- **Lint/format** with ruff; **test** with pytest. Run both before committing.
- **Package manager (JS/Node tooling): pnpm only — never use npm or npx.**
- The `schema/` package is **concrete**; everything else is currently a
  Phase-0 stub (`...` bodies). Implement behind the existing signatures.

## Install / test / lint

```bash
make install        # pip install -e ".[dev]"
make test           # pytest  (schema contract tests already pass)
make lint           # ruff check .
make fmt            # ruff --fix + format
python examples/instrument_toy_agent.py   # builds + prints a demo trace
```

## Where things live / pointers to docs

- `src/agent_lens/schema/` — **the contract** (concrete): `TraceEvent`, `Trace`,
  `EvalResult`, `Metric`, `EvalReport`.
- `src/agent_lens/tracing/` — OTel capture (decorators/context managers). Stub.
- `src/agent_lens/eval/` — evaluators: `Evaluator` Protocol, LLM-as-judge,
  heuristics, trajectory/tool-call scoring. Stub.
- `src/agent_lens/analysis/` — causal failure analysis over sessions. Stub.
- `src/agent_lens/dashboards/` — Prometheus exporter + Grafana JSON. Stub.
- `src/agent_lens/ci/` — eval-gate runner for GitHub Actions. Stub.
- `src/agent_lens/exporters/` — Langfuse/LangSmith-compatible export. Stub.
- `docs/architecture.md` — how tracing→eval→analysis→dashboards→ci fit together.
- `docs/contracts/` — canonical `TraceEvent` spec, Evaluator Protocol, Metric.
- `docs/adr/0001-stack-and-scope.md` — stack decision + when NOT to use this.
- `docs/orchestration.md` — dependency graph + parallel worktree plan.
- `docs/modules/*.md` — one per module (purpose, interface, deps, tests, concerns).
- `docs/context/handoff.md` — current phase + next steps. **Read this to resume.**

## Current status

**Phase 0 (context-readiness) complete.** Structure, docs, concrete `TraceEvent`
contract, and stubs are in place. Next: finalize the `TraceEvent` schema in
`docs/contracts/` (it's the cross-repo contract with claims-auditor), then build
`tracing` + `eval` in parallel worktrees. See `docs/context/handoff.md`.
