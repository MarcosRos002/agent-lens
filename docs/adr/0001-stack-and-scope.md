# ADR 0001 — Stack and scope

- **Status:** Accepted
- **Date:** 2026-06-14
- **Deciders:** Marcos Rostan

## Context

agent-lens is the eval + observability layer for the AI Engineer Portfolio
Program's flagship (`claims-auditor`). It must demonstrate the senior
AI-Engineer skill surface (evals being the #1 weighted 2026 skill), run on a
**100% free-tier** stack, and be **contract-first** so sibling repos can depend
on a stable wire format.

## Decision

### Tech stack

| Concern              | Choice                                   | Why |
| -------------------- | ---------------------------------------- | --- |
| Language             | **Python ≥ 3.11**                        | Ecosystem fit (OTel, pydantic, provider SDKs); matches sibling repos. |
| Schema / contract    | **pydantic v2**                          | Runtime validation + JSON (de)serialization for the cross-repo wire format. |
| Tracing              | **OpenTelemetry (api + sdk)**            | Vendor-neutral spans; clean span→`TraceEvent` mapping; free context propagation for `parent_step_id`. |
| Eval (LLM-as-judge)  | **Provider-agnostic** (Anthropic direct; OpenRouter/OpenAI via OpenAI-compatible client) | No lock-in; free-tier reachable via OpenRouter. |
| Metrics / dashboards | **prometheus-client → Prometheus → Grafana** | Free, self-hostable; standard P50/P95/P99 latency + cost charts. |
| CI eval-gate         | **GitHub Actions**                       | Free for public repos; native to where regressions enter. |
| Compat export        | **Langfuse / LangSmith concepts**        | Adoption path for teams already on a hosted platform. |
| Lint / format        | **ruff**                                 | Fast, single tool. |
| Tests                | **pytest**                               | Standard; schema contract is tested from Phase 0. |
| Packaging            | **setuptools + `src/` layout**, editable | `pip install -e ".[dev]"`. |

### Scope

**In scope:** trace-level evaluation, causal failure analysis, cost/latency
dashboards, CI eval-gates, the canonical `TraceEvent` contract, compatible
exporters.

**Out of scope:** being an agent framework or a Claude Code competitor; hosting a
SaaS; building agents themselves. agent-lens wraps *around* agents.

## When NOT to use agent-lens

Be honest about the trade-off — this is a senior signal:

- **You want a turnkey hosted platform with a UI, auth, and SSO out of the box.**
  Reach for **Langfuse** or **LangSmith**. agent-lens is a library you self-host
  and wire up; we provide *exporters* to those platforms precisely for this case.
- **You only need single-call eval** (one prompt → one response, no tools/steps).
  A lightweight LLM-as-judge or a hosted eval product is simpler; agent-lens's
  value is the *trajectory*.
- **You have no instrumentation budget and won't emit `TraceEvent`s.** Without
  trace data there's nothing to evaluate at trace level.
- **Hard real-time / sub-ms overhead constraints in the hot path.** Capture
  asynchronously or sample; don't block the agent on eval.

## Consequences

- The `TraceEvent` schema becomes public API; changes require an ADR + version bump.
- Free-tier constraint means LLM-judge runs should be cached/sampled to control cost.
- OTel choice keeps us interoperable but adds a dependency surface to learn.
