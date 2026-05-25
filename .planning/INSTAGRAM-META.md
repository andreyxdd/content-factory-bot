# Instagram posting — why “Meta review” matters

You **do** “just use the Instagram API” — but that API is **Meta’s Instagram Graph API**, and Meta gates **production** access.

## What you build technically

1. Creator connects **Instagram Business or Creator** account (linked to a Facebook Page).
2. OAuth stores a **user access token** with publish scopes.
3. Your server calls Graph API endpoints to create media containers and publish.

That matches your mental model: post **on behalf of the connected user**.

## What “Meta app review” is

A **Facebook Developer App** starts in **Development mode**:

| Mode | Who can connect | Who you can publish for |
|------|-----------------|-------------------------|
| **Development** | Test users / roles added in Meta dashboard | Only those testers |
| **Live** (after **App Review**) | Any real user authorizing your app | Real Creators in production |

**App Review** = Meta manually approves requested **permissions** (e.g. `instagram_content_publish`, `pages_show_list`) before non-test users can OAuth and publish.

Without approval:

- Your bot works for **you + named testers only**
- A random allowlisted Creator **cannot** complete Instagram connect/publish in production

LinkedIn has a similar **developer program / product approval** for posting scopes.

## What to do in parallel (not optional for v1 gate)

1. Create Meta app → add Instagram Graph product.
2. Document **screencast + use case** (“creator bot publishes drafts user approved in Telegram”).
3. Submit permissions for review **early** — calendar risk is real.
4. Use **test accounts** for all dev until Live.

## Bottom line

No separate “Meta review product” — it’s the **approval to use publish permissions on real users’ IG accounts**. API-only is correct; review is the gate on that API in production.
