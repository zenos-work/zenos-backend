"""Phase 5 Step 23 — Connector SQL queries."""

# ── Definitions (catalogue) ──────────────────────────────────
LIST_DEFINITIONS = (
    "SELECT * FROM connector_definitions WHERE is_active = 1 ORDER BY category, name"
)
LIST_DEFINITIONS_BY_CATEGORY = "SELECT * FROM connector_definitions WHERE is_active = 1 AND category = ? ORDER BY name"
GET_DEFINITION = "SELECT * FROM connector_definitions WHERE id = ?"
GET_DEFINITION_BY_SLUG = "SELECT * FROM connector_definitions WHERE slug = ?"

# ── Actions ──────────────────────────────────────────────────
LIST_ACTIONS = (
    "SELECT * FROM connector_actions WHERE connector_definition_id = ? AND is_active = 1"
    " ORDER BY sort_order"
)
GET_ACTION = "SELECT * FROM connector_actions WHERE id = ?"

# ── Instances (org-scoped) ───────────────────────────────────
LIST_INSTANCES = (
    "SELECT * FROM connector_instances WHERE org_id = ? ORDER BY created_at DESC"
)
GET_INSTANCE = "SELECT * FROM connector_instances WHERE id = ?"
INSERT_INSTANCE = (
    "INSERT INTO connector_instances"
    " (id, org_id, connector_definition_id, name, auth_method, kv_secret_key,"
    "  instance_config, status, created_by)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
UPDATE_INSTANCE = (
    "UPDATE connector_instances SET name = ?, instance_config = ?,"
    " status = ?, updated_at = datetime('now') WHERE id = ?"
)
DELETE_INSTANCE = "DELETE FROM connector_instances WHERE id = ?"

# ── MCP Servers ──────────────────────────────────────────────
LIST_MCP_SERVERS = (
    "SELECT * FROM mcp_server_registry WHERE org_id = ? ORDER BY created_at DESC"
)
GET_MCP_SERVER = "SELECT * FROM mcp_server_registry WHERE id = ?"
INSERT_MCP_SERVER = (
    "INSERT INTO mcp_server_registry"
    " (id, org_id, name, description, transport, endpoint_url, command, args,"
    "  auth_method, kv_secret_key, tools_schema, status, created_by)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
UPDATE_MCP_SERVER = (
    "UPDATE mcp_server_registry SET name = ?, description = ?, endpoint_url = ?,"
    " status = ?, updated_at = datetime('now') WHERE id = ?"
)
DELETE_MCP_SERVER = "DELETE FROM mcp_server_registry WHERE id = ?"

# ── Custom Agents ────────────────────────────────────────────
LIST_AGENTS = "SELECT * FROM custom_agents WHERE org_id = ? ORDER BY created_at DESC"
GET_AGENT = "SELECT * FROM custom_agents WHERE id = ?"
INSERT_AGENT = (
    "INSERT INTO custom_agents"
    " (id, org_id, name, description, agent_type, model_provider, model_id,"
    "  model_config, system_prompt, tool_connector_action_ids, mcp_server_id,"
    "  endpoint_url, is_active, created_by)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
UPDATE_AGENT = (
    "UPDATE custom_agents SET name = ?, description = ?, model_config = ?,"
    " system_prompt = ?, is_active = ?, updated_at = datetime('now') WHERE id = ?"
)
DELETE_AGENT = "DELETE FROM custom_agents WHERE id = ?"

# ── Marketplace Listings ─────────────────────────────────────
LIST_MARKETPLACE = (
    "SELECT * FROM connector_marketplace_listings WHERE is_public = 1"
    " ORDER BY install_count DESC"
)
GET_MARKETPLACE_LISTING = "SELECT * FROM connector_marketplace_listings WHERE id = ?"
INSERT_MARKETPLACE_LISTING = (
    "INSERT INTO connector_marketplace_listings"
    " (id, connector_definition_id, publisher_org_id, publisher_user_id,"
    "  listing_title, short_description, long_description, tags, is_public, published_at)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))"
)

# ── Installs ─────────────────────────────────────────────────
LIST_INSTALLS = "SELECT * FROM connector_installs WHERE org_id = ?"
INSERT_INSTALL = (
    "INSERT OR IGNORE INTO connector_installs (org_id, connector_definition_id, installed_by)"
    " VALUES (?, ?, ?)"
)
DELETE_INSTALL = (
    "DELETE FROM connector_installs WHERE org_id = ? AND connector_definition_id = ?"
)

# ── Node connector bindings ──────────────────────────────────
GET_NODE_BINDING = (
    "SELECT * FROM workflow_node_connector_bindings WHERE workflow_node_id = ?"
)
INSERT_NODE_BINDING = (
    "INSERT INTO workflow_node_connector_bindings"
    " (id, workflow_node_id, connector_instance_id, connector_action_id,"
    "  param_bindings, output_bindings, max_retries, retry_delay_seconds, timeout_seconds)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
DELETE_NODE_BINDING = "DELETE FROM workflow_node_connector_bindings WHERE id = ?"
