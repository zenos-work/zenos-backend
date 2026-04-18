"""
Phase 13 - Step 49: GenAI Node Type Definitions
Defines pre-built GenAI transformer nodes (Summarize, Translate, etc.)
with cost tracking for metering and access controls.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class GenAIProvider(str, Enum):
    """Supported GenAI providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPL = "deepl"
    CUSTOM = "custom"


class GenAIModel(str, Enum):
    """Supported GenAI models per provider"""

    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    DEEPL_PRO = "deepl-pro"


@dataclass
class GenAINodeConfig:
    """Configuration for a pre-built GenAI node type"""

    node_type: str
    display_name: str
    description: str
    provider: GenAIProvider
    model: GenAIModel
    input_fields: Dict[str, str]  # field_name -> type
    output_fields: Dict[str, str]  # field_name -> type
    system_prompt: str
    default_temperature: float = 0.7
    max_tokens: Optional[int] = None
    cost_per_1k_input_tokens_microcents: int = 0
    cost_per_1k_output_tokens_microcents: int = 0
    requires_addon: bool = True
    min_tier: str = "pro"  # free, starter, business, enterprise
    requires_api_key: bool = True


class GenAINodeRegistry:
    """Registry of pre-defined GenAI node types"""

    NODES = {
        "genai_summarize": GenAINodeConfig(
            node_type="genai_summarize",
            display_name="Summarize",
            description="Generate a concise summary of long text",
            provider=GenAIProvider.OPENAI,
            model=GenAIModel.GPT_35_TURBO,
            input_fields={"text": "string", "length": "enum:short|medium|long"},
            output_fields={"summary": "string", "word_count": "integer"},
            system_prompt="You are an expert summarizer. Create clear, concise summaries that capture the key points.",
            default_temperature=0.5,
            max_tokens=500,
            cost_per_1k_input_tokens_microcents=150,
            cost_per_1k_output_tokens_microcents=200,
        ),
        "genai_translate": GenAINodeConfig(
            node_type="genai_translate",
            display_name="Translate",
            description="Translate text to a target language",
            provider=GenAIProvider.DEEPL,
            model=GenAIModel.DEEPL_PRO,
            input_fields={"text": "string", "target_language": "string"},
            output_fields={"translated_text": "string"},
            system_prompt="You are an expert translator. Maintain tone, style, and meaning.",
            default_temperature=0.3,
            cost_per_1k_input_tokens_microcents=100,
            cost_per_1k_output_tokens_microcents=150,
        ),
        "genai_rewrite_tone": GenAINodeConfig(
            node_type="genai_rewrite_tone",
            display_name="Rewrite Tone",
            description="Rewrite text in a specific tone",
            provider=GenAIProvider.OPENAI,
            model=GenAIModel.GPT_35_TURBO,
            input_fields={
                "text": "string",
                "tone": "enum:formal|casual|technical|friendly",
            },
            output_fields={"rewritten_text": "string"},
            system_prompt="You are an expert writer. Rewrite text maintaining the same meaning but adjusting the tone.",
            default_temperature=0.7,
            max_tokens=None,
            cost_per_1k_input_tokens_microcents=150,
            cost_per_1k_output_tokens_microcents=200,
        ),
        "genai_extract_entities": GenAINodeConfig(
            node_type="genai_extract_entities",
            display_name="Extract Entities",
            description="Extract named entities from text (people, organizations, dates, etc.)",
            provider=GenAIProvider.OPENAI,
            model=GenAIModel.GPT_35_TURBO,
            input_fields={"text": "string"},
            output_fields={"entities": "object", "count": "integer"},
            system_prompt="Extract all named entities. Return as JSON with categories: people, organizations, locations, dates.",
            default_temperature=0.3,
            max_tokens=1000,
            cost_per_1k_input_tokens_microcents=150,
            cost_per_1k_output_tokens_microcents=200,
        ),
        "genai_generate_tags": GenAINodeConfig(
            node_type="genai_generate_tags",
            display_name="Generate Tags",
            description="Suggest relevant tags for article content",
            provider=GenAIProvider.OPENAI,
            model=GenAIModel.GPT_35_TURBO,
            input_fields={
                "title": "string",
                "content": "string",
                "existing_tags": "array",
            },
            output_fields={"suggested_tags": "array", "confidence_scores": "object"},
            system_prompt="Generate 5-10 relevant, SEO-friendly tags for the given content. Return as JSON array.",
            default_temperature=0.6,
            max_tokens=200,
            cost_per_1k_input_tokens_microcents=150,
            cost_per_1k_output_tokens_microcents=200,
        ),
        "genai_content_moderate": GenAINodeConfig(
            node_type="genai_content_moderate",
            display_name="Content Moderation",
            description="Check content for safety and policy violations",
            provider=GenAIProvider.OPENAI,
            model=GenAIModel.GPT_35_TURBO,
            input_fields={"text": "string"},
            output_fields={
                "safety_score": "float",
                "flags": "array",
                "category": "string",
            },
            system_prompt="Analyze content for safety. Return JSON with safety_score (0-100), flags array, and category.",
            default_temperature=0.3,
            max_tokens=500,
            cost_per_1k_input_tokens_microcents=150,
            cost_per_1k_output_tokens_microcents=200,
        ),
        "genai_seo_optimize": GenAINodeConfig(
            node_type="genai_seo_optimize",
            display_name="SEO Optimize",
            description="Generate SEO suggestions and optimized metadata",
            provider=GenAIProvider.OPENAI,
            model=GenAIModel.GPT_35_TURBO,
            input_fields={
                "title": "string",
                "content": "string",
                "target_keyword": "string",
            },
            output_fields={
                "seo_suggestions": "array",
                "meta_title": "string",
                "meta_description": "string",
            },
            system_prompt="Provide SEO optimization suggestions. Return JSON with suggestions array, optimized meta_title, and meta_description.",
            default_temperature=0.6,
            max_tokens=1000,
            cost_per_1k_input_tokens_microcents=150,
            cost_per_1k_output_tokens_microcents=200,
        ),
        "genai_repurpose": GenAINodeConfig(
            node_type="genai_repurpose",
            display_name="Repurpose Content",
            description="Transform article into multiple formats (tweets, LinkedIn, etc.)",
            provider=GenAIProvider.OPENAI,
            model=GenAIModel.GPT_4,
            input_fields={
                "article_title": "string",
                "article_content": "string",
                "format": "enum:tweet|linkedin|email|podcast_script",
            },
            output_fields={"repurposed_content": "string"},
            system_prompt="Transform the article content into the specified format while maintaining key messages.",
            default_temperature=0.7,
            max_tokens=1500,
            cost_per_1k_input_tokens_microcents=300,
            cost_per_1k_output_tokens_microcents=600,
        ),
    }

    @classmethod
    def get_node(cls, node_type: str) -> Optional[GenAINodeConfig]:
        """Retrieve a node configuration by type"""
        return cls.NODES.get(node_type)

    @classmethod
    def list_nodes(cls) -> List[GenAINodeConfig]:
        """List all available GenAI node types"""
        return list(cls.NODES.values())

    @classmethod
    def get_nodes_for_tier(cls, tier: str) -> List[GenAINodeConfig]:
        """Filter nodes available for a given tier"""
        return [
            node
            for node in cls.NODES.values()
            if node.min_tier == tier or tier == "enterprise"
        ]


def validate_genai_node_inputs(
    node_type: str, inputs: Dict[str, Any]
) -> tuple[bool, Optional[str]]:
    """
    Validate that input matches a GenAI node's expected fields.

    Returns (is_valid, error_message)
    """
    node = GenAINodeRegistry.get_node(node_type)

    if not node:
        return False, f"Unknown node type: {node_type}"

    for field_name, field_type in node.input_fields.items():
        if field_name not in inputs:
            return False, f"Missing required input field: {field_name}"

    return True, None


def estimate_cost(
    node_type: str, input_tokens: int, output_tokens: int
) -> Optional[int]:
    """
    Estimate the cost of running a GenAI node in microcents.

    Args:
        node_type: The GenAI node type
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in microcents, or None if node not found
    """
    node = GenAINodeRegistry.get_node(node_type)

    if not node:
        return None

    input_cost = (input_tokens / 1000) * node.cost_per_1k_input_tokens_microcents
    output_cost = (output_tokens / 1000) * node.cost_per_1k_output_tokens_microcents

    return int(round(input_cost + output_cost))


class AccessControlValidator:
    """Validate access to GenAI nodes based on tier and add-ons"""

    @staticmethod
    def can_access_node(
        user_tier: str, org_add_ons: List[str], node_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can access a GenAI node.

        Returns (can_access, reason_if_denied)
        """
        node = GenAINodeRegistry.get_node(node_type)

        if not node:
            return False, f"Unknown node type: {node_type}"

        # Check tier requirement
        tier_order = ["free", "starter", "business", "pro", "enterprise"]
        user_tier_idx = tier_order.index(user_tier) if user_tier in tier_order else -1
        node_tier_idx = (
            tier_order.index(node.min_tier) if node.min_tier in tier_order else 3
        )

        if user_tier_idx < node_tier_idx:
            return False, f"GenAI nodes require {node.min_tier} tier or above"

        # Check add-on requirement
        if node.requires_addon and "workflow_builder" not in org_add_ons:
            return False, "GenAI nodes require 'workflow_builder' add-on"

        return True, None
