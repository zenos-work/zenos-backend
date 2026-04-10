"""
Phase 13 - Step 49: GenAI Executor
Handles execution of GenAI nodes with provider abstraction and cost tracking.
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from .genai_nodes import (
    GenAINodeRegistry,
    GenAIProvider,
    estimate_cost,
    validate_genai_node_inputs,
)


@dataclass
class GenAIExecutionResult:
    """Result of executing a GenAI node"""

    success: bool
    output: Optional[Dict[str, Any]] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_microcents: int = 0
    provider: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    raw_response: Optional[str] = None


class GenAIExecutor:
    """Executes GenAI node types with various providers"""

    def __init__(self, ctx: Any, db: Any):
        """
        Initialize executor with Workers context and DB connection.

        Args:
            ctx: Cloudflare Workers request context
            db: D1 database connection
        """
        self.ctx = ctx
        self.db = db
        self.registry = GenAINodeRegistry()

    async def execute(
        self,
        node_type: str,
        inputs: Dict[str, Any],
        org_vault_credentials: Optional[Dict[str, str]] = None,
        workflow_run_id: Optional[str] = None,
        step_id: Optional[str] = None,
    ) -> GenAIExecutionResult:
        """
        Execute a GenAI node.

        Args:
            node_type: Type of GenAI node to execute
            inputs: Input parameters for the node
            org_vault_credentials: Vault credentials for this org (API keys, etc.)
            workflow_run_id: ID of the workflow run (for cost attribution)
            step_id: ID of the workflow step

        Returns:
            GenAIExecutionResult with output, tokens, cost, etc.
        """
        import time

        start_time = time.time()

        # Validate inputs
        is_valid, error = validate_genai_node_inputs(node_type, inputs)
        if not is_valid:
            return GenAIExecutionResult(
                success=False,
                error=error,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Get node config
        node = self.registry.get_node(node_type)
        if not node:
            return GenAIExecutionResult(
                success=False,
                error=f"Unknown node type: {node_type}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Check credentials
        if (
            not org_vault_credentials
            or node.provider.value not in org_vault_credentials
        ):
            return GenAIExecutionResult(
                success=False,
                error=f"Missing API key for provider: {node.provider.value}. Configure in org vault.",
                provider=node.provider.value,
                model=node.model.value,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Route to appropriate provider
        if node.provider == GenAIProvider.OPENAI:
            result = await self._execute_openai(node, inputs, org_vault_credentials)
        elif node.provider == GenAIProvider.DEEPL:
            result = await self._execute_deepl(node, inputs, org_vault_credentials)
        elif node.provider == GenAIProvider.ANTHROPIC:
            result = await self._execute_anthropic(node, inputs, org_vault_credentials)
        else:
            result = GenAIExecutionResult(
                success=False, error=f"Unsupported provider: {node.provider.value}"
            )

        result.execution_time_ms = (time.time() - start_time) * 1000
        result.provider = node.provider.value
        result.model = node.model.value

        # Log cost and usage if execution was successful
        if result.success and workflow_run_id:
            await self._log_usage(
                workflow_run_id=workflow_run_id,
                step_id=step_id,
                node_type=node_type,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_microcents=result.cost_microcents,
                provider=result.provider,
                model=result.model,
            )

        return result

    async def _execute_openai(
        self, node: Any, inputs: Dict[str, Any], vault_credentials: Dict[str, str]
    ) -> GenAIExecutionResult:
        """Execute via OpenAI API"""
        try:
            api_key = vault_credentials.get("openai")
            if not api_key:
                return GenAIExecutionResult(
                    success=False, error="OpenAI API key not configured"
                )

            # Build prompt from node config and inputs
            prompt = self._build_prompt(node, inputs)

            # Call OpenAI API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": node.model.value,
                "messages": [
                    {"role": "system", "content": node.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": node.default_temperature,
                "max_tokens": node.max_tokens,
            }

            # Use Workers fetch API
            response = await self.ctx.fetch(
                "https://api.openai.com/v1/chat/completions",
                {"method": "POST", "headers": headers, "body": json.dumps(payload)},
            )

            response_text = await response.text()

            if response.status != 200:
                return GenAIExecutionResult(
                    success=False,
                    error=f"OpenAI API error: {response.status} - {response_text}",
                    raw_response=response_text,
                )

            response_json = json.loads(response_text)

            # Extract token usage and content
            usage = response_json.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            content = (
                response_json.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            # Parse output
            output = self._parse_node_output(node.node_type, content)
            cost = estimate_cost(node.node_type, input_tokens, output_tokens) or 0

            return GenAIExecutionResult(
                success=True,
                output=output,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_microcents=cost,
                raw_response=response_text,
            )

        except Exception as e:
            return GenAIExecutionResult(
                success=False, error=f"OpenAI execution error: {str(e)}"
            )

    async def _execute_deepl(
        self, node: Any, inputs: Dict[str, Any], vault_credentials: Dict[str, str]
    ) -> GenAIExecutionResult:
        """Execute via DeepL API"""
        try:
            api_key = vault_credentials.get("deepl")
            if not api_key:
                return GenAIExecutionResult(
                    success=False, error="DeepL API key not configured"
                )

            text = inputs.get("text", "")
            target_lang = inputs.get("target_language", "EN")

            headers = {
                "Authorization": f"DeepL-Auth-Key {api_key}",
                "Content-Type": "application/json",
            }

            payload = {"text": [text], "target_lang": target_lang.upper()}

            response = await self.ctx.fetch(
                "https://api-free.deepl.com/v1/document",
                {"method": "POST", "headers": headers, "body": json.dumps(payload)},
            )

            response_text = await response.text()

            if response.status != 200:
                return GenAIExecutionResult(
                    success=False,
                    error=f"DeepL API error: {response.status} - {response_text}",
                )

            response_json = json.loads(response_text)
            translations = response_json.get("translations", [{}])
            translated_text = translations[0].get("text", "") if translations else ""

            # Estimate tokens (rough approximation: ~4 chars per token)
            input_tokens = len(text) // 4
            output_tokens = len(translated_text) // 4
            cost = estimate_cost(node.node_type, input_tokens, output_tokens) or 0

            output = {"translated_text": translated_text}

            return GenAIExecutionResult(
                success=True,
                output=output,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_microcents=cost,
            )

        except Exception as e:
            return GenAIExecutionResult(
                success=False, error=f"DeepL execution error: {str(e)}"
            )

    async def _execute_anthropic(
        self, node: Any, inputs: Dict[str, Any], vault_credentials: Dict[str, str]
    ) -> GenAIExecutionResult:
        """Execute via Anthropic API"""
        try:
            api_key = vault_credentials.get("anthropic")
            if not api_key:
                return GenAIExecutionResult(
                    success=False, error="Anthropic API key not configured"
                )

            prompt = self._build_prompt(node, inputs)

            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            payload = {
                "model": node.model.value,
                "max_tokens": node.max_tokens or 1024,
                "system": node.system_prompt,
                "messages": [{"role": "user", "content": prompt}],
            }

            response = await self.ctx.fetch(
                "https://api.anthropic.com/v1/messages",
                {"method": "POST", "headers": headers, "body": json.dumps(payload)},
            )

            response_text = await response.text()

            if response.status != 200:
                return GenAIExecutionResult(
                    success=False,
                    error=f"Anthropic API error: {response.status} - {response_text}",
                )

            response_json = json.loads(response_text)
            usage = response_json.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            content = response_json.get("content", [{}])[0].get("text", "")

            output = self._parse_node_output(node.node_type, content)
            cost = estimate_cost(node.node_type, input_tokens, output_tokens) or 0

            return GenAIExecutionResult(
                success=True,
                output=output,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_microcents=cost,
            )

        except Exception as e:
            return GenAIExecutionResult(
                success=False, error=f"Anthropic execution error: {str(e)}"
            )

    def _build_prompt(self, node: Any, inputs: Dict[str, Any]) -> str:
        """Build execution prompt from node config and inputs"""
        prompt_parts = []

        for field_name, field_value in inputs.items():
            if field_name not in ["text", "content", "article_content"]:
                prompt_parts.append(f"{field_name}: {field_value}")

        # Add main text content
        for key in ["text", "content", "article_content", "article_title"]:
            if key in inputs:
                prompt_parts.append(f"\n\n{key}:\n{inputs[key]}")

        return "\n".join(prompt_parts)

    def _parse_node_output(self, node_type: str, content: str) -> Dict[str, Any]:
        """Parse and structure output based on node type"""
        try:
            # Try to parse as JSON for structured nodes
            if node_type in [
                "genai_extract_entities",
                "genai_generate_tags",
                "genai_content_moderate",
                "genai_seo_optimize",
            ]:
                # Clean up response if it contains markdown code blocks
                if "```" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start >= 0 and end > start:
                        content = content[start:end]
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pass

        # Return as-is for text nodes
        node = GenAINodeRegistry.get_node(node_type)
        if node:
            output_fields = list(node.output_fields.keys())
            if output_fields:
                return {output_fields[0]: content}

        return {"output": content}

    async def _log_usage(
        self,
        workflow_run_id: str,
        step_id: Optional[str],
        node_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_microcents: int,
        provider: str,
        model: str,
    ) -> None:
        """Log GenAI usage to workflow_run_costs table"""
        try:
            # Check if workflow_run_costs table exists
            insert_query = """
                INSERT INTO workflow_run_costs (
                    workflow_run_id, step_id, node_type,
                    input_tokens, output_tokens, total_cost_microcents,
                    provider, model, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            await (
                self.db.prepare(insert_query)
                .bind(
                    workflow_run_id,
                    step_id,
                    node_type,
                    input_tokens,
                    output_tokens,
                    cost_microcents,
                    provider,
                    model,
                    datetime.now(timezone.utc).isoformat(),
                )
                .run()
            )
        except Exception as e:
            # Log but don't fail if cost logging fails
            print(f"Failed to log GenAI usage: {str(e)}")
