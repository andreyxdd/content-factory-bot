# OAuth + public URL setup

Grill Q3: hosted web flow (**B**). Operator has HTTPS domain; wire env + provider consoles.

## 1. Environment

```bash
PUBLIC_BASE_URL=https://your-domain.example   # no trailing slash
OAUTH_STATE_SECRET=long-random-string         # signs start links
```

Redirect URIs (register exactly in each developer console):

| Provider | Redirect URI |
|----------|----------------|
| Instagram (Meta) | `{PUBLIC_BASE_URL}/oauth/instagram/callback` |
| LinkedIn | `{PUBLIC_BASE_URL}/oauth/linkedin/callback` |

## 2. Run API sidecar

```bash
uv run uvicorn content_factory_bot.api.app:app --host 0.0.0.0 --port 8000
```

Bot and API share `DATABASE_URL`. Production: reverse proxy TLS terminates at your domain → port 8000.

## 3. Bot UX

`/providers` → inline buttons open:

- `{PUBLIC_BASE_URL}/oauth/instagram/start?uid=<telegram_user_id>&sig=<hmac>`
- `{PUBLIC_BASE_URL}/oauth/linkedin/start?uid=…&sig=…`

Telegram channel: in-bot flow (Phase 4), not OAuth web.

## 4. Meta (Instagram)

- Create Meta app → Instagram Graph / Facebook Login
- Scopes: `instagram_basic`, `instagram_content_publish`, `pages_show_list` (adjust per product)
- Add test users until app review passes

## 5. LinkedIn

- Create LinkedIn app → Sign In + Share / Marketing APIs per post type
- Request `w_member_social` or org scopes as needed

## 6. Verify

1. `GET {PUBLIC_BASE_URL}/health` → `200` with `{"status":"ok","checks":{"database":...,"redis":...,"config":...}}`
2. Open Instagram start URL from test allowlisted account
3. Confirm `provider_connections` row `status=active` after callback (Phase 4 implements token exchange)
