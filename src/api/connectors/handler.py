"""Phase 5 Step 23 — Connector handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.connectors.service import ConnectorService


async def handle_connectors(request, env, path, method, query, ctx):
    svc = ConnectorService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Marketplace ──────────────────────────────────────────
    if path.startswith("/api/connector-marketplace"):
        # GET /api/connector-marketplace
        if method == "GET" and len(parts) == 3:
            return json_resp({"listings": await svc.list_marketplace()})
        # GET /api/connector-marketplace/:id
        if method == "GET" and len(parts) == 4:
            try:
                return json_resp(await svc.get_marketplace_listing(parts[3]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/connector-marketplace
        if method == "POST" and len(parts) == 3:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.publish_listing(
                    def_id=data.get("definition_id", ""),
                    publisher_org_id=data.get("org_id", ""),
                    publisher_user_id=uid,
                    title=data.get("title", ""),
                    short_desc=data.get("short_description", ""),
                    long_desc=data.get("long_description", ""),
                    tags=data.get("tags"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        return error("Not found", 404)

    # ── Installs ─────────────────────────────────────────────
    if path.startswith("/api/connectors/installs"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/connectors/installs
        if method == "GET":
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"installs": await svc.list_installs(org_id)})
        # POST /api/connectors/installs
        if method == "POST":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                await svc.install_connector(
                    data.get("org_id", ""),
                    data.get("definition_id", ""),
                    uid,
                )
                return json_resp({"installed": True}, 201)
            except Exception as e:
                return error(str(e), 400)
        # DELETE /api/connectors/installs
        if method == "DELETE":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            await svc.uninstall_connector(
                data.get("org_id", ""),
                data.get("definition_id", ""),
            )
            return json_resp({"deleted": True})
        return error("Not found", 404)

    # ── MCP Servers ──────────────────────────────────────────
    if path.startswith("/api/connectors/mcp-servers"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/connectors/mcp-servers
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"mcp_servers": await svc.list_mcp_servers(org_id)})
        # GET /api/connectors/mcp-servers/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_mcp_server(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/connectors/mcp-servers
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_mcp_server(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    transport=data.get("transport", "sse"),
                    endpoint_url=data.get("endpoint_url"),
                    command=data.get("command"),
                    args=data.get("args"),
                    auth_method=data.get("auth_method", "bearer"),
                    kv_secret_key=data.get("kv_secret_key"),
                    tools_schema=data.get("tools_schema"),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/connectors/mcp-servers/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_mcp_server(
                    parts[4],
                    name=data.get("name"),
                    description=data.get("description"),
                    endpoint_url=data.get("endpoint_url"),
                    status=data.get("status"),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/connectors/mcp-servers/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_mcp_server(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Custom Agents ────────────────────────────────────────
    if path.startswith("/api/connectors/agents"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/connectors/agents
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"agents": await svc.list_agents(org_id)})
        # GET /api/connectors/agents/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_agent(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/connectors/agents
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_agent(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    agent_type=data.get("agent_type", "llm_chain"),
                    model_provider=data.get("model_provider", "cloudflare_ai"),
                    model_id=data.get("model_id", ""),
                    model_config=data.get("model_config"),
                    system_prompt=data.get("system_prompt"),
                    tool_ids=data.get("tool_ids"),
                    mcp_server_id=data.get("mcp_server_id"),
                    endpoint_url=data.get("endpoint_url"),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/connectors/agents/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_agent(
                    parts[4],
                    name=data.get("name"),
                    description=data.get("description"),
                    model_config=data.get("model_config"),
                    system_prompt=data.get("system_prompt"),
                    is_active=data.get("is_active"),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/connectors/agents/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_agent(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Instances ────────────────────────────────────────────
    if path.startswith("/api/connectors/instances"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/connectors/instances
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"instances": await svc.list_instances(org_id)})
        # GET /api/connectors/instances/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_instance(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/connectors/instances
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_instance(
                    org_id=data.get("org_id", ""),
                    def_id=data.get("definition_id", ""),
                    name=data.get("name", ""),
                    auth_method=data.get("auth_method", "none"),
                    kv_secret_key=data.get("kv_secret_key"),
                    instance_config=data.get("config"),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/connectors/instances/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_instance(
                    parts[4],
                    name=data.get("name"),
                    instance_config=data.get("config"),
                    status=data.get("status"),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/connectors/instances/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_instance(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Node Bindings ────────────────────────────────────────
    if path.startswith("/api/connectors/node-bindings"):
        # GET /api/connectors/node-bindings/:node_id
        if method == "GET" and len(parts) == 5:
            binding = await svc.get_node_binding(parts[4])
            return json_resp({"binding": binding})
        # POST /api/connectors/node-bindings
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_node_binding(
                    node_id=data.get("node_id", ""),
                    instance_id=data.get("instance_id", ""),
                    action_id=data.get("action_id", ""),
                    param_bindings=data.get("param_bindings"),
                    output_bindings=data.get("output_bindings"),
                    max_retries=data.get("max_retries", 2),
                    retry_delay=data.get("retry_delay", 30),
                    timeout=data.get("timeout", 120),
                )
                return json_resp(result, 201)
            except Exception as e:
                return error(str(e), 400)
        # DELETE /api/connectors/node-bindings/:id
        if method == "DELETE" and len(parts) == 5:
            await svc.delete_node_binding(parts[4])
            return json_resp({"deleted": True})
        return error("Not found", 404)

    # ── Catalogue (definitions + actions) ────────────────────
    # GET /api/connectors
    if path.rstrip("/") == "/api/connectors" and method == "GET":
        category = query.get("category", [None])[0]
        return json_resp({"definitions": await svc.list_definitions(category)})

    # GET /api/connectors/:slug
    if len(parts) == 4 and method == "GET":
        slug = parts[3]
        try:
            defn = await svc.get_definition_by_slug(slug)
            actions = await svc.list_actions(defn["id"])
            defn["actions"] = actions
            return json_resp(defn)
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
