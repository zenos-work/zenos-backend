# Zenos Backend
This repository contains the Cloudflare Workers–based backend for the Zenos
platform written in Python. It provides:

* Authentication (Google OAuth2 + JWT)
* User management (profiles, avatars, roles, preferences)
* Content APIs (articles, comments, tags, search)
* Admin functions (user management, content moderation)
* Media storage (R2 for avatars, images)
* Session management (KV for refresh tokens)
* SR-011 success-signal analytics (event capture + hourly aggregation)

## Overview

The service runs on Cloudflare's Workers runtime via `wrangler` and uses:

* Python FastAPI framework (compiled to Cloudflare Workers)
* SQLite database for persistence (`env.DB`)
* Cloudflare KV namespace for session storage (`env.SESSIONS`)
* Cloudflare R2 for media uploads (`env.MEDIA`)
* Google OAuth2 for authentication
* JWTs for stateless access control

## Getting Started

1. Install the [uv toolchain](https://docs.astral.sh/uv/getting-started/installation/).
2. Create and activate the virtual environment:
   ```sh
   uv venv
   uv sync
   ```
3. Configure your editor to use the `.venv` folder for Python.
4. Set up a `wrangler.jsonc` file with the following environment:
   ```jsonc
   [env.dev]
   "vars": {
     "ENVIRONMENT": "development",
     "FRONTEND_URL": "http://localhost:5173",
     "GOOGLE_CLIENT_ID": "your-google-client-id",
     "JWT_SECRET": "your-secret-key"
   }
   ```
5. Start the development server:
   ```sh
   wrangler dev
   ```

   The worker will listen on http://localhost:8787

## Project Structure

```
src/
├── auth/                  # Google OAuth2 + JWT tokens
│   ├── google.py         # Google OAuth exchange
│   ├── jwt_handler.py    # Token generation/verification
│   ├── models.py         # Auth data models
│   └── router.py         # Auth endpoints (login, callback, refresh)
│
├── api/                   # REST API modules
│   ├── users/            # User profiles, avatars, roles ✅
│   ├── articles/         # Article CRUD + approval workflow
│   ├── comments/         # Threaded discussions
│   ├── tags/             # Content tagging
│   ├── social/           # Likes, follows, bookmarks
│   ├── feed/             # Interest-based feed
│   ├── media/            # R2 upload management
│   └── admin/            # Superadmin functions
│
├── models/               # Data classes
│   ├── user/             # User, role models
│   ├── article/          # Article models
│   ├── common/           # Enums, base classes
│   └── base.py           # BaseModel, BaseRequest
│
├── middleware/           # Auth, logging middleware
├── db/                   # Database layer
└── utils/                # Helpers, validation
```

## API Modules

### ✅ Users (Complete - 16 endpoints)
Profile management, avatars, roles, preferences
- `GET /api/users/:id` — Public profile
- `GET /api/users/me` — My profile
- `PUT /api/users/me` — Update profile
- `POST /api/users/me/avatar` — Upload avatar
- `DELETE /api/users/me/avatar` — Remove avatar
- Plus: preferences, role management, terms, admin functions

📖 [Users API Docs](./src/api/users/API.md) | [Quick Reference](./src/api/users/QUICK_REFERENCE.md)

### 🟡 Articles (In Progress - 60%)
Content creation, draft/publish workflow, approval system

### 🟡 Comments (In Progress - 40%)
Threaded discussions, moderation

### ✅ Tags (Complete - 100%)
Content organization

### 🟡 Other Modules (20-40%)
- Social (likes, follows, bookmarks)
- Feed (recommendation engine)
- Media (R2 integration)
- Admin (governance, stats)

    Browser --> Frontend : "Login with Google"
    Frontend --> Worker : "POST /auth/google/callback"
    Frontend --> Worker : "POST /auth/refresh"
    Frontend --> Worker : "POST /auth/logout"
```

The backend exposes the following endpoints:

| Path                         | Method | Description |
|------------------------------|--------|-------------|
| `/auth/google/login`         | GET    | Redirect to Google OAuth consent screen |
| `/auth/google/callback`      | POST   | Accept authorization code and return JWTs; body `{code}` |
| `/auth/refresh`              | POST   | Accept refresh token and issue new access token |
| `/auth/logout`               | POST   | Revoke a refresh token |

### Request / Response Examples

#### Callback

```json
POST /auth/google/callback
{
  "code": "4/0Ab...
}
```

```json
200 OK
{
  "access_token": "eyJ...",
  "user": {"id": "...", "email": "...", "role": "READER"}
}
```

#### Refresh

```json
POST /auth/refresh
{
  "refresh_token": "eyJ..."
}
```

```json
200 OK
{
  "access_token": "eyJ..."
}
```

## Sequence and Use-Case Diagrams

See the Mermaid code above for a login sequence.  Additional diagrams can be
added under `docs/` or inline as needed.

## Development Notes

* This project is intentionally small; for larger applications you may want to
  introduce a proper routing library and separate controllers.
* All database interactions are asynchronous and use simple SQL strings;
  consider using an ORM if complexity grows.

## SR-011 Success Signals (Architecture)

SR-011 now runs on a two-layer model:

- Read-time UX signals in frontend (verification freshness, traction, outcome evidence)
- Backend analytics pipeline for durable hourly scoring

Backend pipeline details:

- Event capture table: `article_events`
- Hourly aggregate table: `article_success_hourly`
- Runtime event writes occur on:
  - Article views (`VIEW`)
  - Likes (`LIKE`)
  - Comment creation (`COMMENT`)
- Scheduled worker aggregation:
  - Worker entrypoint implements `on_scheduled`
  - Cron configured in [wrangler.jsonc](wrangler.jsonc) with `0 * * * *`
  - Aggregation computes per-article hourly counts and derived `success_rate`

To test scheduled execution locally:

```sh
curl "http://localhost:8787/cdn-cgi/handler/scheduled"
```

---

Feel free to update this document as the backend evolves.
