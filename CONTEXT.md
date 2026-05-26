# Content Factory Bot (Telegram)

Telegram-native assistant that onboards creators via an interactive personality interview, then runs repeatable **content sessions** that draft posts and publish to connected social providers.

## Language

### Onboarding

**Creator**:
A human operator allowed to use the bot. Identified by Telegram user id after passing the allowlist gate.
_Avoid_: User, account (unless OAuth provider account)

**Allowlist**:
The closed set of Telegram identities permitted to use the bot. Membership is invite-only and operator-controlled; not inferred from country or phone locale.
_Avoid_: Whitelist (acceptable alias in ops docs only), international (ops wording only, not a bot rule)

**Primary language**:
The Creator's language for bot UI and generated content (`en` or `ru`). Seeded from **Telegram client locale** on first `/start`, confirmed in onboarding Q1, changeable via `/settings` or `/profile`.
_Avoid_: i18n (implementation)

**Telegram client locale**:
Inferred from Telegram `language_code` before onboarding: Russian UI if code is `ru` / `rus` / `ru-*`, else English. Not the same as final **primary language** until onboarding confirms.
_Avoid_: Locale, language_code (API field name)

**Onboarding session**:
The first-run (or re-run) interactive interview: **primary language** first, then personality questions. Persists answers as a **personality profile**.
_Avoid_: Grill session (process name only), setup, wizard

**Personality profile**:
The assembled set of **profile answers** from the onboarding grill (occupation, goals, audience, tone, limits, personal angle, etc.). Used as mandatory context for **writing step** and **review step**.
_Avoid_: Persona, brand kit, style guide (unless we add explicit brand assets later)

**Profile answer**:
One stored response to a single onboarding `question_key`. Editable later via `/profile` without re-running the full grill.
_Avoid_: Onboarding response, survey row

**Second brain**:
Internal durable memory for a Creator — context, voice, and values — compiled into prompts for pipeline steps. Not a separate chat surface in v1; no new Telegram command required.
_Avoid_: Second Brain Agent (implementation name), persona file, RAG index

**Creator memory**:
Atomic fact or preference the **second brain** stores beyond **profile answers** (e.g. recurring themes, refined tone rules, lessons from past sessions). Editable by the Creator; may be proposed automatically but not silently overwritten.
_Avoid_: Memory chunk, embedding, knowledge base row

**Memory note**:
A single **creator memory** entry: `label`, `body`, and `kind` (`voice` | `values` | `context` | `limit`). Optional `pinned` later. Distinct from **profile answer** (fixed grill keys) and from raw **session input** (ephemeral session material). Injected inside `<memory>`, separate from `<profile>`.
_Avoid_: Note, snippet, observation

**Memory kind**:
Category on a **memory note**: how the Creator sounds (`voice`), beliefs/positioning (`values`), situational facts (`context`), or hard boundaries (`limit`). Overlaps onboarding topics but may evolve without re-running the grill.
_Avoid_: Tag, category slug

**Memory update**:
Confirming a **memory suggestion** that targets an existing **memory note** (same `kind` + similar `label`) replaces or appends to that note — not a second duplicate row.
_Avoid_: Merge, patch

**Creator context**:
The compiled prompt bundle for a Creator: `<profile>` from **profile answers** plus `<memory>` from confirmed **memory notes**. Produced by one compiler used by research, writing, and review steps.
_Avoid_: Context pack, system prompt

**Memory suggestion**:
A proposed **memory note** awaiting Creator approval. Created after a **memory trigger** (e.g. session closed); not active in prompts until confirmed.
_Avoid_: Pending memory, AI draft

**Memory trigger**:
An event that may enqueue **memory suggestions** (not manual **memory note** creation). v1: session reaches `published` or `closed`; optional later: **profile answer** saved as **custom reply**, refinement **feedback** text.
_Avoid_: Webhook, cron

**Review step**:
Optional pipeline step after **writing step** when the Creator enabled it at onboarding. Scores draft quality vs **personality profile** and surfaces short feedback before menu selection.
_Avoid_: Review agent (implementation name), moderator

**Research default**:
Creator preference from onboarding for whether new **content sessions** start with **web research** on. Can be changed in `/profile` and overridden per session at `/new` setup.
_Avoid_: Web search setting, Sonar toggle (implementation)

**Recommendation**:
The bot's suggested pick among offered options during onboarding or drafting, shown before the Creator chooses.
_Avoid_: Default, auto-pick

**Custom reply**:
Free-text answer typed while an onboarding question is shown, when the three fixed options are insufficient.
_Avoid_: Other, write your own, fourth button

### Content workflow

**Content session**:
A bounded workflow started with `/new`, with its own **session title**, session flags (**web research**, **cover generation**), inputs (text/image/audio), draft iterations, optional publish, and terminal state. Stored for list/resume. At most one **active** session per Creator; starting `/new` while another is open must prompt resume, close-and-new, or cancel.
_Avoid_: Thread, chat, project

**Web research** (session flag):
When enabled for a **content session**, the bot runs a **research step** before the first **draft round**, producing a **research brief** from live web sources.
_Avoid_: RAG, search mode

**Research brief**:
Short structured summary of trends/sources for the session topic, consumed by the **writing step**. Absent when web research is off for that session.
_Avoid_: Research report, digest

**Cover generation** (session flag):
Chosen during `/new` **setup** (with destinations and web research), before session input. When on, bot runs a **cover step** after draft text is confirmed and before publish. Off by default.
_Avoid_: Thumbnail, image gen

**Session title**:
Human-readable label for a content session, used in session lists and resume pickers.
_Avoid_: Name, slug

**Initial draft menu**:
First menu after inputs (and optional **research brief**): three **draft options** plus **custom reply**. Creator selects one option or sends feedback without confirming final post yet.
_Avoid_: First round (vague)

**Follow-up menu**:
Second menu after an initial selection or feedback: either request **three new options** or **edit selected option only** (enters **refinement mode**), plus **custom reply**. Matches original product brief; not the same as jumping straight to publish.
_Avoid_: Second round (vague)

**Draft round**:
One **writing step** producing up to three **draft options** (initial draft menu, follow-up “three new”, or refinement 1+2). Excludes publish and cover steps.
_Avoid_: Generation, iteration (vague)

**Writing step**:
Generates **draft options** for a **draft round**, using **personality profile**, session inputs, and optional **research brief**. Pipeline: research → writing → (optional review) → cover.
_Avoid_: Draft orchestrator (implementation name), Writing Agent (Discord)

**Draft option**:
One candidate post (or segment) the Creator can select, refine, or replace.
_Avoid_: Variant, version

**Refinement mode**:
When the Creator asks to edit a single selected **draft option**, the next **draft round** shows exactly three buttons: (1) that option edited per their feedback, (2–3) two new alternatives, plus the fourth **custom reply** button. Not three revisions of the same option.
_Avoid_: Edit mode, single-option flow

**Publish intent**:
The Creator's choice of which **session destinations** receive the finalized content for one **content session** (one or more connected **providers**, not necessarily all connected).
_Avoid_: Cross-post, blast

**Published artifact**:
A record linking finalized content to provider post urls returned after successful publish.
_Avoid_: Post result, delivery

### Integrations

**Provider**:
An external channel where content can be published: Telegram (channel/group), Instagram, or LinkedIn. All three are **v1-required**; none are optional add-ons.
_Avoid_: Platform, social, integration (as noun)

**Provider connection**:
OAuth or Telegram-specific linkage storing tokens/scopes/channel ids needed to publish on behalf of the Creator.
_Avoid_: Account link, auth

**Telegram channel link**:
In-bot step: Creator forwards a channel/group post; bot checks it is **admin** in that chat, then creates or updates the Telegram **provider connection** with that `chat_id`.
_Avoid_: Connect Telegram (the DM with the bot is not the publish target)

**OAuth connect confirmation**:
After Instagram or LinkedIn OAuth callback stores a **provider connection**, the bot sends the Creator a Telegram DM (success or failure) and the browser shows a short HTML confirmation page.
_Avoid_: Deep link only, silent callback

**Provider setup**:
The step after **onboarding session** where the Creator links one or more publish targets. The bot opens the `/providers` screen automatically when personality onboarding finishes; `/providers` is also the command to return later.
_Avoid_: Connect wizard (process name only), `/connect` (use `/providers`)

**Setup complete**:
Creator may start `/new`: **personality profile** is ready and at least one **provider connection** is `active`. Does not require all three **providers**.
_Avoid_: Onboarding complete (personality only), profile ready

**Provider setup deferred**:
Creator finished personality onboarding but left **provider setup** without an active connection (e.g. “Skip for now”). May use `/profile`, `/settings`, `/providers`; `/new` stays blocked with a reminder to link at least one **provider**.
_Avoid_: Skipped onboarding

**Provider management**:
Viewing status, connecting, reconnecting, or disconnecting **provider connections** via `/providers` at any time. **Disconnect** via per-provider inline button (with confirm) or `/disconnect <provider>`. Reconnecting replaces the previous link for that **provider** (new OAuth or new forwarded channel).
_Avoid_: Change profile (use reconnect/disconnect)

**Session destinations**:
The subset of **provider connections** (status `active`) the Creator selects during `/new` **setup** for that **content session**. If exactly one is connected, that provider is implicit (no destination toggles). If two or more: default **all connected** ON; Creator toggles off for this session. Publish uses only this subset.
_Avoid_: Publish intent (broader term), platforms

### Flagged ambiguities

| Term | Conflict | Proposed resolution |
|------|----------|---------------------|
| Telegram as provider | Creator already *is* on Telegram; "connect Telegram" unclear | **Provider** means publish target (channel/group), not the bot chat itself |
| Telegram channel link | Forward alone proves ownership? | On forward, bot must be **admin** in that chat (`getChatMember`) before **provider connection** is saved |
| Content Factory | OpenClaw doc implies scheduled multi-agent Discord pipeline | This bot implements **interactive** research/write/publish loops; scheduled overnight pipeline is out of MVP unless explicitly added |

## Example dialogue

**Expert:** A Creator runs `/new` but hasn't finished onboarding. What happens?

**Dev:** Onboarding session is a hard prerequisite. Bot offers to start or resume onboarding; no content session until personality profile exists.

**Expert:** Onboarding done, but they never linked Instagram. Can they `/new` and post only to Telegram?

**Dev:** Yes, once **setup complete** (≥1 active **provider connection**). At `/new` **setup** they pick **session destinations** only from connected **providers** — e.g. Telegram only. They add Instagram later via `/providers` and use it on the next session.

**Expert:** They connected the wrong LinkedIn account yesterday.

**Dev:** `/providers` → Connect LinkedIn again (OAuth **reconnect** overwrites tokens). Same command as first **provider setup**; no `/connect`.

**Expert:** They pick draft option 2, then hit the fourth button and type "shorter, no emoji."

**Dev:** That's custom reply on a draft round. Next draft round runs in refinement mode unless they only wanted a light edit—in which case refinement mode returns one edited option plus two fresh alternatives.

**Expert:** They connected Instagram but publish fails mid-way.

**Dev:** Content session stays open; published artifacts record partial success per provider. Creator can retry publish intent without restarting `/new`.
