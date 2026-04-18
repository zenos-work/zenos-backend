"""Phase 11 Step 43 — Row-Level Security middleware.

Provides tenant-scoped query helpers that automatically append
`WHERE org_id = ?` to prevent cross-tenant data leaks.
"""

# Tables that are org-scoped and require RLS filtering
ORG_SCOPED_TABLES = frozenset(
    {
        "articles",
        "comments",
        "workflows",
        "workflow_runs",
        "workflow_node_cost_rates",
        "workflow_run_costs",
        "connectors",
        "connector_instances",
        "connector_logs",
        "leads",
        "lead_scores",
        "campaigns",
        "campaign_messages",
        "newsletters",
        "newsletter_subscribers",
        "newsletter_issues",
        "courses",
        "course_modules",
        "course_lessons",
        "course_quizzes",
        "course_enrollments",
        "course_certificates",
        "community_spaces",
        "community_posts",
        "community_post_replies",
        "marketplace_listings",
        "marketplace_reviews",
        "podcast_shows",
        "podcast_episodes",
        "audit_log",
        "api_keys",
        "sso_configs",
        "org_add_on_subscriptions",
        "org_members",
        "org_teams",
        "subdomain_configs",
        "vault_secrets",
        "notification_preferences",
        "push_subscriptions",
        "analytics_events",
        "org_metering_daily",
        "org_metering_monthly",
    }
)

# Tables that are public / platform-wide — no org scoping
PUBLIC_TABLES = frozenset(
    {
        "tags",
        "content_types",
        "membership_plans",
        "add_on_packages",
        "feature_flags",
        "platform_metering_daily",
        "ranking_weights",
    }
)


class RlsContext:
    """Request-scoped row-level security context."""

    def __init__(self, org_id: str, user_role: str = ""):
        self.org_id = org_id
        self.user_role = user_role
        self.is_superadmin = user_role == "SUPERADMIN"

    def scoped_query(self, base_sql: str, existing_params: list | tuple = ()):
        """Append org_id scoping to a query.

        If the user is SUPERADMIN, the query is returned unmodified.

        Returns (sql, params) tuple.
        """
        if self.is_superadmin:
            return base_sql, list(existing_params)

        params = list(existing_params)
        upper = base_sql.upper().strip()

        if "WHERE" in upper:
            sql = base_sql + " AND org_id = ?"
        else:
            sql = base_sql + " WHERE org_id = ?"
        params.append(self.org_id)
        return sql, params

    def enforce(self, resource_org_id: str):
        """Raise if the resource belongs to a different org.

        SUPERADMIN bypasses this check.
        """
        if self.is_superadmin:
            return
        if resource_org_id != self.org_id:
            raise PermissionError("Cross-tenant access denied")


def resolve_rls(user: dict, request=None) -> RlsContext | None:
    """Build RlsContext from authenticated user + request headers.

    The active org is determined by:
    1. X-Org-Id header (explicit)
    2. user's default_org_id claim
    If neither is present, returns None (no org scoping).
    """
    if not user:
        return None

    org_id = ""
    if request:
        org_id = request.headers.get("X-Org-Id", "")

    if not org_id:
        org_id = user.get("org_id", "")

    if not org_id:
        return None

    return RlsContext(
        org_id=org_id,
        user_role=user.get("role", ""),
    )
