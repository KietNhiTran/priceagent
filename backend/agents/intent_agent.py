"""
IntentAgent — Detect LLPG price-beat intent from user message.

Uses GPT-4o to classify user intent and extract entities.
Falls back to pre-computed response on inference failure.
"""

from __future__ import annotations

import json
import re
import logging
from typing import Any

from backend.inference import invoke_with_fallback

logger = logging.getLogger(__name__)

INTENT_PROMPT_TEMPLATE = """Analyze the following customer message and determine if it's a Lowest Liquor Price Guarantee (LLPG) price-beat request.

Customer message: "{message}"

Extract the following information and respond with ONLY valid JSON:
{{
  "intent": "llpg_price_beat" or "general_inquiry",
  "confidence": 0.0 to 1.0,
  "entities": {{
    "competitor": "competitor name or null",
    "product_name": "product name or null",
    "competitor_price": price as number or null,
    "competitor_url": "URL or null"
  }},
  "reasoning": "brief explanation"
}}

LLPG indicators: mentions cheaper price elsewhere, competitor name (Liquorland, BoozeBud, First Choice), price comparison, "beat this price", "match this price", screenshot of competitor price, URL to competitor product page.
"""


async def run_intent_agent(
    kernel,
    message: str,
    has_real_ai: bool = True,
) -> tuple[dict[str, Any], str]:
    """
    Detect LLPG intent from user message.

    Returns (result_dict, inference_mode).
    """
    # Quick rule-based pre-check for obvious LLPG keywords
    llpg_keywords = [
        "cheaper", "lower price", "beat", "match", "price guarantee",
        "liquorland", "boozebud", "first choice", "found it for",
        "competitor", "better price", "price beat",
    ]
    message_lower = message.lower()
    has_keyword = any(kw in message_lower for kw in llpg_keywords)

    # Extract URL if present
    url_match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+', message)
    extracted_url = url_match.group(0) if url_match else None

    # Extract price if present (e.g., $48.99, 48.99)
    price_match = re.search(r'\$?(\d+\.?\d*)', message)
    extracted_price = float(price_match.group(1)) if price_match else None

    # Try real AI inference
    prompt = INTENT_PROMPT_TEMPLATE.format(message=message)

    # Choose fallback variant
    fallback_variant = "default" if has_keyword else "no_intent"

    result, mode = await invoke_with_fallback(
        kernel,
        agent_name="IntentAgent",
        prompt=prompt,
        fallback_variant=fallback_variant,
        has_real_ai=has_real_ai,
    )

    # Enrich with extracted entities if AI didn't catch them
    if result.get("entities"):
        if extracted_url and not result["entities"].get("competitor_url"):
            result["entities"]["competitor_url"] = extracted_url
        if extracted_price and not result["entities"].get("competitor_price"):
            result["entities"]["competitor_price"] = extracted_price

    return result, mode
