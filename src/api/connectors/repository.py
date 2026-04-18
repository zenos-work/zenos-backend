"""Phase 5 Step 23 — Connector repository."""

import json
from db.repository import BaseRepository
from api.connectors import queries as Q
from models.connector.model import (
    ConnectorDefinition,
    ConnectorAction,
    ConnectorInstance,
    McpServer,
    CustomAgent,
    ConnectorMarketplaceListing,
)


class ConnectorRepository(BaseRepository):
    def _one(self, model_cls, row):
        return self.map_one(row, model_cls)

    def _many(self, rows, model_cls):
        return self.map_many(rows, model_cls)

    # ── Definitions ──────────────────────────────────────────
    async def list_definitions(self, category=None):
        if category:
            rows = await self.find_all(Q.LIST_DEFINITIONS_BY_CATEGORY, category)
        else:
            rows = await self.find_all(Q.LIST_DEFINITIONS)
        return self._many(rows, ConnectorDefinition)

    async def get_definition(self, def_id):
        return self._one(
            ConnectorDefinition, await self.find_one(Q.GET_DEFINITION, def_id)
        )

    async def get_definition_by_slug(self, slug):
        return self._one(
            ConnectorDefinition, await self.find_one(Q.GET_DEFINITION_BY_SLUG, slug)
        )

    # ── Actions ──────────────────────────────────────────────
    async def list_actions(self, definition_id):
        rows = await self.find_all(Q.LIST_ACTIONS, definition_id)
        return self._many(rows, ConnectorAction)

    async def get_action(self, action_id):
        return self._one(ConnectorAction, await self.find_one(Q.GET_ACTION, action_id))

    # ── Instances ────────────────────────────────────────────
    async def list_instances(self, org_id):
        rows = await self.find_all(Q.LIST_INSTANCES, org_id)
        return self._many(rows, ConnectorInstance)

    async def get_instance(self, instance_id):
        return self._one(
            ConnectorInstance, await self.find_one(Q.GET_INSTANCE, instance_id)
        )

    async def create_instance(
        self,
        iid,
        org_id,
        def_id,
        name,
        auth_method,
        kv_secret_key,
        instance_config,
        status,
        created_by,
    ):
        cfg = (
            json.dumps(instance_config)
            if isinstance(instance_config, dict)
            else (instance_config or "{}")
        )
        await self.execute(
            Q.INSERT_INSTANCE,
            iid,
            org_id,
            def_id,
            name,
            auth_method,
            kv_secret_key,
            cfg,
            status,
            created_by,
        )

    async def update_instance(self, iid, name, instance_config, status):
        cfg = (
            json.dumps(instance_config)
            if isinstance(instance_config, dict)
            else (instance_config or "{}")
        )
        await self.execute(Q.UPDATE_INSTANCE, name, cfg, status, iid)

    async def delete_instance(self, iid):
        await self.execute(Q.DELETE_INSTANCE, iid)

    # ── MCP Servers ──────────────────────────────────────────
    async def list_mcp_servers(self, org_id):
        rows = await self.find_all(Q.LIST_MCP_SERVERS, org_id)
        return self._many(rows, McpServer)

    async def get_mcp_server(self, sid):
        return self._one(McpServer, await self.find_one(Q.GET_MCP_SERVER, sid))

    async def create_mcp_server(
        self,
        sid,
        org_id,
        name,
        description,
        transport,
        endpoint_url,
        command,
        args,
        auth_method,
        kv_secret_key,
        tools_schema,
        status,
        created_by,
    ):
        await self.execute(
            Q.INSERT_MCP_SERVER,
            sid,
            org_id,
            name,
            description,
            transport,
            endpoint_url,
            command,
            json.dumps(args or []),
            auth_method,
            kv_secret_key,
            json.dumps(tools_schema or []),
            status,
            created_by,
        )

    async def update_mcp_server(self, sid, name, description, endpoint_url, status):
        await self.execute(
            Q.UPDATE_MCP_SERVER, name, description, endpoint_url, status, sid
        )

    async def delete_mcp_server(self, sid):
        await self.execute(Q.DELETE_MCP_SERVER, sid)

    # ── Custom Agents ────────────────────────────────────────
    async def list_agents(self, org_id):
        rows = await self.find_all(Q.LIST_AGENTS, org_id)
        return self._many(rows, CustomAgent)

    async def get_agent(self, aid):
        return self._one(CustomAgent, await self.find_one(Q.GET_AGENT, aid))

    async def create_agent(
        self,
        aid,
        org_id,
        name,
        description,
        agent_type,
        model_provider,
        model_id,
        model_config,
        system_prompt,
        tool_ids,
        mcp_server_id,
        endpoint_url,
        is_active,
        created_by,
    ):
        await self.execute(
            Q.INSERT_AGENT,
            aid,
            org_id,
            name,
            description,
            agent_type,
            model_provider,
            model_id,
            json.dumps(model_config or {}),
            system_prompt,
            json.dumps(tool_ids or []),
            mcp_server_id,
            endpoint_url,
            int(is_active),
            created_by,
        )

    async def update_agent(
        self, aid, name, description, model_config, system_prompt, is_active
    ):
        await self.execute(
            Q.UPDATE_AGENT,
            name,
            description,
            json.dumps(model_config or {}),
            system_prompt,
            int(is_active),
            aid,
        )

    async def delete_agent(self, aid):
        await self.execute(Q.DELETE_AGENT, aid)

    # ── Marketplace ──────────────────────────────────────────
    async def list_marketplace(self):
        rows = await self.find_all(Q.LIST_MARKETPLACE)
        return self._many(rows, ConnectorMarketplaceListing)

    async def get_marketplace_listing(self, lid):
        return self._one(
            ConnectorMarketplaceListing,
            await self.find_one(Q.GET_MARKETPLACE_LISTING, lid),
        )

    async def create_marketplace_listing(
        self,
        lid,
        def_id,
        publisher_org_id,
        publisher_user_id,
        title,
        short_desc,
        long_desc,
        tags,
        is_public,
    ):
        await self.execute(
            Q.INSERT_MARKETPLACE_LISTING,
            lid,
            def_id,
            publisher_org_id,
            publisher_user_id,
            title,
            short_desc,
            long_desc,
            json.dumps(tags or []),
            int(is_public),
        )

    # ── Installs ─────────────────────────────────────────────
    async def list_installs(self, org_id):
        return await self.find_all(Q.LIST_INSTALLS, org_id)

    async def install_connector(self, org_id, def_id, user_id):
        await self.execute(Q.INSERT_INSTALL, org_id, def_id, user_id)

    async def uninstall_connector(self, org_id, def_id):
        await self.execute(Q.DELETE_INSTALL, org_id, def_id)

    # ── Node bindings ────────────────────────────────────────
    async def get_node_binding(self, node_id):
        row = await self.find_one(Q.GET_NODE_BINDING, node_id)
        return row

    async def create_node_binding(
        self,
        bid,
        node_id,
        instance_id,
        action_id,
        param_bindings,
        output_bindings,
        max_retries,
        retry_delay,
        timeout,
    ):
        await self.execute(
            Q.INSERT_NODE_BINDING,
            bid,
            node_id,
            instance_id,
            action_id,
            json.dumps(param_bindings or {}),
            json.dumps(output_bindings or {}),
            max_retries,
            retry_delay,
            timeout,
        )

    async def delete_node_binding(self, bid):
        await self.execute(Q.DELETE_NODE_BINDING, bid)
