"""
DecisionAgent — Final pricing decision with natural language explanation.

Uses GPT-4o to generate a customer-friendly response based on the
LLPG rule evaluation results.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.inference import invoke_with_fallback

logger = logging.getLogger(__name__)

DECISION_PROMPT_TEMPLATE = """You are the Decision Agent for Dan Murphy's Lowest Liquor Price Guarantee (LLPG).

Based on the rule evaluation below, generate a friendly customer-facing response.

Rule Evaluation:
{rule_evaluation}

Product: {product_name}
Competitor: {competitor}
Our Price: ${own_price}
Competitor Price: ${competitor_price}
Beat Price: {beat_price}
Decision: {decision}

Generate a JSON response:
{{
  "decision": "{decision}",
  "message": "customer-friendly message explaining the decision",
  "beat_price": beat price or null,
  "original_price": our current price,
  "saving": saving amount or null,
  "competitor": "{competitor}",
  "product_name": "{product_name}",
  "reasoning": "internal reasoning for audit"
}}

Guidelines:
- If APPROVED: Be enthusiastic, highlight the saving, mention the new price
- If SENT_TO_REVIEW: Be reassuring, explain a team member will review
- If REJECTED: Be empathetic, suggest alternatives, don't mention specific policy details
- Keep the tone friendly and professional (Dan Murphy's brand voice)
"""


async def run_decision_agent(
    kernel,
    rule_result: dict[str, Any],
    product_name: str,
    competitor: str,
    own_price: float,
    competitor_price: float,
    has_real_ai: bool = True,
) -> tuple[dict[str, Any], str]:
    """
    Generate final decision with customer-friendly message.

    Returns (result_dict, inference_mode).
    """
    decision = rule_result.get("decision", "AUTO_REJECT")
    beat_price = rule_result.get("beat_price")

    # Map decision to fallback variant
    if decision == "AUTO_APPROVE":
        fallback_variant = "approved"
    elif decision == "SEND_TO_REVIEW":
        fallback_variant = "sent_to_review"
    else:
        fallback_variant = "rejected"

    beat_price_str = f"${beat_price:.2f}" if beat_price else "N/A"

    prompt = DECISION_PROMPT_TEMPLATE.format(
        rule_evaluation=json.dumps(rule_result, indent=2),
        product_name=product_name,
        competitor=competitor,
        own_price=f"{own_price:.2f}",
        competitor_price=f"{competitor_price:.2f}",
        beat_price=beat_price_str,
        decision=decision,
    )

    result, mode = await invoke_with_fallback(
        kernel,
        agent_name="DecisionAgent",
        prompt=prompt,
        fallback_variant=fallback_variant,
        has_real_ai=has_real_ai,
    )

    # Ensure required fields with actual values
    if result.get("beat_price") is None and beat_price:
        result["beat_price"] = beat_price
    if result.get("original_price") is None:
        result["original_price"] = own_price
    if not result.get("competitor"):
        result["competitor"] = competitor
    if not result.get("product_name"):
        result["product_name"] = product_name
    if beat_price is not None and own_price is not None:
        result["saving"] = round(own_price - beat_price, 2)

    # Generate a default message if AI didn't provide one
    if not result.get("message"):
        if decision == "AUTO_APPROVE":
            if beat_price is not None:
                result["message"] = (
                    f"Great news! We can beat that price. Our new price for "
                    f"{product_name} will be ${beat_price:.2f} — "
                    f"saving you ${own_price - beat_price:.2f}!"
                )
            else:
                result["message"] = (
                    f"Great news! We can beat that price for {product_name}. "
                    f"Your price has been updated."
                )
        elif decision == "SEND_TO_REVIEW":
            result["message"] = (
                f"Thanks for letting us know! The price difference is significant, "
                f"so our team will review this and get back to you within 24 hours."
            )
        else:
            result["message"] = (
                f"I'm sorry, but we're unable to match that price at this time. "
                f"Can I help you find something else from our great range?"
            )

    return result, mode
