# User Model & Scope System

## Overview

The `User` model handles scope-based field visibility. Different scopes expose different fields:
- **PUBLIC**: Read-only public profile (name, avatar, role, created_at)
- **PRIVATE**: Full user data including email (requires authentication as that user)
- **ADMIN**: Includes sensitive fields like google_id (superadmin only)

## Fields

| Field | Type | Scope | Nullable | Description |
|-------|------|-------|----------|-------------|
| id | UUID | All | No | Unique user identifier |
| email | String | PRIVATE, ADMIN | No | Email address |
| name | String | PUBLIC, PRIVATE, ADMIN | No | Display name (1-100 chars) |
| role | String | PUBLIC, PRIVATE, ADMIN | No | SUPERADMIN, APPROVER, AUTHOR, READER |
| avatar_url | String | PUBLIC, PRIVATE, ADMIN | Yes | Profile picture URL (R2) |
| google_id | String | ADMIN | Yes | Google OAuth ID (indexed) |
| is_active | Integer | PRIVATE, ADMIN | No | 0=banned, 1=active |
| created_at | Timestamp | PUBLIC, PRIVATE, ADMIN | No | Account creation time |
| updated_at | Timestamp | PRIVATE, ADMIN | No | Last profile update |

## Scope-Based Serialization

### to_dict(scope: Scope) → dict

```python
user = User(...)

# Public API response
user.to_dict(Scope.PUBLIC)
# → {"id", "name", "role", "avatar_url", "created_at"}

# Private API response (authenticated user)
user.to_dict(Scope.PRIVATE)
# → {"id", "name", "email", "role", "avatar_url", "is_active", "created_at", "updated_at"}

# Admin response
user.to_dict(Scope.ADMIN)
# → {"id", "name", "email", "role", "avatar_url", "is_active", "google_id", "created_at", "updated_at"}
```

## Database Schema

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'READER',
  avatar_url TEXT,
  google_id TEXT UNIQUE,
  is_active INTEGER NOT NULL DEFAULT 1,
  terms_accepted_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

## Usage in Handlers

```python
# Get user by ID with scope filtering
user = await svc.get_by_id(user_id, scope=Scope.PUBLIC)
response = user.to_dict(Scope.PUBLIC)  # Safe for public API

# Get private user data
me = await svc.get_by_id(auth_user['sub'], scope=Scope.PRIVATE)
response = me.to_dict(Scope.PRIVATE)  # Full profile with email
```

## Related Models

- **UserPreferences**: Topic interests, notification settings, theme
- **UserFollows**: One user following another (followers/following)
- **UserRole**: Permission levels (see enums.py)

## Validation

- **Email**: Must be unique, valid email format
- **Name**: 1-100 characters, not empty
- **Role**: Must be one of SUPERADMIN, APPROVER, AUTHOR, READER
- **Avatar URL**: Must be valid URL or None

---

See [API.md](./API.md) for endpoint documentation.
