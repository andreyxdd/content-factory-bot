# Python 3.12 + aiogram 3 + PostgreSQL

Telegram bots need mature FSM, callback routing, and file download APIs; aiogram 3 is the common choice in Python. PostgreSQL fits relational sessions, OAuth tokens, and audit trails. FastAPI sidecar handles OAuth redirects and webhooks. Alternatives (Node grammY, Go tgbotapi) were rejected to keep one language with LLM/media libraries. Swapping bot framework later is costly due to FSM rewrite.
