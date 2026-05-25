# Background worker from v1 (Redis queue)

Long-running work (Sonar research, draft generation, cover image, publish API calls) runs in a **worker process** backed by **Redis**, not inside the Telegram polling loop. The bot enqueues jobs, edits a progress message, and consumes results. Inline-only execution was rejected because research + writing routinely exceeds comfortable Telegram wait times and couples bot availability to LLM latency.
