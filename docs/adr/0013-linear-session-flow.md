# ADR 0013: Linear `/new` session flow

## Status

Accepted (2026-06-01)

## Context

The `/new` setup screen mixed non-action headers, destination toggles, and action buttons. Drafting used a legacy three-option loop that did not match the onboarding “test in chat” script (angles A/B/C → full post → tribal check).

## Decision

1. **Publish-time destinations** — `Session destinations` are chosen only when the Creator picks **Post now** (all connected or specific). Setup keeps only web research and cover toggles.
2. **Strict FSM** — Linear states live in `session_states.py`; handlers route by state with a compatibility branch for legacy sessions until they close.
3. **Orchestration** — Persisted `system_prompt_text` is passed as the model `system` role; Style Card and user idea are structured inputs. Quality Gate runs internally (max 2 retries).
4. **Terminal semantics** — `ready_to_publish_later` stores full trace JSON + final text; public copy uses **Saved content**. Partial publish uses `partially_published` with per-provider retry.

## Consequences

- New migration: `content_sessions.session_trace_json`.
- Legacy `awaiting_draft_choice` / follow-up menus remain until old sessions finish.
- Worker notifies stage progress before angle delivery.
