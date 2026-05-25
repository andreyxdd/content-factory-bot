# Critical review — flaws, risks, improvements

Grill-with-docs + spec stress test. Severity: **blocker** | **high** | **medium** | **low**.

## Blockers

1. **"Telegram" as social provider is ambiguous**  
   Creators already chat in Telegram. Connecting "Telegram" must mean **channel/group publish target** (bot admin + `chat_id`), not personal profile posting. Without that definition, OAuth UX and permissions are undefined.

2. **Instagram / LinkedIn API reality**  
   Publishing requires app review, business/creator accounts, token refresh, rate limits, and content-type constraints (carousel vs single image). MVP cannot assume "connect in chat → post works" without a hosted OAuth web flow and compliance checklist.

3. **Allowlist "international Telegram accounts"**  
   Not operationalized: country? phone prefix? manual curator list? Until defined, you cannot implement the gate or audit access.

4. **Fourth button + free text inside FSM**  
   Telegram delivers messages asynchronously. If Creator sends text while a keyboard is showing, state can desync. Need explicit `awaiting_custom_reply` state and ignore stray messages with guidance.

## High

5. **No scheduled research pipeline**  
   Original CF value is overnight chained agents. This spec is interactive-only. Risk: product feels like "ChatGPT with buttons" unless `/research` or session-prefill adds Research-Agent equivalent.

6. **Session resume + `/new` concurrency**  
   What if two open sessions? Recommend: one `active` session per Creator; `/new` offers "close current?" or auto-archive.

7. **Multimodal cost and latency**  
   Audio STT + image vision + 3-option LLM per round = expensive. Need per-Creator quotas, max rounds per session, and async "still working…" messages.

8. **Refinement mode underspecified**  
   "One option edited" vs "three more options" changes prompts and UX. Must be one explicit rule (see CONTEXT refinement mode).

9. **Security**  
   OAuth tokens and personality data are sensitive. Encrypt at rest, rotate refresh tokens, never log draft content at info level.

10. **Content safety**  
    Generated posts on LinkedIn/IG have policy risk. Add pre-publish checklist (claims, PII, defamation) especially for regulated niches.

## Medium

11. **Session title UX**  
    Auto-title from first message may be garbage for voice notes. Prompt for title early or editable via `/rename`.

12. **Partial publish failure**  
    Spec mentions retry; UI must show per-provider status not a single success boolean.

13. **Onboarding re-run**  
    `/onboarding` invalidates old profile mid-flight sessions. Version profile and snapshot into active session.

14. **Operator tooling**  
    Allowlist only in env vars is fine for 10 users; breaks at 100. Plan `/admin_allowlist` or external admin panel.

15. **Testing**  
    Telegram FSM needs integration tests with aiogram test harness; provider APIs mocked.

## Low / polish

16. **i18n** — UI English first; personality profile may be multilingual.
17. **Analytics** — track round count, time-to-publish, provider success.
18. **Deep links** — `t.me/bot?start=resume_<id>` for session resume from notifications.

## Improvements (prioritized)

| Priority | Improvement |
|----------|----------------|
| P0 | Define allowlist + Telegram provider precisely (grill Q1–Q2) |
| P0 | v1 all providers (Q2=C): start Meta + LinkedIn dev apps immediately; OAuth host on FastAPI |
| P1 | Async worker for LLM/STT; bot sends progress messages |
| P1 | Personality profile versioning |
| P2 | `/research` brief step inside `/new` |
| P2 | Scheduled daily digest (OpenClaw parity) |
| P3 | Thumbnail/cover generation sub-step |

## Falsifiable predictions (for you to challenge)

- If IG/LI are in MVP, first publish will land **>4 weeks** after bot MVP due to app review — unless you defer them.
- Creators will use **custom reply** on >40% of draft rounds — keyboard UX must be excellent.
- Without `/cancel`, support burden from stuck FSM will dominate operator time.

What would change my mind: documented allowlist source of truth; signed LOI with Meta/LinkedIn dev programs; or explicit MVP cut to Telegram-only publish.
