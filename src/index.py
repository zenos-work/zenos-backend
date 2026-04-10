from workers import WorkerEntrypoint
from urllib.parse import urlparse, parse_qs
from middleware.logging import with_logging
from utils.helpers import json_resp, cors_headers
from auth.router import handle_auth

# Import all API handlers (add as you build each module)
from api.articles.handler import handle_articles
from api.users.handler import handle_users
from api.tags.handler import handle_tags
from api.comments.handler import handle_comments
from api.social.handler import handle_social
from api.feed.handler import handle_feed
from api.media.handler import handle_media
from api.series.handler import handle_series
from api.membership.handler import handle_membership
from api.admin.handler import handle_admin
from api.search.handler import handle_search
from api.analytics.service import AnalyticsService
from api.sessions.handler import handle_sessions
from api.blocks.handler import handle_blocks
from api.revisions.handler import handle_revisions
from api.reports.handler import handle_reports
from api.earnings.handler import handle_earnings
from api.domains.handler import handle_domains
from api.reading_lists.handler import handle_reading_lists
from api.organizations.handler import handle_organizations, handle_invitation_accept
from api.add_ons.handler import handle_add_ons
from api.org_infra.handler import handle_org_infra
from api.feature_flags.handler import handle_feature_flags
from api.workflows.handler import handle_workflows, handle_webhook_trigger
from api.connectors.handler import handle_connectors
from api.marketing.handler import handle_marketing
from api.leads.handler import handle_leads
from api.analytics.handler import handle_analytics
from api.newsletters.handler import handle_newsletters
from api.publications.handler import handle_publications
from api.courses.handler import handle_courses
from api.community.handler import handle_community
from api.marketplace.handler import handle_marketplace
from api.referrals.handler import handle_referrals
from api.podcasts.handler import handle_podcasts
from api.notification_prefs.handler import handle_notification_prefs
from api.workflow_costs.handler import handle_workflow_costs
from api.usage_alerts.handler import handle_usage_alerts
from api.subdomains.handler import handle_subdomains
from api.sso.handler import handle_sso
from api.vault.handler import handle_vault
from api.billing.handler import handle_billing
from api.compliance.handler import handle_compliance

from js import Response


class Default(WorkerEntrypoint):
    async def on_fetch(self, request):
        return await with_logging(request, self.env, self._dispatch)

    async def scheduled(self, _controller, env, _ctx):
        service = AnalyticsService(env or self.env)
        try:
            result = await service.aggregate_previous_hour()
            print(f"[sr011] hourly aggregation complete: {result}")
        except Exception as exc:
            print(f"[sr011] hourly aggregation failed: {exc}")
            raise

    async def _dispatch(self, ctx):
        """Pure routing — no business logic here."""
        request = ctx.request
        env = ctx.env
        url = urlparse(request.url)
        path = url.path
        method = request.method
        query = parse_qs(url.query)

        if method == "OPTIONS":
            return Response.new(
                None,
                status=204,
                headers=cors_headers(
                    env=env,
                    request=request,
                    content_type=None,
                    allow_credentials=True,
                ),
            )

        if path == "/health":
            return json_resp(
                {
                    "status": "ok",
                    "service": "zenos-api",
                    "env": env.ENVIRONMENT,
                    "trace_id": ctx.trace_id,
                },
                env=env,
                request=request,
            )

        if path.startswith("/auth/"):
            return await handle_auth(request, env, path)

        if path.startswith("/api/articles") and "/revisions" in path:
            return await handle_revisions(request, env, path, method, query, ctx)
        if path.startswith("/api/articles"):
            return await handle_articles(request, env, path, method, query, ctx)
        if path.startswith("/api/users/me/sessions"):
            return await handle_sessions(request, env, path, method, query, ctx)
        if path.startswith("/api/users/me/data-export"):
            return await handle_compliance(request, env, path, method, query, ctx)
        if path.startswith("/api/users/me/erase"):
            return await handle_compliance(request, env, path, method, query, ctx)
        if path.startswith("/api/users/me/blocks") or path.startswith(
            "/api/users/me/mutes"
        ):
            return await handle_blocks(request, env, path, method, query, ctx)
        if path.startswith("/api/users"):
            return await handle_users(request, env, path, method, query, ctx)
        if path.startswith("/api/tags"):
            return await handle_tags(request, env, path, method, query, ctx)
        if path.startswith("/api/comments"):
            return await handle_comments(request, env, path, method, query, ctx)
        if path.startswith("/api/social"):
            return await handle_social(request, env, path, method, query, ctx)
        if path.startswith("/api/feed"):
            return await handle_feed(request, env, path, method, query, ctx)
        if path.startswith("/api/media"):
            return await handle_media(request, env, path, method, query, ctx)
        if path.startswith("/api/series"):
            return await handle_series(request, env, path, method, query, ctx)
        if path.startswith("/api/membership"):
            return await handle_membership(request, env, path, method, query, ctx)
        if path.startswith("/api/admin/earnings"):
            return await handle_earnings(request, env, path, method, query, ctx)
        if path.startswith("/api/admin/reports"):
            return await handle_reports(request, env, path, method, query, ctx)
        if path.startswith("/api/admin/feature-flags"):
            return await handle_feature_flags(request, env, path, method, query, ctx)
        if path.startswith("/api/admin"):
            return await handle_admin(request, env, path, method, query, ctx)

        if path.startswith("/api/search"):
            return await handle_search(request, env, path, method, query, ctx)
        if path.startswith("/api/reports"):
            return await handle_reports(request, env, path, method, query, ctx)
        if path.startswith("/api/earnings"):
            return await handle_earnings(request, env, path, method, query, ctx)
        if path.startswith("/api/tips"):
            return await handle_earnings(request, env, path, method, query, ctx)
        if path.startswith("/api/domains"):
            return await handle_domains(request, env, path, method, query, ctx)
        if path.startswith("/api/reading-lists"):
            return await handle_reading_lists(request, env, path, method, query, ctx)
        if path.startswith("/api/features"):
            return await handle_feature_flags(request, env, path, method, query, ctx)

        # Phase 4: Workflow sub-resources (must come before /api/workflows)
        if path.startswith("/api/workflow-node-types"):
            return await handle_workflows(request, env, path, method, query, ctx)
        if path.startswith("/api/workflow-templates"):
            return await handle_workflows(request, env, path, method, query, ctx)
        if path.startswith("/api/workflow-tasks"):
            return await handle_workflows(request, env, path, method, query, ctx)
        if path.startswith("/api/workflow-approvals"):
            return await handle_workflows(request, env, path, method, query, ctx)
        if path.startswith("/api/webhooks/workflow/"):
            return await handle_webhook_trigger(request, env, path, method, query, ctx)
        if path.startswith("/api/workflows"):
            return await handle_workflows(request, env, path, method, query, ctx)

        # Phase 5: Connectors & Digital Marketing
        if path.startswith("/api/connector-marketplace"):
            return await handle_connectors(request, env, path, method, query, ctx)
        if path.startswith("/api/connectors"):
            return await handle_connectors(request, env, path, method, query, ctx)
        if path.startswith("/api/marketing"):
            return await handle_marketing(request, env, path, method, query, ctx)
        if path.startswith("/api/leads"):
            return await handle_leads(request, env, path, method, query, ctx)

        # Phase 6: Analytics, Metering & Dashboards
        if path.startswith("/api/analytics"):
            return await handle_analytics(request, env, path, method, query, ctx)

        # Phase 7: Newsletters & Publications
        if path.startswith("/api/newsletters"):
            return await handle_newsletters(request, env, path, method, query, ctx)
        if path.startswith("/api/publications"):
            return await handle_publications(request, env, path, method, query, ctx)

        # Phase 8: Courses & Learning Paths
        if path.startswith("/api/courses"):
            return await handle_courses(request, env, path, method, query, ctx)

        # Phase 9: Community, Marketplace & Growth
        if path.startswith("/api/community"):
            return await handle_community(request, env, path, method, query, ctx)
        if path.startswith("/api/marketplace"):
            return await handle_marketplace(request, env, path, method, query, ctx)
        if path.startswith("/api/referrals"):
            return await handle_referrals(request, env, path, method, query, ctx)
        if path.startswith("/api/podcasts"):
            return await handle_podcasts(request, env, path, method, query, ctx)

        # Phase 10: Notification Expansion & System Hardening
        if path.startswith("/api/notification-prefs"):
            return await handle_notification_prefs(
                request, env, path, method, query, ctx
            )
        if path.startswith("/api/workflow-costs"):
            return await handle_workflow_costs(request, env, path, method, query, ctx)
        if path.startswith("/api/usage"):
            return await handle_usage_alerts(request, env, path, method, query, ctx)

        # Phase 11: Enterprise Infrastructure & Tenant Isolation
        if path.startswith("/.well-known/org-info"):
            return await handle_subdomains(request, env, path, method, query, ctx)
        if path.startswith("/api/admin/subdomains"):
            return await handle_subdomains(request, env, path, method, query, ctx)
        if path.startswith("/api/admin/organizations/") and path.endswith("/subdomain"):
            return await handle_subdomains(request, env, path, method, query, ctx)
        if path.startswith("/api/organizations/") and path.endswith("/subdomain"):
            return await handle_subdomains(request, env, path, method, query, ctx)

        if path.startswith("/api/auth/sso/"):
            return await handle_sso(request, env, path, method, query, ctx)
        if path.startswith("/api/organizations/") and "/sso/configs" in path:
            return await handle_sso(request, env, path, method, query, ctx)

        if path.startswith("/api/organizations/") and "/vault/secrets" in path:
            return await handle_vault(request, env, path, method, query, ctx)

        # Phase 12: Financial Engine & Compliance
        if path.startswith("/api/billing/webhooks/stripe"):
            return await handle_billing(request, env, path, method, query, ctx)
        if path.startswith("/api/admin/billing"):
            return await handle_billing(request, env, path, method, query, ctx)
        if path.startswith("/api/admin/compliance"):
            return await handle_compliance(request, env, path, method, query, ctx)

        # Phase 3: Invitation accept (before /api/organizations)
        if path.startswith("/api/invitations/"):
            return await handle_invitation_accept(
                request, env, path, method, query, ctx
            )

        # Phase 3: Org infra sub-routes (before general /api/organizations)
        if path.startswith("/api/organizations/") and (
            "/audit-log" in path or "/api-keys" in path or "/sso" in path
        ):
            return await handle_org_infra(request, env, path, method, query, ctx)

        # Phase 3: Org add-ons — admin routes
        if path.startswith("/api/admin/organizations/") and "/add-ons" in path:
            return await handle_add_ons(request, env, path, method, query, ctx)
        if path.startswith("/api/admin/add-ons"):
            return await handle_add_ons(request, env, path, method, query, ctx)

        # Phase 3: Org add-ons — org routes
        if path.startswith("/api/organizations/") and "/add-ons" in path:
            return await handle_add_ons(request, env, path, method, query, ctx)

        # Phase 3: Organizations CRUD + members + teams + invitations
        if path.startswith("/api/organizations"):
            return await handle_organizations(request, env, path, method, query, ctx)

        return json_resp({"error": "Not found"}, 404, env=env, request=request)
