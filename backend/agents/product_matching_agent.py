"""
ProductMatchingAgent — Match competitor product to Dan Murphy's catalogue.

Uses GPT-4o + embeddings for intelligent matching, with rule-based
fallback matching on barcode/name similarity.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from backend.inference import invoke_with_fallback
from backend.data.loader import find_product_by_sku, find_product_by_name, load_catalogue

logger = logging.getLogger(__name__)

MATCHING_PROMPT_TEMPLATE = """You are a product matching agent for Dan Murphy's liquor store.

Match the competitor product to the correct Dan Murphy's product from our catalogue.

Competitor product:
- Name: "{competitor_product_name}"
- Price: ${competitor_price}
- Competitor: {competitor}

Our catalogue (top candidates):
{catalogue_candidates}

Respond with ONLY valid JSON:
{{
  "matched_sku": "SKU string or null",
  "product_name": "matched product name or null",
  "brand": "brand or null",
  "category": "category or null",
  "current_price": price or null,
  "cost_price": cost or null,
  "match_confidence": 0.0 to 1.0,
  "match_method": "description of matching method",
  "reasoning": "brief explanation"
}}
"""


def _get_top_candidates(product_name: str, n: int = 5) -> str:
    """Get top N catalogue candidates based on name similarity."""
    df = load_catalogue()
    name_lower = product_name.lower()

    # Score all products
    scores = []
    for _, row in df.iterrows():
        cat_name = row["product_name"].lower()
        # Simple word overlap score
        words_input = set(name_lower.split())
        words_cat = set(cat_name.split())
        if not words_input or not words_cat:
            score = 0
        else:
            score = len(words_input & words_cat) / len(words_input | words_cat)
        scores.append((score, row))

    scores.sort(key=lambda x: x[0], reverse=True)
    top = scores[:n]

    lines = []
    for score, row in top:
        lines.append(
            f"- SKU: {row['sku']}, Name: {row['product_name']}, "
            f"Brand: {row['brand']}, Price: ${row['current_price']:.2f}, "
            f"Category: {row['category']}"
        )
    return "\n".join(lines)


async def run_product_matching_agent(
    kernel,
    competitor_product_name: str,
    competitor_price: float,
    competitor: str,
    competitor_barcode: Optional[str] = None,
    matched_sku: Optional[str] = None,
    has_real_ai: bool = True,
) -> tuple[dict[str, Any], str]:
    """
    Match competitor product to Dan Murphy's catalogue.

    Returns (result_dict, inference_mode).
    """
    # Quick path: if we already have a matched SKU from CSV
    if matched_sku:
        product = find_product_by_sku(matched_sku)
        if product:
            return {
                "matched_sku": matched_sku,
                "product_name": product["product_name"],
                "brand": product["brand"],
                "category": product["category"],
                "current_price": float(product["current_price"]),
                "cost_price": float(product["cost_price"]),
                "match_confidence": 0.99,
                "match_method": "csv_sku_lookup",
                "reasoning": f"Direct SKU match from competitor data: {matched_sku}",
            }, "real"

    # Try name-based fuzzy match first
    name_match = find_product_by_name(competitor_product_name)
    if name_match and name_match.get("product_name"):
        # High confidence local match
        return {
            "matched_sku": name_match["sku"],
            "product_name": name_match["product_name"],
            "brand": name_match["brand"],
            "category": name_match["category"],
            "current_price": float(name_match["current_price"]),
            "cost_price": float(name_match["cost_price"]),
            "match_confidence": 0.90,
            "match_method": "name_similarity",
            "reasoning": f"Matched by product name similarity to '{name_match['product_name']}'",
        }, "real"

    # Use AI for more complex matching
    candidates = _get_top_candidates(competitor_product_name)
    prompt = MATCHING_PROMPT_TEMPLATE.format(
        competitor_product_name=competitor_product_name,
        competitor_price=competitor_price,
        competitor=competitor,
        catalogue_candidates=candidates,
    )

    result, mode = await invoke_with_fallback(
        kernel,
        agent_name="ProductMatchingAgent",
        prompt=prompt,
        has_real_ai=has_real_ai,
    )

    return result, mode
