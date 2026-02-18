"""
Inference fallback wrapper.

Primary path: Real Azure OpenAI inference via Semantic Kernel.
Fallback path: Pre-computed responses from data/fallback_responses.json
— activated ONLY when inference fails (auth error, quota, timeout, etc.).
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from backend.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load fallback responses
# ---------------------------------------------------------------------------
_fallback_cache: dict[str, Any] | None = None


def _load_fallback_responses() -> dict[str, Any]:
    global _fallback_cache
    if _fallback_cache is not None:
        return _fallback_cache

    settings = get_settings()
    fallback_path = settings.resolved_data_dir / "fallback_responses.json"
    if fallback_path.exists():
        with open(fallback_path, "r", encoding="utf-8") as f:
            _fallback_cache = json.load(f)
        logger.info("Loaded fallback responses from %s", fallback_path)
    else:
        logger.warning("Fallback responses file not found at %s", fallback_path)
        _fallback_cache = {}
    return _fallback_cache


def get_fallback_response(agent_name: str, variant: str = "default") -> dict[str, Any]:
    """Get a pre-computed fallback response for an agent."""
    responses = _load_fallback_responses()
    agent_responses = responses.get(agent_name, {})
    return agent_responses.get(variant, agent_responses.get("default", {}))


# ---------------------------------------------------------------------------
# Inference wrapper
# ---------------------------------------------------------------------------
# Exceptions that trigger fallback
_FALLBACK_EXCEPTIONS = (
    ConnectionError,
    asyncio.TimeoutError,
    TimeoutError,
)


async def invoke_with_fallback(
    kernel,
    agent_name: str,
    prompt: str,
    *,
    fallback_variant: str = "default",
    timeout_seconds: float = 30.0,
    has_real_ai: bool = True,
) -> tuple[dict[str, Any], str]:
    """
    Invoke Semantic Kernel with real Azure OpenAI, falling back on failure.

    Returns:
        (result_dict, inference_mode) where inference_mode is "real" or "fallback"
    """
    if not has_real_ai:
        logger.info("[%s] No real AI configured — using fallback", agent_name)
        return get_fallback_response(agent_name, fallback_variant), "fallback"

    try:
        from semantic_kernel.contents import ChatHistory

        chat_history = ChatHistory()
        chat_history.add_system_message(
            "You are an AI agent in the LLPG Reactive Price Beat system for Dan Murphy's. "
            "Respond ONLY with valid JSON matching the expected output schema."
        )
        chat_history.add_user_message(prompt)

        result = await asyncio.wait_for(
            kernel.invoke_prompt(prompt=prompt),
            timeout=timeout_seconds,
        )

        # Parse result as JSON
        result_text = str(result)
        # Try to extract JSON from the response
        try:
            # Handle cases where model wraps JSON in markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            result_dict = json.loads(result_text)
        except json.JSONDecodeError:
            logger.warning("[%s] Could not parse AI response as JSON, wrapping as raw", agent_name)
            result_dict = {"raw_response": result_text}

        logger.info("[%s] Real inference succeeded", agent_name)
        return result_dict, "real"

    except _FALLBACK_EXCEPTIONS as e:
        logger.warning("[%s] Inference failed (%s: %s) — using fallback", agent_name, type(e).__name__, e)
        return get_fallback_response(agent_name, fallback_variant), "fallback"
    except Exception as e:
        # Catch Azure-specific errors (HttpResponseError, ServiceResponseException)
        error_name = type(e).__name__
        if error_name in ("HttpResponseError", "ServiceResponseException", "AuthenticationError"):
            logger.warning("[%s] Azure error (%s: %s) — using fallback", agent_name, error_name, e)
            return get_fallback_response(agent_name, fallback_variant), "fallback"
        # Re-raise unexpected errors
        logger.error("[%s] Unexpected error: %s", agent_name, e)
        return get_fallback_response(agent_name, fallback_variant), "fallback"
