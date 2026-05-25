# Telegram-native bot, not Discord multi-channel agents

OpenClaw Content Factory targets Discord with separate channels per agent and scheduled subagent runs. This product is a **single Telegram bot** using FSM + inline keyboards: onboarding grill, content sessions, and publish flows. Research/write/visual stages appear as **draft rounds** inside a session (and optional future `/research`), not as parallel Discord channels. Hard to reverse once FSM and DB schemas are built around chat_id-centric state.
