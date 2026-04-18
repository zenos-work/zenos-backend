"""
Tests for Phase 13 - Step 49: GenAI Node Definitions and Execution
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api.workflows.genai_nodes import (
    GenAINodeRegistry,
    GenAIProvider,
    AccessControlValidator,
    validate_genai_node_inputs,
    estimate_cost,
)
from api.workflows.genai_executor import GenAIExecutor


class TestGenAINodeRegistry:
    """Test GenAI node type registry"""

    def test_get_node_exists(self):
        """Retrieve an existing node config"""
        node = GenAINodeRegistry.get_node("genai_summarize")
        assert node is not None
        assert node.node_type == "genai_summarize"
        assert node.display_name == "Summarize"
        assert node.provider == GenAIProvider.OPENAI
        assert node.min_tier == "pro"
        assert node.requires_addon is True

    def test_get_node_not_exists(self):
        """Attempt to retrieve a non-existent node"""
        node = GenAINodeRegistry.get_node("genai_nonexistent")
        assert node is None

    def test_list_nodes(self):
        """List all available GenAI node types"""
        nodes = GenAINodeRegistry.list_nodes()
        assert len(nodes) == 8
        node_types = {n.node_type for n in nodes}
        assert "genai_summarize" in node_types
        assert "genai_translate" in node_types
        assert "genai_repurpose" in node_types

    def test_get_nodes_for_tier(self):
        """Filter nodes by tier"""
        pro_nodes = GenAINodeRegistry.get_nodes_for_tier("pro")
        assert len(pro_nodes) > 0
        starter_nodes = GenAINodeRegistry.get_nodes_for_tier("starter")
        # All nodes require pro tier or above
        assert len(starter_nodes) == 0

    def test_node_config_structure(self):
        """Verify node config has required fields"""
        node = GenAINodeRegistry.get_node("genai_translate")
        assert node.node_type == "genai_translate"
        assert node.display_name
        assert node.description
        assert node.provider
        assert node.model
        assert node.input_fields
        assert node.output_fields
        assert node.system_prompt
        assert node.cost_per_1k_input_tokens_microcents >= 0
        assert node.cost_per_1k_output_tokens_microcents >= 0


class TestGenAINodeValidation:
    """Test input validation for GenAI nodes"""

    def test_valid_inputs(self):
        """Validate correct inputs"""
        is_valid, error = validate_genai_node_inputs(
            "genai_translate", {"text": "Hello", "target_language": "Spanish"}
        )
        assert is_valid is True
        assert error is None

    def test_missing_required_input(self):
        """Fail on missing required field"""
        is_valid, error = validate_genai_node_inputs(
            "genai_translate", {"text": "Hello"}
        )
        assert is_valid is False
        assert "target_language" in error

    def test_unknown_node_type(self):
        """Fail on unknown node type"""
        is_valid, error = validate_genai_node_inputs("genai_unknown", {"text": "Hello"})
        assert is_valid is False
        assert "Unknown" in error

    def test_summarize_inputs(self):
        """Validate summarize node inputs"""
        is_valid, error = validate_genai_node_inputs(
            "genai_summarize", {"text": "Long text...", "length": "short"}
        )
        assert is_valid is True


class TestCostEstimation:
    """Test GenAI cost estimation"""

    def test_estimate_cost_summarize(self):
        """Calculate cost for summarize node"""
        cost = estimate_cost("genai_summarize", 1000, 200)
        assert cost is not None
        assert cost > 0
        # 1000 tokens input @ 150 microcents/1k = 150
        # 200 tokens output @ 200 microcents/1k = 40
        # Total = 190 microcents
        assert cost == 190

    def test_estimate_cost_expensive_node(self):
        """Calculate cost for expensive (GPT-4) node"""
        cost = estimate_cost("genai_repurpose", 1000, 1000)
        assert cost is not None
        # GPT-4: 300 + 600 = 900 microcents
        assert cost > 500  # GPT-4 is expensive

    def test_estimate_cost_unknown_node(self):
        """Request cost for unknown node"""
        cost = estimate_cost("genai_unknown", 100, 100)
        assert cost is None


class TestAccessControlValidator:
    """Test access control for GenAI nodes"""

    def test_enterprise_can_access_all(self):
        """Enterprise tier can access all nodes"""
        can_access, reason = AccessControlValidator.can_access_node(
            "enterprise", ["workflow_builder"], "genai_translate"
        )
        assert can_access is True
        assert reason is None

    def test_pro_can_access_pro_nodes(self):
        """Pro tier can access pro-tier nodes"""
        can_access, reason = AccessControlValidator.can_access_node(
            "pro", ["workflow_builder"], "genai_translate"
        )
        assert can_access is True

    def test_starter_cannot_access_pro_nodes(self):
        """Starter tier cannot access pro-tier nodes"""
        can_access, reason = AccessControlValidator.can_access_node(
            "starter", ["workflow_builder"], "genai_translate"
        )
        assert can_access is False
        assert "pro" in reason.lower()

    def test_missing_addon_denied(self):
        """Node requires workflow_builder add-on"""
        can_access, reason = AccessControlValidator.can_access_node(
            "enterprise",
            [],  # No add-ons
            "genai_translate",
        )
        assert can_access is False
        assert "workflow_builder" in reason

    def test_unknown_node_type(self):
        """Check access for non-existent node"""
        can_access, reason = AccessControlValidator.can_access_node(
            "pro", ["workflow_builder"], "genai_unknown"
        )
        assert can_access is False
        assert "Unknown" in reason


class TestGenAIExecutor:
    """Test GenAI executor"""

    @pytest.mark.asyncio
    async def test_execute_with_invalid_node_type(self):
        """Executor rejects unknown node type"""
        ctx = AsyncMock()
        db = AsyncMock()
        executor = GenAIExecutor(ctx, db)

        result = await executor.execute(
            "genai_unknown", {"text": "hello"}, {"openai": "sk-..."}
        )

        assert result.success is False
        assert "Unknown" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_invalid_inputs(self):
        """Executor validates inputs"""
        ctx = AsyncMock()
        db = AsyncMock()
        executor = GenAIExecutor(ctx, db)

        result = await executor.execute(
            "genai_translate",
            {"text": "hello"},  # Missing target_language
            {"openai": "sk-..."},
        )

        assert result.success is False
        assert "target_language" in result.error

    @pytest.mark.asyncio
    async def test_execute_missing_api_key(self):
        """Executor requires API key for provider"""
        ctx = AsyncMock()
        db = AsyncMock()
        executor = GenAIExecutor(ctx, db)

        result = await executor.execute(
            "genai_translate",
            {"text": "hello", "target_language": "Spanish"},
            {},  # No credentials
        )

        assert result.success is False
        assert "API key" in result.error or "credential" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_openai_success(self):
        """Successful OpenAI execution"""
        ctx = AsyncMock()
        db = AsyncMock()
        executor = GenAIExecutor(ctx, db)

        # Mock OpenAI response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value=json.dumps(
                {
                    "choices": [{"message": {"content": "Summary text"}}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50},
                }
            )
        )
        ctx.fetch = AsyncMock(return_value=mock_response)

        result = await executor.execute(
            "genai_summarize",
            {"text": "Long article text...", "length": "short"},
            {"openai": "sk-test"},
        )

        assert result.success is True
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.cost_microcents > 0
        assert result.provider == "openai"
        assert result.model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_log_usage_on_success(self):
        """Usage is logged when execution succeeds"""
        ctx = AsyncMock()
        db = AsyncMock()

        # Mock prepare chain with sync prepare/bind and async run.
        mock_bind = MagicMock()
        mock_bind.run = AsyncMock()
        mock_prepare_obj = MagicMock()
        mock_prepare_obj.bind = MagicMock(return_value=mock_bind)
        db.prepare = MagicMock(return_value=mock_prepare_obj)

        executor = GenAIExecutor(ctx, db)

        # Mock OpenAI response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value=json.dumps(
                {
                    "choices": [{"message": {"content": "Response"}}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50},
                }
            )
        )
        ctx.fetch = AsyncMock(return_value=mock_response)

        result = await executor.execute(
            "genai_summarize",
            {"text": "Text", "length": "short"},
            {"openai": "sk-test"},
            workflow_run_id="run-123",
            step_id="step-1",
        )

        assert result.success is True
        # Verify prepare was called (usage was logged)
        assert db.prepare.called

    @pytest.mark.asyncio
    async def test_execution_time_tracking(self):
        """Execution time is measured"""
        ctx = AsyncMock()
        db = AsyncMock()
        executor = GenAIExecutor(ctx, db)

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value=json.dumps(
                {
                    "choices": [{"message": {"content": "Result"}}],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 25},
                }
            )
        )
        ctx.fetch = AsyncMock(return_value=mock_response)

        result = await executor.execute(
            "genai_summarize",
            {"text": "Text", "length": "short"},
            {"openai": "sk-test"},
        )

        assert result.success is True
        assert result.execution_time_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
