# zenos.work — Use Cases & System Flow Reference

All flows follow the 4-layer architecture:
`Handler → Service → Repository → D1/R2`

Each sequence diagram shows the exact class path from user action to response.

---

## Table of Contents

1. [Authentication](#1-authentication)
   - 1.1 Google Login
   - 1.2 Token Refresh
   - 1.3 Logout
2. [User Management](#2-user-management)
   - 2.1 View Own Profile
   - 2.2 Update Profile
   - 2.3 Upgrade to Author
   - 2.4 Update Topic Preferences
3. [Article Lifecycle](#3-article-lifecycle)
   - 3.1 Create Draft
   - 3.2 Submit for Approval
   - 3.3 Approve Article
   - 3.4 Reject Article
   - 3.5 Publish Article
   - 3.6 Edit Article
   - 3.7 Archive Article
   - 3.8 Delete Article
4. [Feed & Discovery](#4-feed--discovery)
   - 4.1 Home Feed (Personalised)
   - 4.2 Read Article
   - 4.3 Featured Carousel
   - 4.4 Following Feed
   - 4.5 Search Articles
   - 4.6 Browse by Tag
5. [Comments](#5-comments)
   - 5.1 Post Comment
   - 5.2 Reply to Comment
   - 5.3 Edit Comment
   - 5.4 Delete Comment
6. [Social Actions](#6-social-actions)
   - 6.1 Like Article
   - 6.2 Bookmark Article
   - 6.3 Follow Author
7. [Media](#7-media)
   - 7.1 Upload Cover Image
8. [Admin & Governance](#8-admin--governance)
   - 8.1 View Platform Stats
   - 8.2 View Approval Queue
   - 8.3 Ban User
   - 8.4 Assign Role
9. [MVP Coverage](#9-mvp-coverage)
    - 9.1 MVP1: Publishable Knowledge Platform
    - 9.2 MVP2: Trust, Compliance, and Moderation
    - 9.3 MVP3: Discovery and Growth Loops
10. [Frontend Use Cases](#10-frontend-use-cases)
    - 10.1 Frontend Use-Case Diagram
    - 10.2 Frontend Sequence: Create and Publish Flow

---

## 1. Authentication

### 1.1 Google Login

**Actor:** Any visitor
**Precondition:** None
**Result:** JWT access token + refresh token, user record upserted in D1

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant auth/router.py
    participant google.py
    participant jwt_handler.py
    participant D1 as D1 (users)
    participant KV as KV (sessions)

    User->>Frontend: Click "Continue with Google"
    Frontend->>auth/router.py: GET /auth/google/login
    auth/router.py-->>Frontend: 302 → accounts.google.com

    User->>Frontend: Approves Google consent screen
    Frontend->>auth/router.py: POST /auth/google/callback {code}

    auth/router.py->>google.py: exchange_code(code, env)
    google.py->>Google API: POST /token (code exchange)
    Google API-->>google.py: {access_token}
    google.py->>Google API: GET /userinfo (Bearer token)
    Google API-->>google.py: {id, email, name, picture}
    google.py-->>auth/router.py: {id, email, name, picture}

    auth/router.py->>D1: UPSERT users (ON CONFLICT google_id)
    D1-->>auth/router.py: row {id, email, name, role}

    auth/router.py->>jwt_handler.py: create_token(payload, secret, 900s)
    jwt_handler.py-->>auth/router.py: access_token (15 min)

    auth/router.py->>jwt_handler.py: create_token({type:refresh}, secret, 7d)
    jwt_handler.py-->>auth/router.py: refresh_token

    auth/router.py->>KV: put(refresh:{user_id}, refresh_token, ttl=7d)
    KV-->>auth/router.py: ok

    auth/router.py-->>Frontend: {access_token, refresh_token, user}
    Frontend->>Frontend: Store tokens in sessionStorage
    Frontend-->>User: Logged in ✓
```

### 1.2 Token Refresh

**Actor:** Authenticated user (token expired)
**Result:** New access token issued without re-login

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant auth/router.py
    participant jwt_handler.py
    participant KV as KV (sessions)
    participant D1 as D1 (users)

    User->>Frontend: Any authenticated action
    Frontend->>Backend: Request with expired access_token
    Backend-->>Frontend: 401 Unauthorised

    Frontend->>auth/router.py: POST /auth/refresh {refresh_token}
    auth/router.py->>jwt_handler.py: verify_token(refresh_token)
    jwt_handler.py-->>auth/router.py: payload {sub, type:refresh}

    auth/router.py->>KV: get(refresh:{user_id})
    KV-->>auth/router.py: stored_token

    Note over auth/router.py: Compare stored == submitted<br/>Prevents token reuse after logout

    auth/router.py->>D1: SELECT id, email, role WHERE id=?
    D1-->>auth/router.py: user row

    auth/router.py->>jwt_handler.py: create_token(payload, secret, 900s)
    jwt_handler.py-->>auth/router.py: new_access_token

    auth/router.py-->>Frontend: {access_token}
    Frontend->>Frontend: Update sessionStorage
    Frontend-->>User: Request retried transparently
```

### 1.3 Logout

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant auth/router.py
    participant KV as KV (sessions)

    User->>Frontend: Click Logout
    Frontend->>auth/router.py: POST /auth/logout {user_id}
    auth/router.py->>KV: delete(refresh:{user_id})
    KV-->>auth/router.py: ok
    auth/router.py-->>Frontend: {status: logged out}
    Frontend->>Frontend: Clear sessionStorage
    Frontend-->>User: Redirected to /login
```

---

## 2. User Management

### 2.1 View Own Profile

```mermaid
sequenceDiagram
    actor User
    participant handler.py as users/handler.py
    participant auth.py as middleware/auth.py
    participant service.py as UserService
    participant repo.py as UserRepository
    participant D1

    User->>handler.py: GET /api/users/me (Bearer token)
    handler.py->>auth.py: get_user(request, env)
    auth.py->>jwt_handler.py: verify_token(token)
    jwt_handler.py-->>auth.py: {sub, email, role}
    auth.py-->>handler.py: user payload

    handler.py->>service.py: get_by_id(user_id, scope=PRIVATE)
    service.py->>repo.py: find_by_id(user_id)
    repo.py->>D1: SELECT * FROM users WHERE id=?
    D1-->>repo.py: row
    repo.py->>User: from_row(row)
    User-->>repo.py: User instance
    repo.py-->>service.py: User instance
    service.py-->>handler.py: User instance

    handler.py->>User: to_dict(Scope.PRIVATE)
    User-->>handler.py: {id, email, name, role, is_active, ...}
    handler.py-->>User: 200 {user: {...}}
```

### 2.2 Update Profile

```mermaid
sequenceDiagram
    actor User
    participant handler.py as users/handler.py
    participant requests.py as UpdateProfileRequest
    participant service.py as UserService
    participant repo.py as UserRepository
    participant D1

    User->>handler.py: PUT /api/users/me {name, avatar_url}
    handler.py->>requests.py: from_body(body)
    Note over requests.py: Validates name not empty,<br/>max 100 chars
    requests.py-->>handler.py: UpdateProfileRequest

    handler.py->>service.py: update_profile(user_id, req)
    service.py->>repo.py: update_profile(user_id, name, avatar_url)
    repo.py->>D1: UPDATE users SET name=?, avatar_url=?, updated_at=now()
    D1-->>repo.py: ok
    repo.py-->>service.py: ok
    service.py-->>handler.py: ok
    handler.py-->>User: 200 {status: updated}
```

### 2.3 Upgrade to Author

**Actor:** READER role user who wants to publish content
**Business rule:** Self-upgrade only allowed READER → AUTHOR. Any other role change requires SUPERADMIN.

```mermaid
sequenceDiagram
    actor User as User (READER)
    participant handler.py as users/handler.py
    participant service.py as UserService
    participant repo.py as UserRepository
    participant D1

    User->>handler.py: PUT /api/users/me/role {role: AUTHOR}
    handler.py->>handler.py: Check role == AUTHOR (only allowed self-upgrade)

    handler.py->>service.py: self_upgrade_to_author(user_id)
    service.py->>repo.py: self_upgrade_role(user_id, AUTHOR, READER)
    repo.py->>D1: UPDATE users SET role=AUTHOR WHERE id=? AND role=READER
    Note over D1: WHERE role=READER prevents<br/>downgrading existing APPROVER/SUPERADMIN
    D1-->>repo.py: 1 row affected
    repo.py-->>service.py: ok

    service.py->>Logger: event(user.role_changed, {user_id, new_role: AUTHOR})
    service.py-->>handler.py: ok
    handler.py-->>User: 200 {role: AUTHOR}
```

### 2.4 Update Topic Preferences

```mermaid
sequenceDiagram
    actor User
    participant handler.py as users/handler.py
    participant service.py as UserService
    participant repo.py as UserRepository
    participant D1

    User->>handler.py: PUT /api/users/me/prefs {topics: [python, ai], theme: dark}
    handler.py->>service.py: update_prefs(user_id, topics, email_notifs, theme)

    service.py->>repo.py: ensure_prefs(user_id)
    repo.py->>D1: INSERT OR IGNORE INTO user_preferences (user_id)
    D1-->>repo.py: ok (idempotent)

    service.py->>repo.py: update_prefs(user_id, json(topics), ...)
    repo.py->>D1: UPDATE user_preferences SET topics=?, ...
    D1-->>repo.py: ok
    repo.py-->>service.py: ok
    service.py-->>handler.py: ok
    handler.py-->>User: 200 {status: updated}
```

---

## 3. Article Lifecycle

### 3.1 Create Draft

**Actor:** AUTHOR, APPROVER, or SUPERADMIN
**Result:** Article created with status=DRAFT

```mermaid
sequenceDiagram
    actor Author
    participant handler.py as articles/handler.py
    participant requests.py as ArticleCreateRequest
    participant service.py as ArticleService
    participant repo.py as ArticleRepository
    participant executor.py as D1Executor
    participant D1

    Author->>handler.py: POST /api/articles {title, content, tag_ids}
    handler.py->>middleware: get_user(request, env)
    middleware-->>handler.py: {sub, role: AUTHOR}
    handler.py->>handler.py: require_role(user, CAN_WRITE) ✓

    handler.py->>requests.py: from_body(body)
    Note over requests.py: Validates title ≤255 chars<br/>content ≥50 chars<br/>tag_ids is list
    requests.py-->>handler.py: ArticleCreateRequest

    handler.py->>service.py: create(req, author_id)
    service.py->>helpers: new_id() → uuid
    service.py->>helpers: unique_slug(title) → title-abc12345
    service.py->>helpers: calc_read_time(content) → N mins

    service.py->>repo.py: insert(aid, author_id, title, slug, ...)
    repo.py->>executor.py: run(INSERT_ARTICLE, ...)
    executor.py->>D1: prepare(sql).bind(...).run()
    D1-->>executor.py: ok

    loop For each tag_id
        repo.py->>executor.py: run(INSERT_ARTICLE_TAG, aid, tag_id)
        executor.py->>D1: INSERT OR IGNORE INTO article_tags
    end

    repo.py->>executor.py: first(SELECT_BY_ID_OR_SLUG, aid)
    executor.py->>D1: SELECT * FROM articles WHERE id=?
    D1-->>executor.py: row
    repo.py->>Article: from_row(row)

    service.py->>Logger: event(article.created, {article_id, author_id, title})
    service.py-->>handler.py: Article

    handler.py->>Article: to_dict(Scope.DETAIL)
    handler.py-->>Author: 201 {article: {...}}
```

### 3.2 Submit for Approval

```mermaid
sequenceDiagram
    actor Author
    participant handler.py as articles/handler.py
    participant service.py as ArticleService
    participant repo.py as ArticleRepository
    participant D1

    Author->>handler.py: POST /api/articles/:id/submit
    handler.py->>service.py: get_owner(article_id)
    service.py->>repo.py: find_author_id(article_id)
    repo.py->>D1: SELECT author_id FROM articles WHERE id=?
    D1-->>repo.py: author_id
    repo.py-->>handler.py: author_id

    handler.py->>handler.py: owner == user['sub'] ✓

    handler.py->>service.py: get_by_id_or_slug(article_id)
    service.py->>repo.py: find_by_id_or_slug(article_id)
    D1-->>repo.py: article row
    repo.py-->>handler.py: Article{status: DRAFT}

    handler.py->>handler.py: status in EDITABLE (DRAFT, REJECTED) ✓

    handler.py->>service.py: transition(article_id, SUBMITTED)
    service.py->>repo.py: set_status(article_id, SUBMITTED)
    repo.py->>D1: UPDATE articles SET status=SUBMITTED, updated_at=now()
    D1-->>repo.py: ok
    service.py->>Logger: event(article.submitted, {article_id})
    service.py-->>handler.py: SUBMITTED

    handler.py-->>Author: 200 {status: SUBMITTED}
```

### 3.3 Approve Article

**Actor:** APPROVER or SUPERADMIN

```mermaid
sequenceDiagram
    actor Approver
    participant handler.py as articles/handler.py
    participant service.py as ArticleService
    participant repo.py as ArticleRepository
    participant D1

    Approver->>handler.py: POST /api/articles/:id/approve
    handler.py->>middleware: get_user(request, env)
    middleware-->>handler.py: {sub, role: APPROVER}
    handler.py->>handler.py: require_role(user, CAN_APPROVE) ✓

    handler.py->>service.py: transition(article_id, APPROVED, actor_id)
    service.py->>repo.py: set_status(article_id, APPROVED, approved_by=actor_id)
    repo.py->>D1: UPDATE articles SET status=APPROVED, approved_by=?, updated_at=now()<br/>WHERE id=? AND status=SUBMITTED
    Note over D1: AND status=SUBMITTED prevents<br/>approving already-published articles
    D1-->>repo.py: ok
    service.py->>Logger: event(article.approved, {article_id, actor_id})
    service.py-->>handler.py: APPROVED
    handler.py-->>Approver: 200 {status: APPROVED}
```

### 3.4 Reject Article

```mermaid
sequenceDiagram
    actor Approver
    participant handler.py as articles/handler.py
    participant requests.py as RejectArticleRequest
    participant service.py as ArticleService
    participant repo.py as ArticleRepository
    participant D1

    Approver->>handler.py: POST /api/articles/:id/reject {note: "needs more detail"}
    handler.py->>handler.py: require_role(user, CAN_APPROVE) ✓

    handler.py->>requests.py: from_body(body)
    Note over requests.py: Validates note not empty, ≤1000 chars
    requests.py-->>handler.py: RejectArticleRequest{note}

    handler.py->>service.py: transition(article_id, REJECTED, note=req.note)
    service.py->>repo.py: set_status(article_id, REJECTED, rejection_note=note)
    repo.py->>D1: UPDATE articles SET status=REJECTED, rejection_note=?, updated_at=now()
    D1-->>repo.py: ok
    service.py->>Logger: event(article.rejected, {article_id, actor_id})
    service.py-->>handler.py: REJECTED
    handler.py-->>Approver: 200 {status: REJECTED}

    Note over D1: Author sees rejection_note<br/>in Scope.ADMIN view of their article<br/>and can resubmit after editing
```

### 3.5 Publish Article

**Precondition:** Article must be in APPROVED state

```mermaid
sequenceDiagram
    actor Approver
    participant handler.py as articles/handler.py
    participant service.py as ArticleService
    participant repo.py as ArticleRepository
    participant D1

    Approver->>handler.py: POST /api/articles/:id/publish
    handler.py->>handler.py: require_role(user, CAN_APPROVE) ✓
    handler.py->>service.py: transition(article_id, PUBLISHED)
    service.py->>repo.py: set_status(article_id, PUBLISHED, publish=True)
    repo.py->>D1: UPDATE articles SET status=PUBLISHED,<br/>published_at=datetime('now'), updated_at=now()<br/>WHERE id=? AND status=APPROVED
    Note over D1: AND status=APPROVED prevents<br/>publishing unapproved articles
    D1-->>repo.py: ok
    service.py->>Logger: event(article.published, {article_id, actor_id})
    service.py-->>handler.py: PUBLISHED
    handler.py-->>Approver: 200 {status: PUBLISHED}
```

### 3.6 Edit Article

**Precondition:** Article must be DRAFT or REJECTED
**Actor:** Article's own author, or SUPERADMIN

```mermaid
sequenceDiagram
    actor Author
    participant handler.py as articles/handler.py
    participant requests.py as ArticleUpdateRequest
    participant service.py as ArticleService
    participant repo.py as ArticleRepository
    participant D1

    Author->>handler.py: PUT /api/articles/:id {title, content, tag_ids}

    handler.py->>service.py: get_by_id_or_slug(article_id)
    service.py->>repo.py: find_by_id_or_slug(article_id)
    D1-->>repo.py: article row
    repo.py-->>handler.py: Article{author_id, status: DRAFT}

    handler.py->>handler.py: article.author_id == user sub ✓
    handler.py->>handler.py: article.status in EDITABLE ✓

    handler.py->>requests.py: from_body(body)
    Note over requests.py: All fields optional<br/>Missing fields keep current value
    requests.py-->>handler.py: ArticleUpdateRequest

    handler.py->>service.py: update(article_id, req, current_article)
    service.py->>service.py: title = req.title or current.title
    service.py->>service.py: content = req.content or current.content
    service.py->>helpers: calc_read_time(content)

    service.py->>repo.py: update(article_id, title, content, ...)
    repo.py->>D1: UPDATE articles SET title=?, content=?, ..., updated_at=now()
    D1-->>repo.py: ok

    alt tag_ids provided
        service.py->>repo.py: sync_tags(article_id, tag_ids)
        repo.py->>D1: DELETE FROM article_tags WHERE article_id=?
        repo.py->>D1: INSERT OR IGNORE INTO article_tags (article_id, tag_id) × N
    end

    repo.py->>D1: SELECT updated article
    D1-->>repo.py: updated row
    repo.py-->>handler.py: Updated Article

    handler.py->>Article: to_dict(Scope.DETAIL)
    handler.py-->>Author: 200 {article: {...}}
```

---

## 4. Feed & Discovery

### 4.1 Home Feed (Personalised)

```mermaid
sequenceDiagram
    actor User
    participant handler.py as feed/handler.py
    participant service.py as FeedService
    participant repo.py as FeedRepository
    participant D1

    User->>handler.py: GET /api/feed/home (optional Bearer token)
    handler.py->>middleware: get_user(request, env) — optional

    alt User is logged in
        handler.py->>D1: SELECT topics FROM user_preferences WHERE user_id=?
        D1-->>handler.py: topics JSON array

        alt User has topic preferences
            handler.py->>service.py: home(page, user_id, topics)
            service.py->>repo.py: find_by_topics(topics, limit, offset)
            repo.py->>D1: SELECT DISTINCT articles ... WHERE t.slug IN json_each(topics)
            D1-->>repo.py: personalised rows
            repo.py-->>service.py: [Article, ...]
            service.py->>Logger: analytics(feed.loaded, {feed_type: personalised})
            service.py-->>handler.py: {articles, feed: personalised}
        end
    end

    alt No preferences or not logged in
        handler.py->>service.py: home(page, user_id=None, topics=[])
        service.py->>repo.py: find_latest(limit, offset)
        repo.py->>D1: SELECT articles WHERE status=PUBLISHED ORDER BY published_at DESC
        D1-->>repo.py: latest rows
        repo.py-->>service.py: [Article, ...]
        service.py->>Logger: analytics(feed.loaded, {feed_type: latest})
        service.py-->>handler.py: {articles, feed: latest}
    end

    handler.py->>Article: to_dict(Scope.LIST) for each
    handler.py-->>User: 200 {articles: [...], feed: type, page: N}
```

### 4.2 Read Article

```mermaid
sequenceDiagram
    actor Reader
    participant handler.py as articles/handler.py
    participant service.py as ArticleService
    participant repo.py as ArticleRepository
    participant D1

    Reader->>handler.py: GET /api/articles/:id_or_slug
    handler.py->>service.py: get_by_id_or_slug(identifier)
    service.py->>repo.py: find_by_id_or_slug(identifier)

    repo.py->>D1: SELECT a.*, u.name, u.avatar_url FROM articles a<br/>JOIN users u WHERE a.id=? OR a.slug=?
    D1-->>repo.py: article row with author info

    repo.py->>Article: from_row(row)
    repo.py->>D1: SELECT tags WHERE article_id=? (via _fetch_tags)
    D1-->>repo.py: tag rows
    repo.py->>Tag: from_row(row) for each
    repo.py->>Article: article.tags = [Tag, ...]
    repo.py-->>service.py: Article with tags

    service.py-->>handler.py: Article

    handler.py->>service.py: increment_views(article.id)
    service.py->>repo.py: increment_views(article_id)
    repo.py->>D1: UPDATE articles SET views_count = views_count + 1
    service.py->>Logger: analytics(article.viewed, {article_id})

    handler.py->>Article: to_dict(Scope.DETAIL)
    handler.py-->>Reader: 200 {article: {content, tags, author, ...}}
```

---

## 5. Comments

### 5.1 Post Comment

```mermaid
sequenceDiagram
    actor User
    participant handler.py as comments/handler.py
    participant requests.py as CommentCreateRequest
    participant service.py as CommentService
    participant comment_repo as CommentRepository
    participant article_repo as ArticleRepository
    participant D1

    User->>handler.py: POST /api/comments {article_id, content}
    handler.py->>middleware: get_user(request, env) — must be logged in
    middleware-->>handler.py: user payload

    handler.py->>requests.py: from_body(body)
    Note over requests.py: Validates article_id not empty<br/>content not empty, ≤5000 chars
    requests.py-->>handler.py: CommentCreateRequest

    handler.py->>service.py: create(req, author_id)
    service.py->>helpers: new_id() → cid
    service.py->>comment_repo: insert(cid, article_id, author_id, parent_id, content)
    comment_repo->>D1: INSERT INTO comments (id, article_id, author_id, ...)
    D1-->>comment_repo: ok

    service.py->>article_repo: increment_comments(article_id)
    article_repo->>D1: UPDATE articles SET comments_count = comments_count + 1
    D1-->>article_repo: ok

    service.py->>Logger: event(comment.created, {comment_id, article_id, author_id})
    service.py-->>handler.py: cid

    handler.py-->>User: 201 {id: cid}
```

### 5.2 Reply to Comment

Same as 5.1 but with `parent_id` set. The `CommentCreateRequest` accepts `parent_id` and passes it through. Top-level comments have `parent_id = NULL`.

### 5.3 Edit Comment

**Actor:** Comment's own author
**Business rule:** Author can edit own comments. Content must still be non-empty and ≤5000 chars.

```mermaid
sequenceDiagram
    actor Author
    participant handler.py as comments/handler.py
    participant requests.py as CommentUpdateRequest
    participant service.py as CommentService
    participant repo.py as CommentRepository
    participant D1

    Author->>handler.py: PUT /api/comments/:id {content: updated text}
    handler.py->>middleware: get_user(request, env)
    middleware-->>handler.py: user payload

    handler.py->>requests.py: from_body(body)
    Note over requests.py: Validates content not empty, ≤5000 chars
    requests.py-->>handler.py: CommentUpdateRequest

    handler.py->>service.py: update(comment_id, user_id, req)
    service.py->>repo.py: find_author_id(comment_id)
    repo.py->>D1: SELECT author_id FROM comments WHERE id=?
    D1-->>repo.py: author_id

    service.py->>service.py: owner == requesting_user ✓
    Note over service.py: Only author can edit own comment<br/>SUPERADMIN cannot edit others' comments<br/>(only delete via soft_delete)

    service.py->>repo.py: update(comment_id, content)
    repo.py->>D1: UPDATE comments SET content=?, updated_at=now() WHERE id=?
    D1-->>repo.py: ok

    service.py->>Logger: event(comment.updated, {comment_id})
    service.py-->>handler.py: ok
    handler.py-->>Author: 200 {status: updated}
```

### 5.4 Delete Comment (Soft)

```mermaid
sequenceDiagram
    actor User
    participant handler.py as comments/handler.py
    participant service.py as CommentService
    participant repo.py as CommentRepository
    participant D1

    User->>handler.py: DELETE /api/comments/:id
    handler.py->>service.py: delete(comment_id, user_id, is_superadmin)
    service.py->>repo.py: find_author_id(comment_id)
    D1-->>repo.py: author_id

    alt user is owner OR is_superadmin
        service.py->>repo.py: soft_delete(comment_id)
        repo.py->>D1: UPDATE comments SET is_deleted=1, updated_at=now()
        Note over D1: Content not erased from DB.<br/>CommentDTO.to_dict() returns '[deleted]'<br/>for is_deleted=1 rows.
        service.py->>Logger: event(comment.deleted, {comment_id})
        handler.py-->>User: 200 {deleted: true}
    else
        service.py--xhandler.py: PermissionError
        handler.py-->>User: 403 Forbidden
    end
```

---

## 6. Social Actions

### 6.1 Like Article

```mermaid
sequenceDiagram
    actor User
    participant handler.py as social/handler.py
    participant service.py as SocialService
    participant social_repo as SocialRepository
    participant article_repo as ArticleRepository
    participant D1

    User->>handler.py: POST /api/social/likes/:article_id
    handler.py->>middleware: get_user(request, env) — required
    middleware-->>handler.py: user payload

    handler.py->>service.py: toggle_like(user_id, article_id, add=True)
    service.py->>social_repo: like(user_id, article_id)
    social_repo->>D1: INSERT INTO likes (user_id, article_id) VALUES (?, ?)
    Note over D1: PRIMARY KEY (user_id, article_id)<br/>Duplicate raises exception → caught as 409

    service.py->>article_repo: increment_likes(article_id)
    article_repo->>D1: UPDATE articles SET likes_count = likes_count + 1

    service.py->>Logger: analytics(social.liked, {user_id, article_id})
    service.py-->>handler.py: SocialActionResult{action:like, active:true}
    handler.py-->>User: 200 {action: like, target_id: ..., active: true}
```

### 6.3 Follow Author

```mermaid
sequenceDiagram
    actor Follower
    participant handler.py as social/handler.py
    participant service.py as SocialService
    participant repo.py as SocialRepository
    participant D1

    Follower->>handler.py: POST /api/social/follows/:author_id
    handler.py->>service.py: toggle_follow(follower_id, following_id, add=True)

    service.py->>service.py: follower_id != following_id ✓
    Note over service.py: DB has CHECK (follower_id != following_id)<br/>but we validate before hitting DB

    service.py->>repo.py: follow(follower_id, following_id)
    repo.py->>D1: INSERT INTO follows (follower_id, following_id)
    D1-->>repo.py: ok

    service.py-->>handler.py: SocialActionResult{action:follow, active:true}
    handler.py-->>Follower: 200 {action: follow, active: true}
```

---

## 7. Media

### 7.1 Upload Cover Image

```mermaid
sequenceDiagram
    actor Author
    participant handler.py as media/handler.py
    participant service.py as MediaService
    participant repo.py as MediaRepository
    participant R2 as R2 (env.MEDIA)

    Author->>handler.py: POST /api/media/upload (Content-Type: image/jpeg, body: binary)
    handler.py->>middleware: get_user(request, env)
    middleware-->>handler.py: user payload

    handler.py->>service.py: upload(user_id, request)
    service.py->>request: headers.get(Content-Type)
    service.py->>request: arrayBuffer()
    service.py->>service.py: size = body.byteLength

    service.py->>repo.py: upload(user_id, content_type, body, size)
    repo.py->>repo.py: Validate content_type in ALLOWED_TYPES
    repo.py->>repo.py: Validate size ≤ 5MB
    repo.py->>helpers: new_id() → uuid
    repo.py->>repo.py: key = uploads/{user_id}/{uuid}.jpg

    repo.py->>R2: put(key, body, {contentType})
    R2-->>repo.py: ok

    repo.py-->>service.py: key
    service.py->>service.py: url = https://media.zenos.work/{key}
    service.py->>Logger: event(media.uploaded, {user_id, key, size_bytes})
    service.py-->>handler.py: {url, key}
    handler.py-->>Author: 201 {url: https://media.zenos.work/..., key: ...}

    Note over Author: Author uses url as cover_image_url<br/>in ArticleCreateRequest
```

---

## 8. Admin & Governance

### 8.1 View Platform Stats

**Actor:** SUPERADMIN only

```mermaid
sequenceDiagram
    actor Admin as Admin (SUPERADMIN)
    participant handler.py as admin/handler.py
    participant service.py as AdminService
    participant repo.py as AdminRepository
    participant D1

    Admin->>handler.py: GET /api/admin/stats
    handler.py->>middleware: get_user(request, env)
    handler.py->>handler.py: require_role(user, [SUPERADMIN]) ✓

    handler.py->>service.py: get_stats()

    par Parallel DB queries
        service.py->>repo.py: count_active_users()
        repo.py->>D1: SELECT COUNT(*) FROM users WHERE is_active=1
    and
        service.py->>repo.py: count_active_comments()
        repo.py->>D1: SELECT COUNT(*) FROM comments WHERE is_deleted=0
    and
        service.py->>repo.py: count_articles_by_status()
        repo.py->>D1: SELECT status, COUNT(*) FROM articles GROUP BY status
    and
        service.py->>repo.py: find_top_articles()
        repo.py->>D1: SELECT id, title, views_count, likes_count ... LIMIT 10
    end

    service.py-->>handler.py: {total_users, total_comments, articles_by_status, top_articles}
    handler.py-->>Admin: 200 {stats: {...}}
```

### 8.2 View Approval Queue

**Actor:** APPROVER or SUPERADMIN

```mermaid
sequenceDiagram
    actor Approver
    participant handler.py as admin/handler.py
    participant service.py as AdminService
    participant repo.py as AdminRepository
    participant D1

    Approver->>handler.py: GET /api/admin/queue
    handler.py->>handler.py: require_role(user, CAN_APPROVE) ✓

    handler.py->>service.py: get_approval_queue()
    service.py->>repo.py: find_approval_queue()
    repo.py->>D1: SELECT a.*, u.name AS author_name FROM articles a<br/>JOIN users u WHERE a.status=SUBMITTED ORDER BY updated_at ASC
    D1-->>repo.py: submitted article rows
    repo.py->>Article: from_row(row) for each
    repo.py-->>service.py: [Article, ...]

    service.py->>Article: to_dict(Scope.ADMIN) for each
    Note over service.py: ADMIN scope includes rejection_note,<br/>approved_by for full context
    service.py-->>handler.py: [{article in ADMIN scope}, ...]
    handler.py-->>Approver: 200 {queue: [...]}
```

---

## 9. MVP Coverage

This section maps shipped and planned flows to product milestones, so PM, engineering, and QA can verify that each MVP is functionally represented in API and UI paths.

### 9.1 MVP1: Publishable Knowledge Platform

MVP1 focus: authenticated writing, review workflow, publishing, and readable discovery surfaces.

- Authentication and session lifecycle: sections 1.1 to 1.3
- User onboarding and author enablement: section 2.3
- Draft to publish lifecycle: sections 3.1 to 3.6
- Reader discovery and consumption: sections 4.1 and 4.2
- SR-010 delivered via reader-side heading-derived table of contents
- SR-011 delivered via reader-side success signals:
  - Verification freshness state (`freshly verified`, `aging`, `expired`, or `not set`)
  - Engagement traction signal derived from views, likes, and comments
  - Outcome evidence signal from outcome-tag coverage
- Rich article metadata currently used by frontend:
    - Dynamic content types via `GET /api/articles/content-types`
    - In-page table-of-contents rendering from article headings

### 9.2 MVP2: Trust, Compliance, and Moderation

MVP2 focus: governance controls, safer community features, and editorial reliability.

- Approval operations and queue management: sections 3.3, 3.4, and 8.2
- Comment moderation support and soft deletion: section 5.4
- Role-aware governance functions: section 8.1
- Policy and lifecycle support in data model:
    - Terms acceptance tracking on users
    - Article moderation and verification metadata
    - Notification types for moderation outcomes

### 9.3 MVP3: Discovery and Growth Loops

MVP3 focus: sustained engagement through personalisation, social loops, and operational signals.

- Personalised home feed with preference-aware fallback: section 4.1
- Social actions (likes, follows, bookmarks): section 6
- Notification-driven feedback loops: notifications table and social/comment events
- Platform analytics and top-content visibility: section 8.1
- Superadmin extensibility for content taxonomy:
    - Runtime content-type management through admin API
    - Non-breaking frontend filter/write integration for newly added types

---

## 10. Frontend Use Cases

### 10.1 Frontend Use-Case Diagram

```mermaid
flowchart LR
        reader[Reader]
        author[Author]
        approver[Approver]
        superadmin[Superadmin]

        subgraph frontend[Frontend Web App]
                auth[Authenticate with Google]
                feed[View personalised home feed]
                read[Read article with TOC]
                write[Create or edit draft]
                submit[Submit draft for approval]
                moderate[Approve or reject article]
                search[Search and filter by content type]
                manageTypes[Manage content types]
        end

        reader --> auth
        reader --> feed
        reader --> read
        reader --> search

        author --> write
        author --> submit
        author --> search
        author --> read

        approver --> moderate
        approver --> read

        superadmin --> manageTypes
        superadmin --> moderate
        superadmin --> search
```

### 10.2 Frontend Sequence: Create and Publish Flow

```mermaid
sequenceDiagram
        actor Author
        participant Browser as Browser UI
        participant WritePage as WritePage.tsx
        participant API as api.ts
        participant ArticleAPI as /api/articles
        participant AdminAPI as /api/admin/content-types

        Author->>Browser: Open Write page
        Browser->>WritePage: Mount component
        WritePage->>API: getArticleContentTypes()
        API->>ArticleAPI: GET /api/articles/content-types
        ArticleAPI-->>API: [article, how-to, case-study, ...]
        API-->>WritePage: contentTypeOptions
        WritePage-->>Author: Render dynamic content-type selector

        alt Superadmin adds a new type
                Author->>WritePage: Enter slug/name and click Add
                WritePage->>API: createContentType(slug, name, description)
                API->>AdminAPI: POST /api/admin/content-types
                AdminAPI-->>API: 201 {content_type}
                API-->>WritePage: new content type
                WritePage->>API: getArticleContentTypes()
                API->>ArticleAPI: GET /api/articles/content-types
                ArticleAPI-->>WritePage: refreshed list
        end

        Author->>WritePage: Fill title, content, tags, content_type
        WritePage->>API: createArticle(payload)
        API->>ArticleAPI: POST /api/articles
        ArticleAPI-->>API: 201 {article: DRAFT}
        API-->>WritePage: created article

        Author->>WritePage: Submit for approval
        WritePage->>API: submitArticle(articleId)
        API->>ArticleAPI: POST /api/articles/:id/submit
        ArticleAPI-->>WritePage: 200 {status: SUBMITTED}
        WritePage-->>Author: Show success and transition state
```

---

## Class Responsibility Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer          │ Class               │ Responsibility                        │
├────────────────┼─────────────────────┼───────────────────────────────────────┤
│ HTTP           │ handler.py          │ Route, auth check, call service       │
│                │ middleware/auth.py  │ JWT verify, role check                │
│                │ middleware/logging  │ Request/response logging, trace_id    │
├────────────────┼─────────────────────┼───────────────────────────────────────┤
│ Business       │ service.py          │ Business rules, event logging, no SQL │
│ Logic          │ interface.py        │ Protocol contract for the service     │
├────────────────┼─────────────────────┼───────────────────────────────────────┤
│ Data Access    │ repository.py       │ Execute SQL, map rows to models       │
│                │ queries.py          │ SQL constants only                    │
│                │ db/executor.py      │ D1 binding wrapper (prep/bind/run)    │
│                │ db/repository.py    │ BaseRepository + IRepository Protocol │
├────────────────┼─────────────────────┼───────────────────────────────────────┤
│ Domain Models  │ models/*/model.py   │ Dataclass + scope-aware to_dict()     │
│                │ models/*/requests.py│ Input validation via from_body()      │
│                │ models/common/enums │ String constants (UserRole, Status)   │
│                │ models/common/page  │ PaginatedResponse wrapper             │
├────────────────┼─────────────────────┼───────────────────────────────────────┤
│ Logging        │ utils/logger.py     │ Structured JSON logs, all event types │
│                │ utils/loki.py       │ Loki/Grafana forwarder                │
│                │ utils/elk.py        │ Elasticsearch forwarder               │
│                │ utils/forwarder.py  │ Factory: ELK > Loki > stdout          │
│                │ utils/context.py    │ RequestContext: trace_id + Logger     │
└────────────────┴─────────────────────┴───────────────────────────────────────┘
```

---

## Status Transition Rules

```
DRAFT ──────────────→ SUBMITTED  (author submits)
REJECTED ───────────→ SUBMITTED  (author resubmits after edits)
SUBMITTED ──────────→ APPROVED   (approver approves)
SUBMITTED ──────────→ REJECTED   (approver rejects + note required)
APPROVED ───────────→ PUBLISHED  (approver publishes)
PUBLISHED ──────────→ ARCHIVED   (author or approver archives)
ARCHIVED ─── (terminal, no further transitions defined)

Editable states: DRAFT, REJECTED
```
