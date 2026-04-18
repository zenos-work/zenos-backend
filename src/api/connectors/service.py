"""Phase 5 Step 23 — Connector service."""

from api.connectors.repository import ConnectorRepository
from utils.helpers import new_id


class ConnectorService:
    def __init__(self, env, ctx=None):
        self._repo = ConnectorRepository(env.DB, ctx)

    # ── Catalogue ────────────────────────────────────────────
    async def list_definitions(self, category=None):
        items = await self._repo.list_definitions(category)
        return [d.to_dict() for d in items]

    async def get_definition(self, def_id):
        d = await self._repo.get_definition(def_id)
        if not d:
            raise ValueError("Connector definition not found")
        return d.to_dict(scope="admin")

    async def get_definition_by_slug(self, slug):
        d = await self._repo.get_definition_by_slug(slug)
        if not d:
            raise ValueError("Connector definition not found")
        return d.to_dict(scope="admin")

    async def list_actions(self, definition_id):
        items = await self._repo.list_actions(definition_id)
        return [a.to_dict() for a in items]

    # ── Instances ────────────────────────────────────────────
    async def list_instances(self, org_id):
        items = await self._repo.list_instances(org_id)
        return [i.to_dict() for i in items]

    async def get_instance(self, instance_id):
        i = await self._repo.get_instance(instance_id)
        if not i:
            raise ValueError("Connector instance not found")
        return i.to_dict(scope="admin")

    async def create_instance(
        self,
        org_id,
        def_id,
        name,
        auth_method="none",
        kv_secret_key=None,
        instance_config=None,
        created_by="",
    ):
        iid = new_id()
        await self._repo.create_instance(
            iid,
            org_id,
            def_id,
            name,
            auth_method,
            kv_secret_key,
            instance_config or {},
            "pending_auth",
            created_by,
        )
        return {"id": iid}

    async def update_instance(
        self, instance_id, name=None, instance_config=None, status=None
    ):
        existing = await self._repo.get_instance(instance_id)
        if not existing:
            raise ValueError("Connector instance not found")
        await self._repo.update_instance(
            instance_id,
            name or existing.name,
            instance_config
            if instance_config is not None
            else existing.instance_config,
            status or existing.status,
        )
        return {"id": instance_id}

    async def delete_instance(self, instance_id):
        existing = await self._repo.get_instance(instance_id)
        if not existing:
            raise ValueError("Connector instance not found")
        await self._repo.delete_instance(instance_id)

    # ── MCP Servers ──────────────────────────────────────────
    async def list_mcp_servers(self, org_id):
        items = await self._repo.list_mcp_servers(org_id)
        return [s.to_dict() for s in items]

    async def get_mcp_server(self, sid):
        s = await self._repo.get_mcp_server(sid)
        if not s:
            raise ValueError("MCP server not found")
        return s.to_dict()

    async def create_mcp_server(
        self,
        org_id,
        name,
        description="",
        transport="sse",
        endpoint_url=None,
        command=None,
        args=None,
        auth_method="bearer",
        kv_secret_key=None,
        tools_schema=None,
        created_by="",
    ):
        sid = new_id()
        await self._repo.create_mcp_server(
            sid,
            org_id,
            name,
            description,
            transport,
            endpoint_url,
            command,
            args or [],
            auth_method,
            kv_secret_key,
            tools_schema or [],
            "pending",
            created_by,
        )
        return {"id": sid}

    async def update_mcp_server(
        self, sid, name=None, description=None, endpoint_url=None, status=None
    ):
        existing = await self._repo.get_mcp_server(sid)
        if not existing:
            raise ValueError("MCP server not found")
        await self._repo.update_mcp_server(
            sid,
            name or existing.name,
            description if description is not None else existing.description,
            endpoint_url if endpoint_url is not None else existing.endpoint_url,
            status or existing.status,
        )
        return {"id": sid}

    async def delete_mcp_server(self, sid):
        existing = await self._repo.get_mcp_server(sid)
        if not existing:
            raise ValueError("MCP server not found")
        await self._repo.delete_mcp_server(sid)

    # ── Custom Agents ────────────────────────────────────────
    async def list_agents(self, org_id):
        items = await self._repo.list_agents(org_id)
        return [a.to_dict() for a in items]

    async def get_agent(self, aid):
        a = await self._repo.get_agent(aid)
        if not a:
            raise ValueError("Custom agent not found")
        return a.to_dict()

    async def create_agent(
        self,
        org_id,
        name,
        description="",
        agent_type="llm_chain",
        model_provider="cloudflare_ai",
        model_id="",
        model_config=None,
        system_prompt=None,
        tool_ids=None,
        mcp_server_id=None,
        endpoint_url=None,
        created_by="",
    ):
        aid = new_id()
        await self._repo.create_agent(
            aid,
            org_id,
            name,
            description,
            agent_type,
            model_provider,
            model_id,
            model_config or {},
            system_prompt,
            tool_ids or [],
            mcp_server_id,
            endpoint_url,
            True,
            created_by,
        )
        return {"id": aid}

    async def update_agent(
        self,
        aid,
        name=None,
        description=None,
        model_config=None,
        system_prompt=None,
        is_active=None,
    ):
        existing = await self._repo.get_agent(aid)
        if not existing:
            raise ValueError("Custom agent not found")
        await self._repo.update_agent(
            aid,
            name or existing.name,
            description if description is not None else existing.description,
            model_config if model_config is not None else existing.model_config_data,
            system_prompt if system_prompt is not None else existing.system_prompt,
            is_active if is_active is not None else existing.is_active,
        )
        return {"id": aid}

    async def delete_agent(self, aid):
        existing = await self._repo.get_agent(aid)
        if not existing:
            raise ValueError("Custom agent not found")
        await self._repo.delete_agent(aid)

    # ── Marketplace ──────────────────────────────────────────
    async def list_marketplace(self):
        items = await self._repo.list_marketplace()
        return [listing.to_dict() for listing in items]

    async def get_marketplace_listing(self, lid):
        listing = await self._repo.get_marketplace_listing(lid)
        if not listing:
            raise ValueError("Marketplace listing not found")
        return listing.to_dict()

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
        lid = new_id()
        await self._repo.create_marketplace_listing(
            lid,
            def_id,
            publisher_org_id,
            publisher_user_id,
            title,
            short_desc,
            long_desc,
            tags or [],
            True,
        )
        return {"id": lid}

    # ── Installs ─────────────────────────────────────────────
    async def list_installs(self, org_id):
        return await self._repo.list_installs(org_id)

    async def install_connector(self, org_id, def_id, user_id):
        await self._repo.install_connector(org_id, def_id, user_id)

    async def uninstall_connector(self, org_id, def_id):
        await self._repo.uninstall_connector(org_id, def_id)

    # ── Node bindings ────────────────────────────────────────
    async def get_node_binding(self, node_id):
        return await self._repo.get_node_binding(node_id)

    async def create_node_binding(
        self,
        node_id,
        instance_id,
        action_id,
        param_bindings=None,
        output_bindings=None,
        max_retries=2,
        retry_delay=30,
        timeout=120,
    ):
        bid = new_id()
        await self._repo.create_node_binding(
            bid,
            node_id,
            instance_id,
            action_id,
            param_bindings or {},
            output_bindings or {},
            max_retries,
            retry_delay,
            timeout,
        )
        return {"id": bid}

    async def delete_node_binding(self, bid):
        await self._repo.delete_node_binding(bid)
