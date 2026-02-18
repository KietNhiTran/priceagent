"""
SK Plugin: Compute beat price.

Implements the LLPG beat formula:
  beat_price = competitor_price - beat_amount (default $0.01)

With tier routing:
  auto_approve: beat $0.01–$5.00, diff < 15%
  human_review: beat $5.01–$20.00, diff 15%–30%
  auto_reject: beat > $20.00 or diff > 30% or below RSA floor
"""

from __future__ import annotations

from typing import Any

from backend.data.loader import get_beat_tier


def compute_beat_price(
    own_price: float,
    competitor_price: float,
    rsa_floor_price: float,
    beat_amount: float = 0.01,
) -> dict[str, Any]:
    """
    Compute the LLPG beat price and determine the routing tier.

    Returns dict with: beat_price, beat_amount, price_diff, diff_pct,
    tier, action, rsa_compliant, reasoning.
    """
    # If competitor is already more expensive, no action needed
    if competitor_price >= own_price:
        return {
            "beat_price": None,
            "beat_amount": 0,
            "price_diff": round(own_price - competitor_price, 2),
            "diff_pct": 0.0,
            "tier": "no_action",
            "action": "NO_ACTION",
            "rsa_compliant": True,
            "reasoning": f"Competitor price ${competitor_price:.2f} is already >= our price ${own_price:.2f}. No beat needed.",
        }

    # Calculate beat price
    proposed_beat = round(competitor_price - beat_amount, 2)
    price_diff = round(own_price - proposed_beat, 2)
    diff_pct = round((price_diff / own_price) * 100, 1) if own_price > 0 else 0.0

    # RSA floor check
    rsa_compliant = proposed_beat >= rsa_floor_price

    # Get tier from config
    tier_config = get_beat_tier(price_diff, diff_pct)
    action = tier_config["action"]

    # Override to auto-reject if below RSA floor
    if not rsa_compliant:
        action = "AUTO_REJECT"
        tier_name = "auto_reject"
        reasoning = (
            f"Beat price ${proposed_beat:.2f} is below RSA floor ${rsa_floor_price:.2f}. "
            f"Auto-rejected for RSA compliance."
        )
    else:
        tier_name = tier_config["tier"]
        reasoning = tier_config.get("description", "")

    return {
        "beat_price": proposed_beat if rsa_compliant and action != "AUTO_REJECT" else None,
        "beat_amount": beat_amount,
        "price_diff": price_diff,
        "diff_pct": diff_pct,
        "tier": tier_name,
        "action": action,
        "rsa_compliant": rsa_compliant,
        "reasoning": reasoning,
    }
