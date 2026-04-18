"""Phase 9 Step 32 — Community queries."""

# ── Spaces ───────────────────────────────────────────────────
LIST_SPACES = "SELECT * FROM community_spaces WHERE org_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
LIST_SPACES_PUBLIC = "SELECT * FROM community_spaces WHERE space_type != 'secret' ORDER BY member_count DESC LIMIT ? OFFSET ?"
GET_SPACE = "SELECT * FROM community_spaces WHERE id = ?"
GET_SPACE_BY_SLUG = "SELECT * FROM community_spaces WHERE slug = ?"
INSERT_SPACE = """INSERT INTO community_spaces
    (id, org_id, name, slug, description, cover_image_url, icon,
     space_type, membership_tier, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_SPACE = """UPDATE community_spaces SET
    name=?, description=?, cover_image_url=?, icon=?,
    space_type=?, membership_tier=?,
    updated_at=datetime('now') WHERE id=?"""
DELETE_SPACE = "DELETE FROM community_spaces WHERE id = ?"
INCREMENT_MEMBER_COUNT = (
    "UPDATE community_spaces SET member_count = member_count + 1 WHERE id = ?"
)
DECREMENT_MEMBER_COUNT = (
    "UPDATE community_spaces SET member_count = MAX(0, member_count - 1) WHERE id = ?"
)
INCREMENT_POST_COUNT = (
    "UPDATE community_spaces SET post_count = post_count + 1 WHERE id = ?"
)
DECREMENT_POST_COUNT = (
    "UPDATE community_spaces SET post_count = MAX(0, post_count - 1) WHERE id = ?"
)

# ── Members ──────────────────────────────────────────────────
LIST_MEMBERS = "SELECT * FROM space_members WHERE space_id = ? ORDER BY joined_at DESC LIMIT ? OFFSET ?"
GET_MEMBER = "SELECT * FROM space_members WHERE space_id = ? AND user_id = ?"
INSERT_MEMBER = "INSERT INTO space_members (space_id, user_id, role) VALUES (?, ?, ?)"
UPDATE_MEMBER_ROLE = (
    "UPDATE space_members SET role = ? WHERE space_id = ? AND user_id = ?"
)
DELETE_MEMBER = "DELETE FROM space_members WHERE space_id = ? AND user_id = ?"

# ── Posts ────────────────────────────────────────────────────
LIST_POSTS = "SELECT * FROM community_posts WHERE space_id = ? AND status = 'published' ORDER BY pinned DESC, created_at DESC LIMIT ? OFFSET ?"
LIST_REPLIES = "SELECT * FROM community_posts WHERE parent_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?"
GET_POST = "SELECT * FROM community_posts WHERE id = ?"
INSERT_POST = """INSERT INTO community_posts
    (id, space_id, author_id, parent_id, title, body, post_type, article_id, status, pinned)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
UPDATE_POST = """UPDATE community_posts SET
    title=?, body=?, post_type=?, status=?, pinned=?,
    updated_at=datetime('now') WHERE id=?"""
DELETE_POST = "DELETE FROM community_posts WHERE id = ?"
INCREMENT_REPLY_COUNT = (
    "UPDATE community_posts SET reply_count = reply_count + 1 WHERE id = ?"
)
INCREMENT_LIKE_COUNT = (
    "UPDATE community_posts SET like_count = like_count + 1 WHERE id = ?"
)
