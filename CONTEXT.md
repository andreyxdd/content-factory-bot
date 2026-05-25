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
Free-text input via the fourth menu button when the three fixed options are insufficient.
_Avoid_: Other, write your own

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
The Creator's choice of which connected **providers** receive the finalized content (all connected, or a one-time subset).
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

### Flagged ambiguities

| Term | Conflict | Proposed resolution |
|------|----------|---------------------|
| Telegram as provider | Creator already *is* on Telegram; "connect Telegram" unclear | **Provider** means publish target (channel/group), not the bot chat itself |
| Content Factory | OpenClaw doc implies scheduled multi-agent Discord pipeline | This bot implements **interactive** research/write/publish loops; scheduled overnight pipeline is out of MVP unless explicitly added |

## Example dialogue

**Expert:** A Creator runs `/new` but hasn't finished onboarding. What happens?

**Dev:** Onboarding session is a hard prerequisite. Bot offers to start or resume onboarding; no content session until personality profile exists.

**Expert:** They pick draft option 2, then hit the fourth button and type "shorter, no emoji."

**Dev:** That's custom reply on a draft round. Next draft round runs in refinement mode unless they only wanted a light edit—in which case refinement mode returns one edited option plus two fresh alternatives.

**Expert:** They connected Instagram but publish fails mid-way.

**Dev:** Content session stays open; published artifacts record partial success per provider. Creator can retry publish intent without restarting `/new`.
