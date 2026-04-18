# ── Organizations ───────────────────────────────────────────────────────────
INSERT_ORG = (
    "INSERT INTO organizations"
    " (id, name, slug, description, created_by, settings)"
    " VALUES (?, ?, ?, NULLIF(?, ''), ?, '{}')"
)

SELECT_ORG_BY_ID = "SELECT * FROM organizations WHERE id = ?"

SELECT_ORG_BY_SLUG = "SELECT * FROM organizations WHERE slug = ?"

SELECT_ORGS_BY_USER = (
    "SELECT o.* FROM organizations o"
    " JOIN org_members m ON m.org_id = o.id"
    " WHERE m.user_id = ?"
    " ORDER BY o.created_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_ORGS_BY_USER = "SELECT COUNT(*) AS c FROM org_members WHERE user_id = ?"

UPDATE_ORG = (
    "UPDATE organizations"
    " SET name = ?, description = NULLIF(?, ''), logo_url = NULLIF(?, ''),"
    " website = NULLIF(?, ''), updated_at = datetime('now')"
    " WHERE id = ?"
)

# ── Org Members ────────────────────────────────────────────────────────────
INSERT_MEMBER = (
    "INSERT INTO org_members (id, org_id, user_id, org_role, invited_by)"
    " VALUES (?, ?, ?, ?, NULLIF(?, ''))"
)

SELECT_MEMBERS = (
    "SELECT * FROM org_members WHERE org_id = ? ORDER BY joined_at ASC LIMIT ? OFFSET ?"
)

COUNT_MEMBERS = "SELECT COUNT(*) AS c FROM org_members WHERE org_id = ?"

SELECT_MEMBER = "SELECT * FROM org_members WHERE org_id = ? AND user_id = ?"

UPDATE_MEMBER_ROLE = (
    "UPDATE org_members SET org_role = ? WHERE org_id = ? AND user_id = ?"
)

DELETE_MEMBER = "DELETE FROM org_members WHERE org_id = ? AND user_id = ?"

# ── Teams ──────────────────────────────────────────────────────────────────
INSERT_TEAM = (
    "INSERT INTO teams (id, org_id, name, description, created_by)"
    " VALUES (?, ?, ?, NULLIF(?, ''), ?)"
)

SELECT_TEAMS = "SELECT * FROM teams WHERE org_id = ? ORDER BY name ASC LIMIT ? OFFSET ?"

COUNT_TEAMS = "SELECT COUNT(*) AS c FROM teams WHERE org_id = ?"

INSERT_TEAM_MEMBER = (
    "INSERT OR IGNORE INTO team_members (team_id, user_id) VALUES (?, ?)"
)

DELETE_TEAM_MEMBER = "DELETE FROM team_members WHERE team_id = ? AND user_id = ?"

SELECT_TEAM_MEMBERS = (
    "SELECT * FROM team_members WHERE team_id = ? ORDER BY added_at ASC"
)

# ── Invitations ────────────────────────────────────────────────────────────
INSERT_INVITATION = (
    "INSERT INTO org_invitations"
    " (id, org_id, email, org_role, token, invited_by, expires_at)"
    " VALUES (?, ?, ?, ?, ?, ?, ?)"
)

SELECT_INVITATION_BY_TOKEN = (
    "SELECT * FROM org_invitations WHERE token = ? AND status = 'pending'"
)

SELECT_INVITATIONS_BY_ORG = (
    "SELECT * FROM org_invitations WHERE org_id = ?"
    " ORDER BY created_at DESC"
    " LIMIT ? OFFSET ?"
)

COUNT_INVITATIONS_BY_ORG = "SELECT COUNT(*) AS c FROM org_invitations WHERE org_id = ?"

ACCEPT_INVITATION = (
    "UPDATE org_invitations"
    " SET status = 'accepted', accepted_at = datetime('now')"
    " WHERE id = ? AND status = 'pending'"
)

DELETE_INVITATION = "DELETE FROM org_invitations WHERE id = ? AND org_id = ?"
