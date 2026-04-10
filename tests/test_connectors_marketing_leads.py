"""Tests for Phase 5 — Connectors, Marketing & Leads (model + handler)."""

import asyncio
import importlib
import json
import sys
import types
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "js" not in sys.modules:
    js_stub = types.ModuleType("js")

    class _Headers:
        @staticmethod
        def new(values=None, **_kwargs):
            return (
                dict(values)
                if isinstance(values, dict)
                else ({} if values is None else {k: v for k, v in values})
            )

    class _Resp:
        def __init__(self, body=None, status=200, headers=None):
            self.status_code = status
            self.headers = headers or {}
            self._body = body

        def json(self):
            if self._body is None or self._body == "":
                return None
            if isinstance(self._body, (dict, list)):
                return self._body
            return json.loads(self._body)

    class _Response:
        @staticmethod
        def new(body=None, status=200, headers=None):
            return _Resp(body=body, status=status, headers=headers)

    js_stub.Headers = _Headers
    js_stub.Response = _Response
    sys.modules["js"] = js_stub

# ── Model imports ───────────────────────────────────────────
conn_models = importlib.import_module("models.connector.model")
ConnectorDefinition = conn_models.ConnectorDefinition
ConnectorAction = conn_models.ConnectorAction
ConnectorInstance = conn_models.ConnectorInstance
McpServer = conn_models.McpServer
CustomAgent = conn_models.CustomAgent
ConnectorMarketplaceListing = conn_models.ConnectorMarketplaceListing

mkt_models = importlib.import_module("models.marketing.model")
DistributionChannel = mkt_models.DistributionChannel
ScheduledPublication = mkt_models.ScheduledPublication
ContentDistributionJob = mkt_models.ContentDistributionJob
ContentSyndication = mkt_models.ContentSyndication
RssFeed = mkt_models.RssFeed
ContentRepurposingJob = mkt_models.ContentRepurposingJob
Campaign = mkt_models.Campaign

lead_models = importlib.import_module("models.lead.model")
LeadCaptureForm = lead_models.LeadCaptureForm
Lead = lead_models.Lead
LeadEvent = lead_models.LeadEvent
LeadScoreRule = lead_models.LeadScoreRule
LeadPipeline = lead_models.LeadPipeline
PipelineStage = lead_models.PipelineStage
LeadPipelineEntry = lead_models.LeadPipelineEntry
EmailSequence = lead_models.EmailSequence
EmailSequenceStep = lead_models.EmailSequenceStep
LeadSequenceEnrollment = lead_models.LeadSequenceEnrollment

# ── Handler imports ─────────────────────────────────────────
conn_handler = importlib.import_module("api.connectors.handler")
mkt_handler = importlib.import_module("api.marketing.handler")
lead_handler = importlib.import_module("api.leads.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Connector Model Tests
# ═══════════════════════════════════════════════════════════════
class TestConnectorModels:
    def test_connector_definition_from_row(self):
        row = {
            "id": "cd1",
            "name": "Slack",
            "slug": "slack",
            "description": "",
            "logo_url": "",
            "documentation_url": "",
            "source_type": "builtin",
            "auth_method": "oauth2",
            "auth_config_schema": "{}",
            "instance_config_schema": "{}",
            "category": "messaging",
            "is_active": 1,
            "is_verified": 0,
            "is_enterprise": 0,
            "version": "1.0.0",
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        d = ConnectorDefinition.from_row(row)
        assert d.id == "cd1"
        assert d.slug == "slack"
        assert d.is_active is True
        assert d.auth_config_schema == {}

    def test_connector_definition_from_row_none(self):
        assert ConnectorDefinition.from_row(None) is None

    def test_connector_definition_public_scope(self):
        d = ConnectorDefinition(
            id="cd1",
            name="Slack",
            slug="slack",
            source_type="builtin",
            auth_method="oauth2",
            category="messaging",
            is_active=True,
            is_verified=False,
            is_enterprise=False,
            version="1.0.0",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        pub = d.to_dict()
        assert "id" in pub
        assert "auth_config_schema" not in pub  # admin only

    def test_connector_definition_admin_scope(self):
        d = ConnectorDefinition(
            id="cd1",
            name="Slack",
            slug="slack",
            source_type="builtin",
            auth_method="oauth2",
            category="messaging",
            is_active=True,
            is_verified=False,
            is_enterprise=False,
            version="1.0.0",
            auth_config_schema={"token": "str"},
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        adm = d.to_dict(scope="admin")
        assert "auth_config_schema" in adm

    def test_connector_action_from_row(self):
        row = {
            "id": "ca1",
            "connector_definition_id": "cd1",
            "action_key": "send_message",
            "name": "Send Message",
            "description": "",
            "category": "messaging",
            "node_category": "action",
            "input_schema": "{}",
            "output_schema": "{}",
            "cost_model": "per_execution",
            "rate_microcents": 0,
            "unit_label": None,
            "requires_enterprise": 0,
            "is_active": 1,
            "sort_order": 0,
        }
        a = ConnectorAction.from_row(row)
        assert a.action_key == "send_message"
        assert a.is_active is True

    def test_connector_instance_from_row(self):
        row = {
            "id": "ci1",
            "org_id": "org1",
            "connector_definition_id": "cd1",
            "name": "My Slack",
            "auth_method": "oauth2",
            "kv_secret_key": "secret",
            "instance_config": "{}",
            "status": "active",
            "last_health_check": None,
            "health_status": "unknown",
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        i = ConnectorInstance.from_row(row)
        assert i.status == "active"
        assert i.instance_config == {}

    def test_mcp_server_from_row(self):
        row = {
            "id": "mcp1",
            "org_id": "org1",
            "name": "MCP 1",
            "description": "",
            "transport": "sse",
            "endpoint_url": "https://mcp.example.com",
            "command": None,
            "args": "[]",
            "auth_method": "bearer",
            "kv_secret_key": "",
            "tools_schema": "[]",
            "resources_schema": "[]",
            "status": "active",
            "last_health_check": None,
            "health_status": "unknown",
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        s = McpServer.from_row(row)
        assert s.transport == "sse"
        assert s.tools_schema == []

    def test_custom_agent_from_row(self):
        row = {
            "id": "ag1",
            "org_id": "org1",
            "name": "Bot",
            "description": "",
            "agent_type": "llm_chain",
            "model_provider": "openai",
            "model_id": "gpt-4",
            "model_config": '{"temp":0.7}',
            "system_prompt": "help",
            "tool_connector_action_ids": '["t1"]',
            "mcp_server_id": None,
            "endpoint_url": None,
            "is_active": 1,
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        a = CustomAgent.from_row(row)
        assert a.agent_type == "llm_chain"
        assert a.tool_connector_action_ids == ["t1"]
        assert a.model_config_data == {"temp": 0.7}

    def test_marketplace_listing_from_row(self):
        row = {
            "id": "ml1",
            "connector_definition_id": "cd1",
            "publisher_org_id": "org1",
            "publisher_user_id": "u1",
            "listing_title": "Slack",
            "short_description": "Short",
            "long_description": "Long",
            "tags": '["messaging"]',
            "screenshot_urls": "[]",
            "install_count": 100,
            "star_count": 5,
            "is_public": 1,
            "created_at": "2026-01-01",
        }
        listing = ConnectorMarketplaceListing.from_row(row)
        assert listing.listing_title == "Slack"
        assert listing.tags == ["messaging"]


# ═══════════════════════════════════════════════════════════════
# Marketing Model Tests
# ═══════════════════════════════════════════════════════════════
class TestMarketingModels:
    def test_distribution_channel_from_row(self):
        row = {
            "id": "dc1",
            "org_id": "org1",
            "name": "Twitter",
            "channel_type": "twitter",
            "config": '{"api_key":"x"}',
            "kv_secret_key": "s",
            "is_active": 1,
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        c = DistributionChannel.from_row(row)
        assert c.channel_type == "twitter"
        assert c.config == {"api_key": "x"}
        assert c.is_active is True

    def test_distribution_channel_from_row_none(self):
        assert DistributionChannel.from_row(None) is None

    def test_scheduled_publication_from_row(self):
        row = {
            "id": "sp1",
            "article_id": "a1",
            "scheduled_by": "u1",
            "scheduled_at": "2026-03-01T12:00:00Z",
            "timezone": "UTC",
            "status": "pending",
            "published_at": None,
            "error_message": None,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        s = ScheduledPublication.from_row(row)
        assert s.status == "pending"

    def test_content_distribution_job_from_row(self):
        row = {
            "id": "dj1",
            "org_id": "org1",
            "article_id": "a1",
            "channel_id": "dc1",
            "status": "queued",
            "distribute_at": "2026-03-01",
            "external_id": None,
            "external_url": None,
            "error_message": None,
            "retry_count": 0,
            "run_id": "",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        j = ContentDistributionJob.from_row(row)
        assert j.status == "queued"

    def test_content_syndication_from_row(self):
        row = {
            "id": "cs1",
            "article_id": "a1",
            "platform": "dev.to",
            "external_url": "https://dev.to/x",
            "canonical_back_link": 1,
            "syndicated_at": "2026-01-01",
            "created_at": "2026-01-01",
        }
        s = ContentSyndication.from_row(row)
        assert s.platform == "dev.to"
        assert s.canonical_back_link is True

    def test_rss_feed_from_row(self):
        row = {
            "id": "rf1",
            "org_id": "org1",
            "name": "Main Feed",
            "slug": "main",
            "description": "",
            "filter_tags": '["python"]',
            "filter_authors": "[]",
            "max_items": 50,
            "include_premium": 0,
            "is_active": 1,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        f = RssFeed.from_row(row)
        assert f.filter_tags == ["python"]
        assert f.include_premium is False

    def test_repurposing_job_from_row(self):
        row = {
            "id": "rj1",
            "org_id": "org1",
            "article_id": "a1",
            "format": "twitter_thread",
            "status": "pending",
            "input_options": "{}",
            "output_content": None,
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        r = ContentRepurposingJob.from_row(row)
        assert r.format == "twitter_thread"

    def test_campaign_from_row(self):
        row = {
            "id": "c1",
            "org_id": "org1",
            "name": "Launch",
            "description": "",
            "type": "content",
            "status": "draft",
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
            "budget_cents": 10000,
            "goal_id": "g1",
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "revenue_cents": 0,
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        c = Campaign.from_row(row)
        assert c.name == "Launch"
        assert c.budget_cents == 10000


# ═══════════════════════════════════════════════════════════════
# Lead Model Tests
# ═══════════════════════════════════════════════════════════════
class TestLeadModels:
    def test_lead_capture_form_from_row(self):
        row = {
            "id": "f1",
            "org_id": "org1",
            "owner_id": "u1",
            "name": "Newsletter",
            "slug": "newsletter",
            "description": "",
            "placement": "inline",
            "fields_schema": '[{"name":"email"}]',
            "submit_button_text": "Subscribe",
            "success_message": "Thanks!",
            "redirect_url": "",
            "tags_on_submit": '["subscriber"]',
            "workflow_id": "",
            "submission_count": 0,
            "is_active": 1,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        f = LeadCaptureForm.from_row(row)
        assert f.name == "Newsletter"
        assert f.fields_schema == [{"name": "email"}]
        assert f.tags_on_submit == ["subscriber"]

    def test_lead_from_row(self):
        row = {
            "id": "l1",
            "org_id": "org1",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "company": "",
            "job_title": "",
            "phone": "",
            "source": "form",
            "source_detail": "",
            "utm_source": "",
            "utm_medium": "",
            "utm_campaign": "",
            "utm_content": "",
            "utm_term": "",
            "referrer_url": "",
            "landing_page": "",
            "capture_form_id": "",
            "ip_address": "",
            "user_agent": "",
            "custom_fields": "{}",
            "score": 0,
            "status": "new",
            "consent_email": 0,
            "consent_tracking": 0,
            "consent_at": "",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        lead = Lead.from_row(row)
        assert lead.email == "test@example.com"
        assert lead.custom_fields == {}
        assert lead.source == "form"

    def test_lead_from_row_none(self):
        assert Lead.from_row(None) is None

    def test_lead_public_scope(self):
        lead = Lead(id="l1", org_id="org1", email="t@t.com")
        pub = lead.to_dict()
        assert "email" in pub
        # ip_address should only appear in admin scope
        assert "ip_address" not in pub

    def test_lead_admin_scope(self):
        lead = Lead(id="l1", org_id="org1", email="t@t.com", ip_address="1.2.3.4")
        adm = lead.to_dict(scope="admin")
        assert adm["ip_address"] == "1.2.3.4"

    def test_lead_score_rule_from_row(self):
        row = {
            "id": "sr1",
            "org_id": "org1",
            "name": "Open Email",
            "trigger_event": "email_open",
            "condition": '{"min":1}',
            "score_delta": 5,
            "is_active": 1,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        r = LeadScoreRule.from_row(row)
        assert r.score_delta == 5
        assert r.condition == {"min": 1}

    def test_pipeline_stage_from_row(self):
        row = {
            "id": "ps1",
            "pipeline_id": "p1",
            "name": "New",
            "sort_order": 0,
            "stage_type": "open",
            "color": "#fff",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        s = PipelineStage.from_row(row)
        assert s.name == "New"
        assert s.stage_type == "open"

    def test_email_sequence_from_row(self):
        row = {
            "id": "es1",
            "org_id": "org1",
            "name": "Welcome",
            "description": "",
            "trigger_type": "form_submit",
            "status": "active",
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        s = EmailSequence.from_row(row)
        assert s.trigger_type == "form_submit"

    def test_email_sequence_step_from_row(self):
        row = {
            "id": "ess1",
            "sequence_id": "es1",
            "step_number": 1,
            "delay_days": 1,
            "subject": "Welcome!",
            "body_html": "<p>Hi</p>",
            "body_text": "Hi",
            "created_at": "2026-01-01",
        }
        s = EmailSequenceStep.from_row(row)
        assert s.step_number == 1
        assert s.subject == "Welcome!"

    def test_lead_sequence_enrollment_from_row(self):
        row = {
            "id": "lse1",
            "lead_id": "l1",
            "sequence_id": "es1",
            "current_step": 1,
            "status": "active",
            "enrolled_at": "2026-01-01",
            "last_step_sent_at": None,
            "completed_at": None,
            "created_at": "2026-01-01",
        }
        e = LeadSequenceEnrollment.from_row(row)
        assert e.current_step == 1
        assert e.status == "active"


# ═══════════════════════════════════════════════════════════════
# Fake Services
# ═══════════════════════════════════════════════════════════════
class FakeConnectorService:
    def __init__(self, env, ctx=None):
        self.calls = []

    # Catalogue
    async def list_definitions(self, category=None):
        self.calls.append(("list_definitions", category))
        return [{"id": "cd1", "slug": "slack"}]

    async def get_definition(self, def_id):
        self.calls.append(("get_definition", def_id))
        if def_id == "missing":
            raise ValueError("Not found")
        return {"id": def_id, "name": "Slack"}

    async def get_definition_by_slug(self, slug):
        self.calls.append(("get_definition_by_slug", slug))
        if slug == "missing":
            raise ValueError("Not found")
        return {"id": "cd1", "name": "Slack"}

    async def list_actions(self, definition_id):
        self.calls.append(("list_actions", definition_id))
        return [{"id": "ca1", "action_key": "send_message"}]

    # Instances
    async def list_instances(self, org_id):
        self.calls.append(("list_instances", org_id))
        return [{"id": "ci1"}]

    async def get_instance(self, instance_id):
        self.calls.append(("get_instance", instance_id))
        if instance_id == "missing":
            raise ValueError("Connector instance not found")
        return {"id": instance_id}

    async def create_instance(self, org_id, def_id, name, **kw):
        self.calls.append(("create_instance", org_id))
        return {"id": "new-inst"}

    async def update_instance(self, instance_id, **kw):
        self.calls.append(("update_instance", instance_id))
        if instance_id == "missing":
            raise ValueError("Connector instance not found")
        return {"id": instance_id}

    async def delete_instance(self, instance_id):
        self.calls.append(("delete_instance", instance_id))
        if instance_id == "missing":
            raise ValueError("Connector instance not found")

    # MCP Servers
    async def list_mcp_servers(self, org_id):
        self.calls.append(("list_mcp_servers", org_id))
        return [{"id": "mcp1"}]

    async def get_mcp_server(self, sid):
        self.calls.append(("get_mcp_server", sid))
        if sid == "missing":
            raise ValueError("MCP server not found")
        return {"id": sid}

    async def create_mcp_server(self, org_id, name, **kw):
        self.calls.append(("create_mcp_server", org_id))
        return {"id": "new-mcp"}

    async def update_mcp_server(self, sid, **kw):
        self.calls.append(("update_mcp_server", sid))
        if sid == "missing":
            raise ValueError("MCP server not found")
        return {"id": sid}

    async def delete_mcp_server(self, sid):
        self.calls.append(("delete_mcp_server", sid))
        if sid == "missing":
            raise ValueError("MCP server not found")

    # Custom Agents
    async def list_agents(self, org_id):
        self.calls.append(("list_agents", org_id))
        return [{"id": "ag1"}]

    async def get_agent(self, aid):
        self.calls.append(("get_agent", aid))
        if aid == "missing":
            raise ValueError("Custom agent not found")
        return {"id": aid}

    async def create_agent(self, org_id, name, **kw):
        self.calls.append(("create_agent", org_id))
        return {"id": "new-agent"}

    async def update_agent(self, aid, **kw):
        self.calls.append(("update_agent", aid))
        if aid == "missing":
            raise ValueError("Custom agent not found")
        return {"id": aid}

    async def delete_agent(self, aid):
        self.calls.append(("delete_agent", aid))
        if aid == "missing":
            raise ValueError("Custom agent not found")

    # Marketplace
    async def list_marketplace(self):
        self.calls.append(("list_marketplace",))
        return [{"id": "ml1", "title": "Slack"}]

    async def get_marketplace_listing(self, lid):
        self.calls.append(("get_marketplace_listing", lid))
        if lid == "missing":
            raise ValueError("Marketplace listing not found")
        return {"id": lid, "title": "Slack"}

    async def publish_listing(
        self,
        def_id,
        publisher_org_id,
        publisher_user_id,
        title,
        short_desc,
        long_desc="",
        tags=None,
    ):
        self.calls.append(("publish_listing", def_id))
        return {"id": "new-listing"}

    # Installs
    async def list_installs(self, org_id):
        self.calls.append(("list_installs", org_id))
        return [{"definition_id": "cd1"}]

    async def install_connector(self, org_id, def_id, user_id):
        self.calls.append(("install_connector", org_id, def_id))

    async def uninstall_connector(self, org_id, def_id):
        self.calls.append(("uninstall_connector", org_id, def_id))

    # Node bindings
    async def get_node_binding(self, node_id):
        self.calls.append(("get_node_binding", node_id))
        return {"node_id": node_id}

    async def create_node_binding(self, node_id, instance_id, action_id, **kw):
        self.calls.append(("create_node_binding", node_id))
        return {"id": "new-bind"}

    async def delete_node_binding(self, bid):
        self.calls.append(("delete_node_binding", bid))


class FakeMarketingService:
    def __init__(self, env, ctx=None):
        self.calls = []

    # Channels
    async def list_channels(self, org_id):
        self.calls.append(("list_channels", org_id))
        return [{"id": "dc1"}]

    async def get_channel(self, cid):
        self.calls.append(("get_channel", cid))
        if cid == "missing":
            raise ValueError("Channel not found")
        return {"id": cid}

    async def create_channel(self, org_id, name, channel_type, **kw):
        self.calls.append(("create_channel", org_id))
        return {"id": "new-ch"}

    async def update_channel(self, cid, **kw):
        self.calls.append(("update_channel", cid))
        if cid == "missing":
            raise ValueError("Channel not found")
        return {"id": cid}

    async def delete_channel(self, cid):
        self.calls.append(("delete_channel", cid))
        if cid == "missing":
            raise ValueError("Channel not found")

    # Scheduled
    async def list_scheduled(self, uid):
        self.calls.append(("list_scheduled", uid))
        return [{"id": "sp1"}]

    async def get_scheduled(self, sid):
        self.calls.append(("get_scheduled", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def create_scheduled(
        self, article_id, scheduled_by, scheduled_at, timezone="UTC"
    ):
        self.calls.append(("create_scheduled", article_id))
        return {"id": "new-sp"}

    async def update_scheduled_status(
        self, sid, status, published_at="", error_message=""
    ):
        self.calls.append(("update_scheduled_status", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def delete_scheduled(self, sid):
        self.calls.append(("delete_scheduled", sid))
        if sid == "missing":
            raise ValueError("Not found")

    # Distribution Jobs
    async def list_dist_jobs(self, org_id, page=1, limit=20):
        self.calls.append(("list_dist_jobs", org_id))
        return {"jobs": [{"id": "dj1"}], "total": 1, "page": page, "limit": limit}

    async def get_dist_job(self, jid):
        self.calls.append(("get_dist_job", jid))
        if jid == "missing":
            raise ValueError("Not found")
        return {"id": jid}

    async def create_dist_job(
        self, org_id, article_id, channel_id, distribute_at="", run_id=""
    ):
        self.calls.append(("create_dist_job", org_id))
        return {"id": "new-dj"}

    async def update_dist_job_status(
        self, jid, status, external_id="", external_url="", error_message=""
    ):
        self.calls.append(("update_dist_job_status", jid))
        if jid == "missing":
            raise ValueError("Not found")
        return {"id": jid}

    # Syndication
    async def list_syndications(self, article_id):
        self.calls.append(("list_syndications", article_id))
        return [{"id": "cs1"}]

    async def create_syndication(
        self, article_id, platform, external_url, canonical_back_link=True
    ):
        self.calls.append(("create_syndication", article_id))
        return {"id": "new-cs"}

    async def delete_syndication(self, sid):
        self.calls.append(("delete_syndication", sid))

    # RSS Feeds
    async def list_rss_feeds(self, org_id):
        self.calls.append(("list_rss_feeds", org_id))
        return [{"id": "rf1"}]

    async def get_rss_feed(self, fid):
        self.calls.append(("get_rss_feed", fid))
        if fid == "missing":
            raise ValueError("Not found")
        return {"id": fid}

    async def create_rss_feed(self, org_id, name, slug, **kw):
        self.calls.append(("create_rss_feed", org_id))
        return {"id": "new-rf"}

    async def update_rss_feed(self, fid, **kw):
        self.calls.append(("update_rss_feed", fid))
        if fid == "missing":
            raise ValueError("Not found")
        return {"id": fid}

    async def delete_rss_feed(self, fid):
        self.calls.append(("delete_rss_feed", fid))
        if fid == "missing":
            raise ValueError("Not found")

    # Repurposing
    async def list_repurposing(self, org_id, page=1, limit=20):
        self.calls.append(("list_repurposing", org_id))
        return {"jobs": [{"id": "rj1"}], "total": 1, "page": page, "limit": limit}

    async def get_repurposing(self, rid):
        self.calls.append(("get_repurposing", rid))
        if rid == "missing":
            raise ValueError("Not found")
        return {"id": rid}

    async def create_repurposing(
        self, org_id, article_id, fmt, input_options=None, created_by=""
    ):
        self.calls.append(("create_repurposing", org_id))
        return {"id": "new-rj"}

    async def update_repurposing_status(self, rid, status, output_content=""):
        self.calls.append(("update_repurposing_status", rid))
        if rid == "missing":
            raise ValueError("Not found")
        return {"id": rid}

    # Campaigns
    async def list_campaigns(self, org_id, page=1, limit=20):
        self.calls.append(("list_campaigns", org_id))
        return {"campaigns": [{"id": "c1"}], "total": 1, "page": page, "limit": limit}

    async def get_campaign(self, cid):
        self.calls.append(("get_campaign", cid))
        if cid == "missing":
            raise ValueError("Not found")
        return {"id": cid}

    async def create_campaign(self, org_id, name, **kw):
        self.calls.append(("create_campaign", org_id))
        return {"id": "new-c"}

    async def update_campaign(self, cid, **kw):
        self.calls.append(("update_campaign", cid))
        if cid == "missing":
            raise ValueError("Not found")
        return {"id": cid}

    async def delete_campaign(self, cid):
        self.calls.append(("delete_campaign", cid))
        if cid == "missing":
            raise ValueError("Not found")

    # Campaign articles
    async def list_campaign_articles(self, campaign_id):
        self.calls.append(("list_campaign_articles", campaign_id))
        return [{"article_id": "a1"}]

    async def add_campaign_article(self, campaign_id, article_id):
        self.calls.append(("add_campaign_article", campaign_id, article_id))

    async def remove_campaign_article(self, campaign_id, article_id):
        self.calls.append(("remove_campaign_article", campaign_id, article_id))


class FakeLeadService:
    def __init__(self, env, ctx=None):
        self.calls = []

    # Forms
    async def list_forms(self, org_id):
        self.calls.append(("list_forms", org_id))
        return [{"id": "f1"}]

    async def get_form(self, fid):
        self.calls.append(("get_form", fid))
        if fid == "missing":
            raise ValueError("Form not found")
        return {"id": fid}

    async def create_form(self, org_id, owner_id, name, slug, **kw):
        self.calls.append(("create_form", org_id))
        return {"id": "new-form"}

    async def update_form(self, fid, **kw):
        self.calls.append(("update_form", fid))
        if fid == "missing":
            raise ValueError("Form not found")
        return {"id": fid}

    async def delete_form(self, fid):
        self.calls.append(("delete_form", fid))
        if fid == "missing":
            raise ValueError("Form not found")

    # Leads
    async def list_leads(self, org_id, status=None, page=1, limit=20):
        self.calls.append(("list_leads", org_id))
        return {"leads": [{"id": "l1"}], "total": 1, "page": page, "limit": limit}

    async def get_lead(self, lid):
        self.calls.append(("get_lead", lid))
        if lid == "missing":
            raise ValueError("Lead not found")
        return {"id": lid}

    async def create_lead(self, org_id, email, **kw):
        self.calls.append(("create_lead", org_id))
        return {"id": "new-lead"}

    async def update_lead(self, lid, **kw):
        self.calls.append(("update_lead", lid))
        if lid == "missing":
            raise ValueError("Lead not found")
        return {"id": lid}

    async def delete_lead(self, lid):
        self.calls.append(("delete_lead", lid))
        if lid == "missing":
            raise ValueError("Lead not found")

    # Tags
    async def list_lead_tags(self, org_id, lead_id):
        self.calls.append(("list_lead_tags", org_id, lead_id))
        return ["subscriber"]

    async def add_lead_tag(self, org_id, lead_id, tag):
        self.calls.append(("add_lead_tag", org_id, lead_id, tag))

    async def remove_lead_tag(self, org_id, lead_id, tag):
        self.calls.append(("remove_lead_tag", org_id, lead_id, tag))

    # Events
    async def list_lead_events(self, lead_id, page=1, limit=50):
        self.calls.append(("list_lead_events", lead_id))
        return {"events": [{"id": "e1"}], "total": 1, "page": page, "limit": limit}

    async def create_lead_event(
        self, lead_id, org_id, event_type, metadata=None, actor_id=""
    ):
        self.calls.append(("create_lead_event", lead_id))
        return {"id": "new-evt"}

    # Score Rules
    async def list_score_rules(self, org_id):
        self.calls.append(("list_score_rules", org_id))
        return [{"id": "sr1"}]

    async def create_score_rule(
        self, org_id, name, trigger_event, condition=None, score_delta=0, is_active=True
    ):
        self.calls.append(("create_score_rule", org_id))
        return {"id": "new-sr"}

    async def update_score_rule(self, rid, **kw):
        self.calls.append(("update_score_rule", rid))
        return {"id": rid}

    async def delete_score_rule(self, rid):
        self.calls.append(("delete_score_rule", rid))

    # Pipelines
    async def list_pipelines(self, org_id):
        self.calls.append(("list_pipelines", org_id))
        return [{"id": "p1"}]

    async def get_pipeline(self, pid):
        self.calls.append(("get_pipeline", pid))
        if pid == "missing":
            raise ValueError("Pipeline not found")
        return {"id": pid}

    async def create_pipeline(self, org_id, name, description="", sort_order=0):
        self.calls.append(("create_pipeline", org_id))
        return {"id": "new-pipe"}

    async def update_pipeline(self, pid, **kw):
        self.calls.append(("update_pipeline", pid))
        if pid == "missing":
            raise ValueError("Pipeline not found")
        return {"id": pid}

    async def delete_pipeline(self, pid):
        self.calls.append(("delete_pipeline", pid))
        if pid == "missing":
            raise ValueError("Pipeline not found")

    # Stages
    async def list_stages(self, pipeline_id):
        self.calls.append(("list_stages", pipeline_id))
        return [{"id": "ps1"}]

    async def create_stage(
        self, pipeline_id, name, sort_order=0, stage_type="open", color=""
    ):
        self.calls.append(("create_stage", pipeline_id))
        return {"id": "new-stage"}

    async def update_stage(self, sid, **kw):
        self.calls.append(("update_stage", sid))
        return {"id": sid}

    async def delete_stage(self, sid):
        self.calls.append(("delete_stage", sid))

    # Pipeline Entries
    async def list_pipeline_entries(self, pipeline_id, page=1, limit=50):
        self.calls.append(("list_pipeline_entries", pipeline_id))
        return {"entries": [{"id": "pe1"}], "total": 1, "page": page, "limit": limit}

    async def create_pipeline_entry(
        self, lead_id, pipeline_id, stage_id, assigned_to="", deal_value=0, notes=""
    ):
        self.calls.append(("create_pipeline_entry", lead_id, pipeline_id))
        return {"id": "new-entry"}

    async def update_pipeline_entry(self, eid, **kw):
        self.calls.append(("update_pipeline_entry", eid))
        return {"id": eid}

    async def delete_pipeline_entry(self, eid):
        self.calls.append(("delete_pipeline_entry", eid))

    # Sequences
    async def list_sequences(self, org_id):
        self.calls.append(("list_sequences", org_id))
        return [{"id": "es1"}]

    async def get_sequence(self, sid):
        self.calls.append(("get_sequence", sid))
        if sid == "missing":
            raise ValueError("Sequence not found")
        return {"id": sid}

    async def create_sequence(
        self, org_id, name, description="", trigger_type="", created_by=""
    ):
        self.calls.append(("create_sequence", org_id))
        return {"id": "new-seq"}

    async def update_sequence(self, sid, **kw):
        self.calls.append(("update_sequence", sid))
        if sid == "missing":
            raise ValueError("Sequence not found")
        return {"id": sid}

    async def delete_sequence(self, sid):
        self.calls.append(("delete_sequence", sid))
        if sid == "missing":
            raise ValueError("Sequence not found")

    # Steps
    async def list_steps(self, sequence_id):
        self.calls.append(("list_steps", sequence_id))
        return [{"id": "ess1"}]

    async def create_step(
        self,
        sequence_id,
        step_number=0,
        delay_days=0,
        subject="",
        body_html="",
        body_text="",
    ):
        self.calls.append(("create_step", sequence_id))
        return {"id": "new-step"}

    async def update_step(self, step_id, **kw):
        self.calls.append(("update_step", step_id))
        return {"id": step_id}

    async def delete_step(self, step_id):
        self.calls.append(("delete_step", step_id))

    # Enrollments
    async def list_enrollments(self, sequence_id, page=1, limit=50):
        self.calls.append(("list_enrollments", sequence_id))
        return {
            "enrollments": [{"id": "lse1"}],
            "total": 1,
            "page": page,
            "limit": limit,
        }

    async def create_enrollment(self, lead_id, sequence_id):
        self.calls.append(("create_enrollment", lead_id, sequence_id))
        return {"id": "new-enr"}

    async def update_enrollment(self, eid, current_step=None, status=None):
        self.calls.append(("update_enrollment", eid))
        return {"id": eid}


# ═══════════════════════════════════════════════════════════════
# Test Client Helpers
# ═══════════════════════════════════════════════════════════════
class FakeRequest:
    def __init__(self, method, url, headers=None, json_body=None):
        self.method = method
        self.url = f"https://testserver{url}"
        self.headers = headers or {}
        self._json = json_body

    async def json(self):
        return self._json or {}


class FakeCtx:
    trace_id = "test-trace"


def _token(sub="u1", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


def _make_client(handler_mod, handler_fn, fake_svc_class, svc_attr, svc_instance):
    """Generic client factory for handler tests."""

    class Client:
        def __init__(self):
            self.svc = svc_instance

        def _dispatch(self, method, path, headers=None, json_body=None):
            parsed = urlparse(path)
            req = FakeRequest(
                method=method, url=path, headers=headers or {}, json_body=json_body
            )

            class _Env:
                JWT_SECRET = _JWT_SECRET

            orig = getattr(handler_mod, svc_attr)
            setattr(handler_mod, svc_attr, lambda env, ctx=None: self.svc)
            try:
                return asyncio.run(
                    handler_fn(
                        req,
                        _Env(),
                        parsed.path,
                        method,
                        parse_qs(parsed.query),
                        FakeCtx(),
                    )
                )
            finally:
                setattr(handler_mod, svc_attr, orig)

        def get(self, path, headers=None):
            return self._dispatch("GET", path, headers=headers)

        def post(self, path, headers=None, json_body=None):
            return self._dispatch("POST", path, headers=headers, json_body=json_body)

        def put(self, path, headers=None, json_body=None):
            return self._dispatch("PUT", path, headers=headers, json_body=json_body)

        def delete(self, path, headers=None, json_body=None):
            return self._dispatch("DELETE", path, headers=headers, json_body=json_body)

    return Client()


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════
@pytest.fixture
def conn_svc():
    return FakeConnectorService(type("E", (), {})())


@pytest.fixture
def conn_client(conn_svc):
    return _make_client(
        conn_handler,
        conn_handler.handle_connectors,
        FakeConnectorService,
        "ConnectorService",
        conn_svc,
    )


@pytest.fixture
def mkt_svc():
    return FakeMarketingService(type("E", (), {})())


@pytest.fixture
def mkt_client(mkt_svc):
    return _make_client(
        mkt_handler,
        mkt_handler.handle_marketing,
        FakeMarketingService,
        "MarketingService",
        mkt_svc,
    )


@pytest.fixture
def lead_svc():
    return FakeLeadService(type("E", (), {})())


@pytest.fixture
def lead_client(lead_svc):
    return _make_client(
        lead_handler,
        lead_handler.handle_leads,
        FakeLeadService,
        "LeadService",
        lead_svc,
    )


# ═══════════════════════════════════════════════════════════════
# Step 23 — Connector Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestConnectorHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, conn_client):
        resp = conn_client.get("/api/connectors")
        assert resp.status_code == 401

    # Marketplace
    def test_list_marketplace(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connector-marketplace", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["listings"]) == 1

    def test_get_marketplace_listing(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connector-marketplace/ml1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["id"] == "ml1"

    def test_get_marketplace_listing_missing(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connector-marketplace/missing", headers=self._h())
        assert resp.status_code == 404

    def test_publish_listing(self, conn_client, conn_svc):
        resp = conn_client.post(
            "/api/connector-marketplace",
            headers=self._h(),
            json_body={"definition_id": "cd1", "org_id": "org1", "title": "Slack"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-listing"

    # Installs
    def test_list_installs(self, conn_client, conn_svc):
        resp = conn_client.get(
            "/api/connectors/installs?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200
        assert len(resp.json()["installs"]) == 1

    def test_list_installs_missing_org(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/installs", headers=self._h())
        assert resp.status_code == 400

    def test_install_connector(self, conn_client, conn_svc):
        resp = conn_client.post(
            "/api/connectors/installs",
            headers=self._h(),
            json_body={"org_id": "org1", "definition_id": "cd1"},
        )
        assert resp.status_code == 201

    def test_uninstall_connector(self, conn_client, conn_svc):
        resp = conn_client.delete(
            "/api/connectors/installs",
            headers=self._h(),
            json_body={"org_id": "org1", "definition_id": "cd1"},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    # MCP Servers
    def test_list_mcp_servers(self, conn_client, conn_svc):
        resp = conn_client.get(
            "/api/connectors/mcp-servers?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200
        assert len(resp.json()["mcp_servers"]) == 1

    def test_list_mcp_servers_missing_org(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/mcp-servers", headers=self._h())
        assert resp.status_code == 400

    def test_get_mcp_server(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/mcp-servers/mcp1", headers=self._h())
        assert resp.status_code == 200

    def test_get_mcp_server_missing(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/mcp-servers/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_mcp_server(self, conn_client, conn_svc):
        resp = conn_client.post(
            "/api/connectors/mcp-servers",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "MCP1"},
        )
        assert resp.status_code == 201

    def test_update_mcp_server(self, conn_client, conn_svc):
        resp = conn_client.put(
            "/api/connectors/mcp-servers/mcp1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_mcp_server(self, conn_client, conn_svc):
        resp = conn_client.delete("/api/connectors/mcp-servers/mcp1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_mcp_server_missing(self, conn_client, conn_svc):
        resp = conn_client.delete(
            "/api/connectors/mcp-servers/missing", headers=self._h()
        )
        assert resp.status_code == 404

    # Custom Agents
    def test_list_agents(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/agents?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["agents"]) == 1

    def test_list_agents_missing_org(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/agents", headers=self._h())
        assert resp.status_code == 400

    def test_get_agent(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/agents/ag1", headers=self._h())
        assert resp.status_code == 200

    def test_get_agent_missing(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/agents/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_agent(self, conn_client, conn_svc):
        resp = conn_client.post(
            "/api/connectors/agents",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "Bot"},
        )
        assert resp.status_code == 201

    def test_update_agent(self, conn_client, conn_svc):
        resp = conn_client.put(
            "/api/connectors/agents/ag1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_agent(self, conn_client, conn_svc):
        resp = conn_client.delete("/api/connectors/agents/ag1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_agent_missing(self, conn_client, conn_svc):
        resp = conn_client.delete("/api/connectors/agents/missing", headers=self._h())
        assert resp.status_code == 404

    # Instances
    def test_list_instances(self, conn_client, conn_svc):
        resp = conn_client.get(
            "/api/connectors/instances?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200
        assert len(resp.json()["instances"]) == 1

    def test_list_instances_missing_org(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/instances", headers=self._h())
        assert resp.status_code == 400

    def test_get_instance(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/instances/ci1", headers=self._h())
        assert resp.status_code == 200

    def test_get_instance_missing(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/instances/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_instance(self, conn_client, conn_svc):
        resp = conn_client.post(
            "/api/connectors/instances",
            headers=self._h(),
            json_body={"org_id": "org1", "definition_id": "cd1", "name": "MyConn"},
        )
        assert resp.status_code == 201

    def test_update_instance(self, conn_client, conn_svc):
        resp = conn_client.put(
            "/api/connectors/instances/ci1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_instance(self, conn_client, conn_svc):
        resp = conn_client.delete("/api/connectors/instances/ci1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_instance_missing(self, conn_client, conn_svc):
        resp = conn_client.delete(
            "/api/connectors/instances/missing", headers=self._h()
        )
        assert resp.status_code == 404

    # Node Bindings
    def test_get_node_binding(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/node-bindings/n1", headers=self._h())
        assert resp.status_code == 200

    def test_create_node_binding(self, conn_client, conn_svc):
        resp = conn_client.post(
            "/api/connectors/node-bindings",
            headers=self._h(),
            json_body={"node_id": "n1", "instance_id": "ci1", "action_id": "ca1"},
        )
        assert resp.status_code == 201

    def test_delete_node_binding(self, conn_client, conn_svc):
        resp = conn_client.delete("/api/connectors/node-bindings/b1", headers=self._h())
        assert resp.status_code == 200

    # Catalogue
    def test_list_definitions(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["definitions"]) == 1

    def test_list_definitions_with_category(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors?category=messaging", headers=self._h())
        assert resp.status_code == 200
        assert conn_svc.calls[-1] == ("list_definitions", "messaging")

    def test_get_definition_by_slug(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/slack", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["name"] == "Slack"

    def test_get_definition_by_slug_missing(self, conn_client, conn_svc):
        resp = conn_client.get("/api/connectors/missing", headers=self._h())
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Step 24 — Marketing Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestMarketingHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, mkt_client):
        resp = mkt_client.get("/api/marketing/channels?org_id=org1")
        assert resp.status_code == 401

    # Channels
    def test_list_channels(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/channels?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["channels"]) == 1

    def test_list_channels_missing_org(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/channels", headers=self._h())
        assert resp.status_code == 400

    def test_get_channel(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/channels/dc1", headers=self._h())
        assert resp.status_code == 200

    def test_get_channel_missing(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/channels/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_channel(self, mkt_client, mkt_svc):
        resp = mkt_client.post(
            "/api/marketing/channels",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "Twitter", "channel_type": "twitter"},
        )
        assert resp.status_code == 201

    def test_update_channel(self, mkt_client, mkt_svc):
        resp = mkt_client.put(
            "/api/marketing/channels/dc1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_channel(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/channels/dc1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_channel_missing(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/channels/missing", headers=self._h())
        assert resp.status_code == 404

    # Scheduled
    def test_list_scheduled(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/scheduled", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["scheduled"]) == 1

    def test_get_scheduled(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/scheduled/sp1", headers=self._h())
        assert resp.status_code == 200

    def test_get_scheduled_missing(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/scheduled/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_scheduled(self, mkt_client, mkt_svc):
        resp = mkt_client.post(
            "/api/marketing/scheduled",
            headers=self._h(),
            json_body={"article_id": "a1", "scheduled_at": "2026-03-01T12:00:00Z"},
        )
        assert resp.status_code == 201

    def test_update_scheduled(self, mkt_client, mkt_svc):
        resp = mkt_client.put(
            "/api/marketing/scheduled/sp1",
            headers=self._h(),
            json_body={"status": "published"},
        )
        assert resp.status_code == 200

    def test_delete_scheduled(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/scheduled/sp1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_scheduled_missing(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/scheduled/missing", headers=self._h())
        assert resp.status_code == 404

    # Distribution Jobs
    def test_list_dist_jobs(self, mkt_client, mkt_svc):
        resp = mkt_client.get(
            "/api/marketing/distribution-jobs?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_dist_jobs_missing_org(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/distribution-jobs", headers=self._h())
        assert resp.status_code == 400

    def test_get_dist_job(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/distribution-jobs/dj1", headers=self._h())
        assert resp.status_code == 200

    def test_create_dist_job(self, mkt_client, mkt_svc):
        resp = mkt_client.post(
            "/api/marketing/distribution-jobs",
            headers=self._h(),
            json_body={"org_id": "org1", "article_id": "a1", "channel_id": "dc1"},
        )
        assert resp.status_code == 201

    def test_update_dist_job(self, mkt_client, mkt_svc):
        resp = mkt_client.put(
            "/api/marketing/distribution-jobs/dj1",
            headers=self._h(),
            json_body={"status": "completed"},
        )
        assert resp.status_code == 200

    # Syndication
    def test_list_syndications(self, mkt_client, mkt_svc):
        resp = mkt_client.get(
            "/api/marketing/syndication?article_id=a1", headers=self._h()
        )
        assert resp.status_code == 200
        assert len(resp.json()["syndications"]) == 1

    def test_list_syndications_missing_article(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/syndication", headers=self._h())
        assert resp.status_code == 400

    def test_create_syndication(self, mkt_client, mkt_svc):
        resp = mkt_client.post(
            "/api/marketing/syndication",
            headers=self._h(),
            json_body={
                "article_id": "a1",
                "platform": "dev.to",
                "external_url": "https://dev.to/x",
            },
        )
        assert resp.status_code == 201

    def test_delete_syndication(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/syndication/cs1", headers=self._h())
        assert resp.status_code == 200

    # RSS Feeds
    def test_list_rss_feeds(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/rss-feeds?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["feeds"]) == 1

    def test_list_rss_feeds_missing_org(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/rss-feeds", headers=self._h())
        assert resp.status_code == 400

    def test_get_rss_feed(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/rss-feeds/rf1", headers=self._h())
        assert resp.status_code == 200

    def test_get_rss_feed_missing(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/rss-feeds/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_rss_feed(self, mkt_client, mkt_svc):
        resp = mkt_client.post(
            "/api/marketing/rss-feeds",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "Feed", "slug": "feed"},
        )
        assert resp.status_code == 201

    def test_update_rss_feed(self, mkt_client, mkt_svc):
        resp = mkt_client.put(
            "/api/marketing/rss-feeds/rf1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_rss_feed(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/rss-feeds/rf1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_rss_feed_missing(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/rss-feeds/missing", headers=self._h())
        assert resp.status_code == 404

    # Repurposing
    def test_list_repurposing(self, mkt_client, mkt_svc):
        resp = mkt_client.get(
            "/api/marketing/repurposing?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200

    def test_list_repurposing_missing_org(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/repurposing", headers=self._h())
        assert resp.status_code == 400

    def test_get_repurposing(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/repurposing/rj1", headers=self._h())
        assert resp.status_code == 200

    def test_create_repurposing(self, mkt_client, mkt_svc):
        resp = mkt_client.post(
            "/api/marketing/repurposing",
            headers=self._h(),
            json_body={
                "org_id": "org1",
                "article_id": "a1",
                "format": "twitter_thread",
            },
        )
        assert resp.status_code == 201

    def test_update_repurposing(self, mkt_client, mkt_svc):
        resp = mkt_client.put(
            "/api/marketing/repurposing/rj1",
            headers=self._h(),
            json_body={"status": "completed"},
        )
        assert resp.status_code == 200

    # Campaigns
    def test_list_campaigns(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/campaigns?org_id=org1", headers=self._h())
        assert resp.status_code == 200

    def test_list_campaigns_missing_org(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/campaigns", headers=self._h())
        assert resp.status_code == 400

    def test_get_campaign(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/campaigns/c1", headers=self._h())
        assert resp.status_code == 200

    def test_get_campaign_missing(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/campaigns/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_campaign(self, mkt_client, mkt_svc):
        resp = mkt_client.post(
            "/api/marketing/campaigns",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "Launch"},
        )
        assert resp.status_code == 201

    def test_update_campaign(self, mkt_client, mkt_svc):
        resp = mkt_client.put(
            "/api/marketing/campaigns/c1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_campaign(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/campaigns/c1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_campaign_missing(self, mkt_client, mkt_svc):
        resp = mkt_client.delete("/api/marketing/campaigns/missing", headers=self._h())
        assert resp.status_code == 404

    # Campaign articles
    def test_list_campaign_articles(self, mkt_client, mkt_svc):
        resp = mkt_client.get("/api/marketing/campaigns/c1/articles", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["articles"]) == 1

    def test_add_campaign_article(self, mkt_client, mkt_svc):
        resp = mkt_client.post(
            "/api/marketing/campaigns/c1/articles",
            headers=self._h(),
            json_body={"article_id": "a1"},
        )
        assert resp.status_code == 201

    def test_remove_campaign_article(self, mkt_client, mkt_svc):
        resp = mkt_client.delete(
            "/api/marketing/campaigns/c1/articles/a1", headers=self._h()
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# Step 25 — Lead Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestLeadHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, lead_client):
        resp = lead_client.get("/api/leads/forms?org_id=org1")
        assert resp.status_code == 401

    # Forms
    def test_list_forms(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/forms?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["forms"]) == 1

    def test_list_forms_missing_org(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/forms", headers=self._h())
        assert resp.status_code == 400

    def test_get_form(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/forms/f1", headers=self._h())
        assert resp.status_code == 200

    def test_get_form_missing(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/forms/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_form(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/forms",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "Newsletter", "slug": "news"},
        )
        assert resp.status_code == 201

    def test_update_form(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/forms/f1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_form(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/forms/f1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_form_missing(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/forms/missing", headers=self._h())
        assert resp.status_code == 404

    # Score Rules
    def test_list_score_rules(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/score-rules?org_id=org1", headers=self._h())
        assert resp.status_code == 200

    def test_list_score_rules_missing_org(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/score-rules", headers=self._h())
        assert resp.status_code == 400

    def test_create_score_rule(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/score-rules",
            headers=self._h(),
            json_body={
                "org_id": "org1",
                "name": "Open",
                "trigger_event": "email_open",
                "score_delta": 5,
            },
        )
        assert resp.status_code == 201

    def test_update_score_rule(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/score-rules/sr1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_score_rule(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/score-rules/sr1", headers=self._h())
        assert resp.status_code == 200

    # Pipelines
    def test_list_pipelines(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/pipelines?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["pipelines"]) == 1

    def test_list_pipelines_missing_org(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/pipelines", headers=self._h())
        assert resp.status_code == 400

    def test_get_pipeline(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/pipelines/p1", headers=self._h())
        assert resp.status_code == 200

    def test_get_pipeline_missing(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/pipelines/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_pipeline(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/pipelines",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "Sales"},
        )
        assert resp.status_code == 201

    def test_update_pipeline(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/pipelines/p1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_pipeline(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/pipelines/p1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_pipeline_missing(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/pipelines/missing", headers=self._h())
        assert resp.status_code == 404

    # Stages sub-resource
    def test_list_stages(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/pipelines/p1/stages", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["stages"]) == 1

    def test_create_stage(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/pipelines/p1/stages",
            headers=self._h(),
            json_body={"name": "New"},
        )
        assert resp.status_code == 201

    def test_update_stage(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/pipelines/p1/stages/ps1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_stage(self, lead_client, lead_svc):
        resp = lead_client.delete(
            "/api/leads/pipelines/p1/stages/ps1", headers=self._h()
        )
        assert resp.status_code == 200

    # Pipeline Entries sub-resource
    def test_list_pipeline_entries(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/pipelines/p1/entries", headers=self._h())
        assert resp.status_code == 200

    def test_create_pipeline_entry(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/pipelines/p1/entries",
            headers=self._h(),
            json_body={"lead_id": "l1", "stage_id": "ps1"},
        )
        assert resp.status_code == 201

    def test_update_pipeline_entry(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/pipelines/p1/entries/pe1",
            headers=self._h(),
            json_body={"stage_id": "ps2"},
        )
        assert resp.status_code == 200

    def test_delete_pipeline_entry(self, lead_client, lead_svc):
        resp = lead_client.delete(
            "/api/leads/pipelines/p1/entries/pe1", headers=self._h()
        )
        assert resp.status_code == 200

    # Sequences
    def test_list_sequences(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/sequences?org_id=org1", headers=self._h())
        assert resp.status_code == 200

    def test_list_sequences_missing_org(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/sequences", headers=self._h())
        assert resp.status_code == 400

    def test_get_sequence(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/sequences/es1", headers=self._h())
        assert resp.status_code == 200

    def test_get_sequence_missing(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/sequences/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_sequence(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/sequences",
            headers=self._h(),
            json_body={
                "org_id": "org1",
                "name": "Welcome",
                "trigger_type": "form_submit",
            },
        )
        assert resp.status_code == 201

    def test_update_sequence(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/sequences/es1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_sequence(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/sequences/es1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_sequence_missing(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/sequences/missing", headers=self._h())
        assert resp.status_code == 404

    # Steps sub-resource
    def test_list_steps(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/sequences/es1/steps", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["steps"]) == 1

    def test_create_step(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/sequences/es1/steps",
            headers=self._h(),
            json_body={"step_number": 1, "delay_days": 1, "subject": "Welcome!"},
        )
        assert resp.status_code == 201

    def test_update_step(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/sequences/es1/steps/ess1",
            headers=self._h(),
            json_body={"subject": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_step(self, lead_client, lead_svc):
        resp = lead_client.delete(
            "/api/leads/sequences/es1/steps/ess1", headers=self._h()
        )
        assert resp.status_code == 200

    # Enrollments sub-resource
    def test_list_enrollments(self, lead_client, lead_svc):
        resp = lead_client.get(
            "/api/leads/sequences/es1/enrollments", headers=self._h()
        )
        assert resp.status_code == 200

    def test_create_enrollment(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/sequences/es1/enrollments",
            headers=self._h(),
            json_body={"lead_id": "l1"},
        )
        assert resp.status_code == 201

    def test_update_enrollment(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/sequences/es1/enrollments/lse1",
            headers=self._h(),
            json_body={"status": "completed"},
        )
        assert resp.status_code == 200

    # Lead CRUD
    def test_list_leads(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads?org_id=org1", headers=self._h())
        assert resp.status_code == 200

    def test_list_leads_missing_org(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads", headers=self._h())
        assert resp.status_code == 400

    def test_create_lead(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads",
            headers=self._h(),
            json_body={"org_id": "org1", "email": "test@example.com"},
        )
        assert resp.status_code == 201

    def test_get_lead(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/l1", headers=self._h())
        assert resp.status_code == 200

    def test_get_lead_missing(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_lead(self, lead_client, lead_svc):
        resp = lead_client.put(
            "/api/leads/l1",
            headers=self._h(),
            json_body={"first_name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_lead(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/l1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_lead_missing(self, lead_client, lead_svc):
        resp = lead_client.delete("/api/leads/missing", headers=self._h())
        assert resp.status_code == 404

    # Lead tags sub-resource
    def test_list_lead_tags(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/l1/tags?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["tags"] == ["subscriber"]

    def test_list_lead_tags_missing_org(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/l1/tags", headers=self._h())
        assert resp.status_code == 400

    def test_add_lead_tag(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/l1/tags?org_id=org1",
            headers=self._h(),
            json_body={"tag": "premium"},
        )
        assert resp.status_code == 201

    def test_remove_lead_tag(self, lead_client, lead_svc):
        resp = lead_client.delete(
            "/api/leads/l1/tags/premium?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200

    # Lead events sub-resource
    def test_list_lead_events(self, lead_client, lead_svc):
        resp = lead_client.get("/api/leads/l1/events", headers=self._h())
        assert resp.status_code == 200

    def test_create_lead_event(self, lead_client, lead_svc):
        resp = lead_client.post(
            "/api/leads/l1/events",
            headers=self._h(),
            json_body={"org_id": "org1", "event_type": "page_view"},
        )
        assert resp.status_code == 201
