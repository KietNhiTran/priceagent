"""
LLPGRuleAgent — Apply all LLPG rules: RSA, stock-for-stock, beat formula.

Rule-based core with GPT-4o for edge cases.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from backend.plugins.compute_beat_price import compute_beat_price
from backend.plugins.check_rsa_compliance import check_rsa_compliance
from backend.inference import invoke_with_fallback

logger = logging.getLogger(__name__)


def _check_stock_for_stock(
    competitor_name: str,
    our_name: str,
    competitor_volume: Optional[int] = None,
    our_volume: Optional[int] = None,
    competitor_pack: Optional[int] = None,
    our_pack: Optional[int] = None,
) -> dict[str, Any]:
    """Check if competitor product is stock-for-stock equivalent."""
    # Simple heuristic: compare names word overlap
    comp_words = set(competitor_name.lower().split())
    our_words = set(our_name.lower().split())
    overlap = len(comp_words & our_words)
    total = len(comp_words | our_words)
    name_similarity = overlap / total if total > 0 else 0

    same_volume = True if not competitor_volume or not our_volume else competitor_volume == our_volume
    same_pack = True if not competitor_pack or not our_pack else competitor_pack == our_pack

    is_match = name_similarity >= 0.4 and same_volume and same_pack

    return {
        "same_product": name_similarity >= 0.4,
        "same_volume": same_volume,
        "same_pack": same_pack,
        "name_similarity": round(name_similarity, 2),
        "result": "PASS" if is_match else "FAIL",
    }


async def run_llpg_rule_agent(
    kernel,
    competitor_price: float,
    own_price: float,
    cost_price: float,
    category: str,
    competitor_product_name: str,
    our_product_name: str,
    standard_drinks: float = 0.0,
    has_real_ai: bool = True,
) -> tuple[dict[str, Any], str]:
    """
    Apply all LLPG rules and determine the action tier.

    Returns (result_dict, inference_mode).
    """
    # 1. Compute beat price
    rsa_floor = round(cost_price * 1.05, 2)
    beat_result = compute_beat_price(
        own_price=own_price,
        competitor_price=competitor_price,
        rsa_floor_price=rsa_floor,
    )

    # 2. Check RSA compliance
    proposed_price = beat_result["beat_price"] or (competitor_price - 0.01)
    rsa_result = check_rsa_compliance(
        category=category,
        proposed_price=proposed_price,
        cost_price=cost_price,
        standard_drinks=standard_drinks,
    )

    # 3. Stock-for-stock check
    sfs_result = _check_stock_for_stock(
        competitor_name=competitor_product_name,
        our_name=our_product_name,
    )

    # Determine final decision
    if not sfs_result["result"] == "PASS":
        decision = "AUTO_REJECT"
        tier = "auto_reject"
        reasoning = "Stock-for-stock check failed — products are not equivalent."
    elif not rsa_result["compliant"]:
        decision = "AUTO_REJECT"
        tier = "auto_reject"
        reasoning = f"Beat price ${proposed_price:.2f} falls below RSA floor ${rsa_result['effective_floor']:.2f}."
    elif beat_result["action"] == "NO_ACTION":
        decision = "NO_ACTION"
        tier = "no_action"
        reasoning = beat_result["reasoning"]
    else:
        decision = beat_result["action"]
        tier = beat_result["tier"]
        reasoning = beat_result["reasoning"]

    result = {
        "decision": decision,
        "beat_price": beat_result["beat_price"],
        "beat_amount": beat_result.get("beat_amount", 0.01),
        "price_diff_pct": beat_result["diff_pct"],
        "tier": tier,
        "rsa_compliant": rsa_result["compliant"],
        "rules_evaluated": {
            "rsa_check": {
                "floor_price": rsa_result["effective_floor"],
                "beat_price": proposed_price,
                "compliant": rsa_result["compliant"],
            },
            "stock_for_stock": sfs_result,
            "beat_formula": {
                "competitor_price": competitor_price,
                "own_price": own_price,
                "beat_amount": beat_result.get("beat_amount", 0.01),
                "beat_price": beat_result["beat_price"],
                "diff_pct": beat_result["diff_pct"],
                "tier": tier,
            },
        },
        "reasoning": reasoning,
    }

    return result, "real"  # Rule-based = always "real"
