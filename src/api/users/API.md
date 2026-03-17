# Users API — Phase 6 Complete

All endpoints for user management, authentication, profiles, and preferences.

## Authentication

All endpoints except listed public ones require a valid JWT bearer token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### Public Endpoints (No Auth Required)

#### GET /api/users/:id
Retrieve public profile of a user by ID.

**Request:**
```
GET /api/users/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Authorization: Bearer <token>
```

**Response:** 200 OK
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Alice Author",
    "role": "AUTHOR",
    "avatar_url": "https://media.zenos.work/uploads/abc/def.jpg",
    "created_at": "2026-01-15T10:30:00Z"
  }
}
```

---

### Authenticated User Endpoints

#### GET /api/users/me
Retrieve the authenticated user's full profile (private scope).

**Request:**
```
GET /api/users/me HTTP/1.1
Authorization: Bearer <access_token>
```

**Response:** 200 OK
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Alice Author",
    "email": "alice@example.com",
    "role": "AUTHOR",
    "avatar_url": "https://media.zenos.work/uploads/abc/def.jpg",
    "is_active": 1,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-03-16T14:22:00Z"
  }
}
```

---

#### PUT /api/users/me
Update the authenticated user's profile (name and/or avatar URL).

**Request:**
```
PUT /api/users/me HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Alice Brown",
  "avatar_url": "https://media.zenos.work/uploads/new/avatar.jpg"
}
```

**Response:** 200 OK
```json
{
  "status": "updated"
}
```

**Validation:**
- At least one field (name or avatar_url) must be provided
- Name: 1-100 characters
- avatar_url: Optional, can be null to remove avatar

---

#### POST /api/users/me/avatar
Upload a new avatar image for the authenticated user.

**Request:**
```
POST /api/users/me/avatar HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: image/jpeg

[binary image data]
```

**Response:** 201 Created
```json
{
  "avatar_url": "https://media.zenos.work/uploads/550e8400-e29b-41d4-a716-446655440000/image-id-123.jpg",
  "key": "uploads/550e8400-e29b-41d4-a716-446655440000/image-id-123.jpg"
}
```

**Constraints:**
- Allowed types: image/jpeg, image/png, image/webp, image/gif
- Max file size: 5 MB

---

#### DELETE /api/users/me/avatar
Remove the user's avatar (no avatar URL).

**Request:**
```
DELETE /api/users/me/avatar HTTP/1.1
Authorization: Bearer <access_token>
```

**Response:** 200 OK
```json
{
  "avatar_url": null
}
```

---

#### GET /api/users/me/prefs
Retrieve the authenticated user's preferences.

**Request:**
```
GET /api/users/me/prefs HTTP/1.1
Authorization: Bearer <access_token>
```

**Response:** 200 OK
```json
{
  "prefs": {
    "topics": ["technology", "business", "science"],
    "email_notifs": 1,
    "theme": "dark"
  }
}
```

---

#### PUT /api/users/me/prefs
Update the authenticated user's preferences.

**Request:**
```
PUT /api/users/me/prefs HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "topics": ["technology", "ai", "startups"],
  "email_notifs": 1,
  "theme": "light"
}
```

**Response:** 200 OK
```json
{
  "status": "updated"
}
```

**Fields:**
- `topics`: Array of interest tags (strings)
- `email_notifs`: 0 or 1 (enable/disable email notifications)
- `theme`: "dark" or "light"

---

#### PUT /api/users/me/role
Self-upgrade from READER to AUTHOR role (one-way upgrade).

**Request:**
```
PUT /api/users/me/role HTTP/1.1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "role": "AUTHOR"
}
```

**Response:** 200 OK
```json
{
  "role": "AUTHOR"
}
```

**Constraints:**
- Only READER → AUTHOR upgrade allowed via this endpoint
- No downgrade possible
- Requires terms_accepted_at to be set before writing articles

---

#### PUT /api/users/me/accept-terms
Accept the platform's Writer Content Agreement (one-time, idempotent).

**Request:**
```
PUT /api/users/me/accept-terms HTTP/1.1
Authorization: Bearer <access_token>
```

**Response:** 200 OK
```json
{
  "terms_accepted": true,
  "terms_accepted_at": "2026-03-16T14:25:00Z"
}
```

**Notes:**
- Idempotent: second call is a no-op
- Required before user can create draft articles

---

#### DELETE /api/users/me
Deactivate the authenticated user's account (soft delete).

**Request:**
```
DELETE /api/users/me HTTP/1.1
Authorization: Bearer <access_token>
```

**Response:** 200 OK
```json
{
  "status": "deactivated"
}
```

**Side Effects:**
- User's is_active flag set to 0
- User can no longer log in
- TODO: Revoke all active sessions and tokens

---

### Admin Endpoints (Requires SUPERADMIN or APPROVER Role)

#### GET /api/users
List all users with pagination.

**Request:**
```
GET /api/users?page=1&limit=20 HTTP/1.1
Authorization: Bearer <superadmin_token>
```

**Query Parameters:**
- `page`: 1-based page number (default: 1)
- `limit`: Results per page, max 100 (default: 20)

**Response:** 200 OK
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Alice Author",
      "role": "AUTHOR",
      "avatar_url": "https://media.zenos.work/uploads/abc/def.jpg",
      "created_at": "2026-01-15T10:30:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440111",
      "name": "Bob Approver",
      "role": "APPROVER",
      "avatar_url": null,
      "created_at": "2026-01-10T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 147,
    "pages": 8
  }
}
```

---

#### PUT /api/users/:id/role
Set a user's role (SUPERADMIN-only authoritative role management).

**Request:**
```
PUT /api/users/550e8400-e29b-41d4-a716-446655440000/role HTTP/1.1
Authorization: Bearer <superadmin_token>
Content-Type: application/json

{
  "role": "APPROVER"
}
```

**Response:** 200 OK
```json
{
  "role": "APPROVER"
}
```

**Valid Roles:**
- SUPERADMIN
- APPROVER
- AUTHOR
- READER

---

#### PUT /api/users/:id/ban
Ban a user (revoke write access, deactivate account).

**Request:**
```
PUT /api/users/550e8400-e29b-41d4-a716-446655440000/ban HTTP/1.1
Authorization: Bearer <superadmin_token>
```

**Response:** 200 OK
```json
{
  "is_active": false
}
```

**Side Effects:**
- User's is_active set to 0
- User can no longer log in
- Existing articles remain visible but user cannot edit

---

#### PUT /api/users/:id/unban
Reactivate a banned user.

**Request:**
```
PUT /api/users/550e8400-e29b-41d4-a716-446655440000/unban HTTP/1.1
Authorization: Bearer <superadmin_token>
```

**Response:** 200 OK
```json
{
  "is_active": true
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "message": "User not found",
    "status": 404,
    "code": "NOT_FOUND"
  }
}
```

**Common Status Codes:**
- `400` - BAD_REQUEST: Invalid input
- `401` - UNAUTHORISED: Missing or invalid token
- `403` - FORBIDDEN: Insufficient permissions
- `404` - NOT_FOUND: Resource not found
- `409` - CONFLICT: Resource already exists
- `422` - VALIDATION_ERROR: Invalid field values
- `500` - INTERNAL_ERROR: Server error

---

## Data Models

### User (Public Scope)
```json
{
  "id": "uuid",
  "name": "string",
  "role": "SUPERADMIN|APPROVER|AUTHOR|READER",
  "avatar_url": "url|null",
  "created_at": "ISO8601 timestamp"
}
```

### User (Private Scope) ← Includes email & metadata
```json
{
  "id": "uuid",
  "email": "email",
  "name": "string",
  "role": "SUPERADMIN|APPROVER|AUTHOR|READER",
  "avatar_url": "url|null",
  "is_active": 0|1,
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

### Preferences
```json
{
  "topics": ["string"],
  "email_notifs": 0|1,
  "theme": "dark"|"light"
}
```

---

## Implementation Status: ✅ 100% COMPLETE

- ✅ Profile CRUD (read, update)
- ✅ Avatar upload/delete (via R2)
- ✅ Preferences management
- ✅ Role management (self-upgrade, admin assign)
- ✅ Terms acceptance tracking
- ✅ User listing (paginated)
- ✅ Ban/unban (admin)
- ✅ Account deactivation
- ✅ Error handling & validation

## Next: Phase 6 - Articles Module
