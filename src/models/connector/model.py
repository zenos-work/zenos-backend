"""Phase 5 — Connector models (Step 23)."""

from dataclasses import dataclass
from typing import Optional
import json
from models.base import BaseModel, row_get


def _json_field(row, key, default="{}"):
    raw = row_get(row, key, default)
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw) if raw else ([] if default == "[]" else {})
    except (json.JSONDecodeError, TypeError):
        return [] if default == "[]" else {}


@dataclass
class ConnectorDefinition(BaseModel):
    id: str
    name: str
    slug: str
    source_type: str
    auth_method: str
    category: str
    is_active: bool
    is_verified: bool
    is_enterprise: bool
    version: str
    created_at: str
    updated_at: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    auth_config_schema: Optional[dict] = None
    instance_config_schema: Optional[dict] = None
    openapi_spec_url: Optional[str] = None
    created_by: Optional[str] = None
    org_id: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row_get(row, "id"),
            name=row_get(row, "name"),
            slug=row_get(row, "slug"),
            description=row_get(row, "description"),
            logo_url=row_get(row, "logo_url"),
            documentation_url=row_get(row, "documentation_url"),
            source_type=row_get(row, "source_type", "builtin"),
            auth_method=row_get(row, "auth_method", "none"),
            auth_config_schema=_json_field(row, "auth_config_schema"),
            instance_config_schema=_json_field(row, "instance_config_schema"),
            openapi_spec_url=row_get(row, "openapi_spec_url"),
            category=row_get(row, "category", "other"),
            is_enterprise=bool(row_get(row, "is_enterprise", 0)),
            is_active=bool(row_get(row, "is_active", 1)),
            is_verified=bool(row_get(row, "is_verified", 0)),
            created_by=row_get(row, "created_by"),
            org_id=row_get(row, "org_id"),
            version=row_get(row, "version", "1.0.0"),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "logo_url": self.logo_url,
            "category": self.category,
            "source_type": self.source_type,
            "auth_method": self.auth_method,
            "is_enterprise": self.is_enterprise,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "version": self.version,
        }
        if scope == "admin":
            d["auth_config_schema"] = self.auth_config_schema or {}
            d["instance_config_schema"] = self.instance_config_schema or {}
            d["openapi_spec_url"] = self.openapi_spec_url
            d["documentation_url"] = self.documentation_url
            d["created_by"] = self.created_by
            d["org_id"] = self.org_id
            d["created_at"] = self.created_at
            d["updated_at"] = self.updated_at
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class ConnectorAction(BaseModel):
    id: str
    connector_definition_id: str
    action_key: str
    name: str
    node_category: str
    cost_model: str
    rate_microcents: int
    is_active: bool
    sort_order: int
    description: Optional[str] = None
    category: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    unit_label: Optional[str] = None
    requires_enterprise: bool = False

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row_get(row, "id"),
            connector_definition_id=row_get(row, "connector_definition_id"),
            action_key=row_get(row, "action_key"),
            name=row_get(row, "name"),
            description=row_get(row, "description"),
            category=row_get(row, "category"),
            node_category=row_get(row, "node_category", "action"),
            input_schema=_json_field(row, "input_schema"),
            output_schema=_json_field(row, "output_schema"),
            cost_model=row_get(row, "cost_model", "per_execution"),
            rate_microcents=int(row_get(row, "rate_microcents", 0)),
            unit_label=row_get(row, "unit_label"),
            requires_enterprise=bool(row_get(row, "requires_enterprise", 0)),
            is_active=bool(row_get(row, "is_active", 1)),
            sort_order=int(row_get(row, "sort_order", 0)),
        )


@dataclass
class ConnectorInstance(BaseModel):
    id: str
    org_id: str
    connector_definition_id: str
    name: str
    status: str
    created_by: str
    created_at: str
    updated_at: str
    auth_method: Optional[str] = None
    kv_secret_key: Optional[str] = None
    instance_config: Optional[dict] = None
    last_tested_at: Optional[str] = None
    last_error: Optional[str] = None
    last_error_at: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row_get(row, "id"),
            org_id=row_get(row, "org_id"),
            connector_definition_id=row_get(row, "connector_definition_id"),
            name=row_get(row, "name"),
            auth_method=row_get(row, "auth_method"),
            kv_secret_key=row_get(row, "kv_secret_key"),
            instance_config=_json_field(row, "instance_config"),
            status=row_get(row, "status", "pending_auth"),
            last_tested_at=row_get(row, "last_tested_at"),
            last_error=row_get(row, "last_error"),
            last_error_at=row_get(row, "last_error_at"),
            created_by=row_get(row, "created_by"),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "connector_definition_id": self.connector_definition_id,
            "status": self.status,
            "created_at": self.created_at,
        }
        if scope == "admin":
            d["auth_method"] = self.auth_method
            d["instance_config"] = self.instance_config or {}
            d["last_tested_at"] = self.last_tested_at
            d["last_error"] = self.last_error
            d["created_by"] = self.created_by
            d["updated_at"] = self.updated_at
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class McpServer(BaseModel):
    id: str
    name: str
    transport: str
    status: str
    created_by: str
    created_at: str
    updated_at: str
    org_id: Optional[str] = None
    connector_definition_id: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list] = None
    tools_schema: Optional[list] = None
    resources_schema: Optional[list] = None
    prompts_schema: Optional[list] = None
    last_synced_at: Optional[str] = None
    last_error: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row_get(row, "id"),
            org_id=row_get(row, "org_id"),
            connector_definition_id=row_get(row, "connector_definition_id"),
            name=row_get(row, "name"),
            description=row_get(row, "description"),
            transport=row_get(row, "transport", "sse"),
            endpoint_url=row_get(row, "endpoint_url"),
            command=row_get(row, "command"),
            args=_json_field(row, "args", "[]"),
            tools_schema=_json_field(row, "tools_schema", "[]"),
            resources_schema=_json_field(row, "resources_schema", "[]"),
            prompts_schema=_json_field(row, "prompts_schema", "[]"),
            last_synced_at=row_get(row, "last_synced_at"),
            status=row_get(row, "status", "pending"),
            last_error=row_get(row, "last_error"),
            created_by=row_get(row, "created_by"),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
        )


@dataclass
class CustomAgent(BaseModel):
    id: str
    name: str
    agent_type: str
    model_provider: str
    model_id: str
    is_active: bool
    created_by: str
    created_at: str
    updated_at: str
    org_id: Optional[str] = None
    connector_definition_id: Optional[str] = None
    description: Optional[str] = None
    model_config_data: Optional[dict] = None
    system_prompt: Optional[str] = None
    tool_connector_action_ids: Optional[list] = None
    mcp_server_id: Optional[str] = None
    endpoint_url: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row_get(row, "id"),
            org_id=row_get(row, "org_id"),
            connector_definition_id=row_get(row, "connector_definition_id"),
            name=row_get(row, "name"),
            description=row_get(row, "description"),
            agent_type=row_get(row, "agent_type", "llm_chain"),
            model_provider=row_get(row, "model_provider", "cloudflare_ai"),
            model_id=row_get(row, "model_id", ""),
            model_config_data=_json_field(row, "model_config"),
            system_prompt=row_get(row, "system_prompt"),
            tool_connector_action_ids=_json_field(
                row, "tool_connector_action_ids", "[]"
            ),
            mcp_server_id=row_get(row, "mcp_server_id"),
            endpoint_url=row_get(row, "endpoint_url"),
            is_active=bool(row_get(row, "is_active", 1)),
            created_by=row_get(row, "created_by"),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
        )


@dataclass
class ConnectorMarketplaceListing(BaseModel):
    id: str
    connector_definition_id: str
    publisher_user_id: str
    listing_title: str
    short_description: str
    is_public: bool
    install_count: int
    star_count: int
    created_at: str
    publisher_org_id: Optional[str] = None
    long_description: Optional[str] = None
    tags: Optional[list] = None
    screenshot_urls: Optional[list] = None
    published_at: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row_get(row, "id"),
            connector_definition_id=row_get(row, "connector_definition_id"),
            publisher_org_id=row_get(row, "publisher_org_id"),
            publisher_user_id=row_get(row, "publisher_user_id"),
            listing_title=row_get(row, "listing_title"),
            short_description=row_get(row, "short_description"),
            long_description=row_get(row, "long_description"),
            tags=_json_field(row, "tags", "[]"),
            screenshot_urls=_json_field(row, "screenshot_urls", "[]"),
            is_public=bool(row_get(row, "is_public", 1)),
            install_count=int(row_get(row, "install_count", 0)),
            star_count=int(row_get(row, "star_count", 0)),
            published_at=row_get(row, "published_at"),
            created_at=row_get(row, "created_at", ""),
        )
