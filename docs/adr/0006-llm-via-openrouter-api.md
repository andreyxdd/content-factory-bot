# Draft generation via OpenRouter (OpenAI-compatible HTTP API)

Content draft rounds call an **in-process orchestrator** in Python that builds prompts from the personality profile and session history, then invokes an **LLM HTTP client** (default: OpenRouter, OpenAI-compatible `/v1/chat/completions`) with **structured JSON output** for three draft options. We do not run Claude Code, Cursor agent harnesses, or OpenClaw-style subagent spawns in the request path—those are dev-time or a different product shape.

**Alternatives rejected:** (1) Claude Code / IDE agent as runtime—wrong tenancy, latency, and ops model for a multi-user bot. (2) Heavy agent frameworks as the core loop—extra indirection before FSM is proven. (3) Three separate remote “agents” per round—cost and failure modes without v1 need.

**Models:** Routing and model id live in config (e.g. primary draft model, cheap model for title/summary). “Hermes” is a **model choice on OpenRouter**, not a separate runtime tier, unless we later add a dedicated worker service.
