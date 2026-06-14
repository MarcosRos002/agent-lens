# Contract: the canonical `TraceEvent` schema

**Status:** authoritative. This is the **cross-repo contract** between
`claims-auditor` (producer) and `agent-lens` (consumer). The Python source of
truth is [`src/agent_lens/schema/trace.py`](../../src/agent_lens/schema/trace.py);
this document is the human-readable spec. **They must stay in sync.**

> Changing any field below is a **breaking change**. Bump `SCHEMA_VERSION`,
> update this doc, and write an ADR. Producers and consumers negotiate on
> `schema_version`.

## Model: `TraceEvent`

One `TraceEvent` = **one step** of an agent run. A full run is an ordered list of
events sharing a `session_id`, linked into a tree by `parent_step_id`. The
wrapper type is `Trace` (`{ session_id, events[], metadata }`).

### Fields

| Field            | Type                       | Req | Description |
| ---------------- | -------------------------- | --- | ----------- |
| `schema_version` | `str`                      | def | Schema version; defaults to `SCHEMA_VERSION`. Used for compat negotiation. |
| `session_id`     | `str`                      | ✅  | Groups all steps of one agent run (the "trace" id). |
| `step_id`        | `str`                      | ✅  | Unique id of **this** step within the session. |
| `parent_step_id` | `str \| null`              | —  | Id of the causing step; `null` for the root. Forms the trajectory tree. |
| `kind`           | `StepKind` enum            | ✅  | `llm` · `tool` · `retrieval` · `agent` · `guardrail` · `other`. |
| `name`           | `str`                      | ✅  | Human-readable step name (tool name, agent node, model role). |
| `tool_name`      | `str \| null`              | —  | Tool/function name when `kind == tool`. |
| `inputs`         | `dict[str, Any]`           | def | Step inputs (args/prompt/query). **Redact PII before emit.** |
| `output`         | `Any \| null`              | —  | Step output (tool return, completion, retrieved docs). |
| `model`          | `str \| null`              | —  | Model id for LLM steps, e.g. `claude-sonnet-4`. |
| `provider`       | `str \| null`              | —  | `anthropic` · `openrouter` · `openai`. |
| `tokens`         | `TokenUsage`               | def | Token accounting (see below). Zeros for non-LLM steps. |
| `cost_usd`       | `float \| null`            | —  | Computed USD cost for this step. |
| `latency_ms`     | `float \| null`            | —  | Wall-clock duration of this step, ms. |
| `start_time`     | `datetime` (UTC, tz-aware) | ✅  | Step start. |
| `end_time`       | `datetime \| null`         | —  | Step end; `null` while in-flight. |
| `status`         | `StepStatus` enum          | def | `ok` · `error` · `timeout` · `cancelled`. Defaults `ok`. |
| `error`          | `ErrorInfo \| null`        | *  | **Required when `status == error`** (validated). |
| `metadata`       | `dict[str, Any]`           | def | Tags: env, git sha, `model_version`, `prompt_version`, A/B bucket, etc. |

Legend: ✅ required · def = has default · — = optional · * = conditionally required.

### `TokenUsage`

| Field               | Type          | Description |
| ------------------- | ------------- | ----------- |
| `prompt_tokens`     | `int` (0)     | Input tokens. |
| `completion_tokens` | `int` (0)     | Output tokens. |
| `total_tokens`      | `int` (0)     | Sum (producer-computed). |
| `cache_read_tokens` | `int \| null` | Prompt-cache reads (Anthropic/OpenRouter caching). |
| `cache_write_tokens`| `int \| null` | Prompt-cache writes. |

### `ErrorInfo`

| Field       | Type           | Description |
| ----------- | -------------- | ----------- |
| `type`      | `str`          | Exception/class name or error code. |
| `message`   | `str`          | Human-readable message. |
| `retryable` | `bool \| null` | Whether the agent could have retried. |
| `stack`     | `str \| null`  | Optional stack trace (truncate before emit). |

## Invariants (enforced in code)

1. `status == "error"` ⇒ `error` payload **must** be present.
2. Within a `Trace`, every event's `session_id` **must** equal the trace's `session_id`.
3. `parent_step_id`, when set, **should** reference an existing `step_id` in the
   same session (consumers may treat a dangling parent as a warning).

## Producer guidance (for claims-auditor)

- Emit one event per meaningful step (each LLM call, tool call, retrieval, guardrail).
- Set `parent_step_id` so the trajectory tree reconstructs the real causal flow.
- Populate `tokens`, `cost_usd`, `latency_ms` whenever known — dashboards depend on them.
- Put version/experiment context in `metadata` (`git_sha`, `model_version`,
  `prompt_version`) so the CI eval-gate can attribute regressions.
- **Redact PII/PHI** in `inputs`/`output` before emitting (claims data is sensitive).

## Example (JSON)

```json
{
  "schema_version": "0.1.0",
  "session_id": "audit-2026-0612-abc",
  "step_id": "step-2",
  "parent_step_id": "step-1",
  "kind": "tool",
  "name": "lookup_cpt_code",
  "tool_name": "lookup_cpt_code",
  "inputs": { "code": "99213" },
  "output": { "description": "Office visit, established patient" },
  "model": null,
  "provider": null,
  "tokens": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 },
  "cost_usd": 0.0,
  "latency_ms": 42.0,
  "start_time": "2026-06-12T10:00:01Z",
  "end_time": "2026-06-12T10:00:01Z",
  "status": "ok",
  "error": null,
  "metadata": { "git_sha": "abc123", "model_version": "veritas-0.3" }
}
```
