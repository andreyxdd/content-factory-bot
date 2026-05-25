# Model matrix — pipeline steps (OpenRouter-first)

Three **pipeline steps** map to OpenClaw agents (research → writing → thumbnail). Each step has a **primary** and **fallback** model/route via env. Transport remains OpenRouter HTTP unless noted.

**Token budget cap:** nice-to-have (monitoring first; hard cap later).

## Summary table

| Step | OpenClaw analog | Primary | Fallback | When it runs |
|------|-----------------|---------|----------|--------------|
| **Research** | Research Agent | `perplexity/sonar-pro` | `perplexity/sonar` | If session has **web research** enabled (see grill Q7) |
| **Writing** | Writing Agent | `anthropic/claude-sonnet-4` | `openai/gpt-4o` | Every draft round |
| **Review** | (quality gate) | `openai/gpt-4o` | `anthropic/claude-sonnet-4` | If Creator enabled **review step** at onboarding |
| **Cover** | Thumbnail Agent | `black-forest-labs/flux-1.1-pro` | `openai/dall-e-3` | Only if Creator enabled **cover generation** at `/new` |

## Research (web)

| | Model / route | Why |
|---|---------------|-----|
| **Primary** | `perplexity/sonar-pro` | Native web grounding, one call, good for trend/niche briefs |
| **Fallback** | `perplexity/sonar` | Same stack, lower cost/latency if pro unavailable |

**Grill Q7:** Sonar-only (no Tavily/Serper in v1). Tavily+mini can be a later ADR if citations become a compliance requirement.

**Output artifact:** **Research brief** (text) stored on session, fed into writing step.

Env:

```bash
LLM_MODEL_RESEARCH=perplexity/sonar-pro
LLM_MODEL_RESEARCH_FALLBACK=perplexity/sonar
```

## Writing (draft options)

| | Model | Why |
|---|--------|-----|
| **Primary** | `anthropic/claude-sonnet-4` | Strong long-form + instruction following for 3-option JSON |
| **Fallback** | `openai/gpt-4o` | Reliable structured output if Sonnet rate-limits/errors |

**Refinement rounds** use the same writing pair (no separate model).

Env:

```bash
LLM_MODEL_DRAFT=anthropic/claude-sonnet-4
LLM_MODEL_DRAFT_FALLBACK=openai/gpt-4o
```

## Cover (image — optional per session)

| | Model | Why |
|---|--------|-----|
| **Primary** | `black-forest-labs/flux-1.1-pro` | Quality/cost balance for social covers |
| **Fallback** | `openai/dall-e-3` | Mature image API on OpenRouter |

Image calls use OpenRouter **image** or provider-specific endpoints (implement in `CoverGenerator` — may not be `chat/completions`).

Env:

```bash
LLM_MODEL_IMAGE=black-forest-labs/flux-1.1-pro
LLM_MODEL_IMAGE_FALLBACK=openai/dall-e-3
```

## Review (optional)

| | Model | Why |
|---|--------|-----|
| **Primary** | `openai/gpt-4o` | Strong, consistent rubric-style critique and JSON scores |
| **Fallback** | `anthropic/claude-sonnet-4` | If OpenAI rate-limits |

**Input:** draft options JSON + personality profile + destinations.  
**Output:** per-option notes (voice match, clarity, CTA, risks) + optional 1–10 score; show in Telegram before **follow-up menu**.

Env:

```bash
LLM_MODEL_REVIEW=openai/gpt-4o
LLM_MODEL_REVIEW_FALLBACK=anthropic/claude-sonnet-4
```

**Not** a separate harness — one `ReviewStep` job on the worker queue.

## Fast auxiliary (not a pipeline agent)

| Use | Model |
|-----|--------|
| Session title, summaries | `openai/gpt-4o-mini` |
| Fallback | `google/gemini-2.5-flash` |

```bash
LLM_MODEL_FAST=openai/gpt-4o-mini
LLM_MODEL_FAST_FALLBACK=google/gemini-2.5-flash
```

## Failure routing (application code)

1. Call primary with timeout (research 90s, writing 120s, image 180s).
2. On retryable error (429, 5xx, timeout) → **one** retry on **fallback** model.
3. Surface user-visible error; session stays resumable.

## Hermes / other models

`nousresearch/hermes-3-…` is a valid **writing fallback** swap if you prefer; not default — weaker structured JSON discipline than Sonnet/GPT-4o in practice.

## Verify slugs before ship

OpenRouter model ids change. Before production:

```bash
curl -s https://openrouter.ai/api/v1/models -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq -r '.data[].id' | rg -i 'sonar|claude-sonnet|gpt-4o|flux|dall-e'
```

Update env to match live ids.
