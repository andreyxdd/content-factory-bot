# All three publish providers in v1

v1 ships publish integrations for Telegram (channel/group), Instagram, and LinkedIn together—not a Telegram-only MVP with deferred social APIs. Telegram-only was rejected because the product brief treats multi-platform publish as core value, not a follow-up.

**Consequences:** Meta and LinkedIn developer app review, OAuth redirect hosting (FastAPI), encrypted token storage, and per-provider failure handling must be on the critical path before v1 launch. Schedule risk is accepted explicitly.
